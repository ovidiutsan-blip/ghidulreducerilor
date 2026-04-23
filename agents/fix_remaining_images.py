"""Final fix for remaining broken images.

For each deal with profitsmart.ro image:
1. Fetch product page
2. Try og:image (works for hiris, vegis)
3. Fallback: first plausible product image from data-src (works for alecoair, hotpick)
4. If page returns 403 (CloudFlare on mathaus): mark deal as activ=false (hide from site)

This unifies all merchant patterns into one script. Can run weekly to catch image rot.
"""
import json, re, time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

BASE = Path(__file__).resolve().parent.parent
DEALS = BASE / "data" / "deals.json"

OG = re.compile(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', re.I)

# Patterns to find product image in data-src (excludes logos, banners, placeholders)
DATA_SRC_PATTERNS = [
    re.compile(r'data-src=["\']([^"\']+(?:products?|catalog)[^"\']+\.(?:jpg|jpeg|png|webp))[^"\']*["\']', re.I),
    re.compile(r'data-src=["\']([^"\']+/p/(?:l|m|t)/[^"\']+\.(?:jpg|jpeg|png|webp))[^"\']*["\']', re.I),
    re.compile(r'data-src=["\']([^"\']+\.(?:jpg|jpeg|png|webp))[^"\']*["\']', re.I),
]

BAD_HINTS = ["logo", "placeholder", "lazy-loader", "loader.gif", "no-image", "noimage",
             "banner", "footer", "header", "social", "icon", "sprite"]

UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15",
]

def is_bad_img(url: str) -> bool:
    low = url.lower()
    return any(h in low for h in BAD_HINTS)

def extract_image(html: str, product_url: str) -> str | None:
    # 1. og:image
    m = OG.search(html)
    if m:
        img = m.group(1).strip()
        if not is_bad_img(img):
            return img
    # 2. data-src scan — first candidate that's not a bad hint
    for pat in DATA_SRC_PATTERNS:
        for cand in pat.findall(html):
            cand = cand.strip()
            if not is_bad_img(cand) and len(cand) > 30:
                # Make absolute
                if cand.startswith("//"):
                    cand = "https:" + cand
                elif cand.startswith("/"):
                    # relative to product_url host
                    m2 = re.match(r'(https?://[^/]+)/', product_url)
                    if m2: cand = m2.group(1) + cand
                return cand
    return None

def fetch(url: str, ua: str) -> tuple[int | None, str]:
    try:
        r = requests.get(url, headers={"User-Agent": ua, "Accept":"text/html"},
                         timeout=15, allow_redirects=True)
        return r.status_code, r.text
    except Exception as e:
        return None, str(e)

def process(args):
    idx, d = args
    url = d.get("product_url") or ""
    if not url:
        return (d["id"], None, "no_url", None)
    ua = UAS[idx % len(UAS)]
    code, body = fetch(url, ua)
    if code == 403:
        return (d["id"], None, "cloudflare_403", None)
    if code != 200:
        return (d["id"], None, f"http_{code}", None)
    img = extract_image(body, url)
    if not img:
        return (d["id"], None, "no_image_found", None)
    return (d["id"], img, "ok", url)

def main():
    with open(DEALS, encoding="utf-8") as f:
        deals = json.load(f)
    # Find still-broken by HTTP check
    broken = [d for d in deals if "profitsmart.ro" in (d.get("image") or "")]
    print(f"deals with profitsmart.ro image: {len(broken)}")
    if not broken:
        print("nothing to do"); return

    now = datetime.now().isoformat() + "Z"
    results = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(process, (i, d)): d["id"] for i, d in enumerate(broken)}
        done = 0
        for fut in as_completed(futures):
            did, img, status, url = fut.result()
            results[did] = (img, status)
            done += 1
            if done % 15 == 0:
                print(f"  progress: {done}/{len(futures)}")

    # Apply
    deals_by_id = {d.get("id"): d for d in deals}
    stats = {"fixed": 0, "disabled": 0, "still_broken": 0}
    for did, (img, status) in results.items():
        d = deals_by_id.get(did)
        if not d: continue
        if img:
            d["image"] = img
            d["imagine_url"] = img
            d["image_fixed_at"] = now
            d["image_fix_source"] = "generic-extract"
            stats["fixed"] += 1
        elif status == "cloudflare_403":
            # Hide from site but keep data
            d["activ"] = False
            d["image_disabled_reason"] = "cloudflare_403"
            d["image_disabled_at"] = now
            stats["disabled"] += 1
        else:
            stats["still_broken"] += 1
            print(f"  STUCK: {did} | {status}")

    print(f"\n=== RESULT ===")
    print(f"  fixed:         {stats['fixed']}")
    print(f"  disabled:      {stats['disabled']} (CloudFlare-blocked magazins)")
    print(f"  still broken:  {stats['still_broken']}")

    with open(DEALS, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2, ensure_ascii=False)
    print(f"wrote {DEALS}")

if __name__ == "__main__":
    main()
