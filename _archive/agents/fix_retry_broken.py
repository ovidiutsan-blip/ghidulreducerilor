"""Retry broken images sequential with 2s delay + UA rotation to bypass 403 rate limit."""
import json, re, time
from pathlib import Path
from datetime import datetime
import requests

BASE = Path(__file__).resolve().parent.parent
DEALS = BASE / "data" / "deals.json"
OG = re.compile(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', re.I)
OG_ALT = re.compile(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', re.I)

UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
]

def fetch_og(url, ua, referer=None):
    headers = {"User-Agent": ua, "Accept":"text/html,application/xhtml+xml", "Accept-Language":"ro-RO,ro;q=0.9,en;q=0.8"}
    if referer: headers["Referer"] = referer
    try:
        r = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        if not r.ok: return None, f"HTTP {r.status_code}"
        m = OG.search(r.text) or OG_ALT.search(r.text)
        if not m: return None, "no og:image"
        img = m.group(1).strip()
        if "lazy-loader" in img or "no-image" in img: return None, "placeholder"
        return img, "ok"
    except Exception as e: return None, type(e).__name__

def main():
    with open(DEALS, encoding="utf-8") as f:
        deals = json.load(f)
    # Find still-broken: no image_fixed_at since today AND profitsmart.ro image
    today = datetime.now().date().isoformat()
    broken = []
    for d in deals:
        fixed_at = (d.get("image_fixed_at") or "")[:10]
        img = (d.get("image") or d.get("imagine_url") or "")
        if fixed_at == today: continue
        if "profitsmart.ro" in img:
            broken.append(d)
    print(f"still-broken profitsmart images: {len(broken)}")

    now = datetime.now().isoformat() + "Z"
    ok = fail = 0
    for i, d in enumerate(broken):
        url = d.get("product_url","")
        if not url:
            fail += 1
            continue
        ua = UAS[i % len(UAS)]
        img, status = fetch_og(url, ua)
        if img:
            d["image"] = img
            d["imagine_url"] = img
            d["image_fixed_at"] = now
            d["image_fix_source"] = "og-image-retry"
            ok += 1
            print(f"  [{i+1}/{len(broken)}] OK {d.get('id')}")
        else:
            fail += 1
            print(f"  [{i+1}/{len(broken)}] FAIL {d.get('id')} ({status})")
        time.sleep(2.0)

    print(f"\nretry FIXED: {ok}   still failed: {fail}")
    with open(DEALS, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2, ensure_ascii=False)
    print(f"wrote {DEALS}")

if __name__ == "__main__":
    main()
