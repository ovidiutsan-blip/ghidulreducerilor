"""Fix all broken images (profitsmart.ro 404) by re-fetching from PS feed + og:image fallback.

Strategy per broken deal:
1. Re-fetch merchant PS feed, match by product_url -> use fresh image
2. If not in feed (product removed), scrape <meta property=og:image> from product page

Runs against logs/bad_images.json (produced by agents/audit_live_images.py).
"""
import os, hmac, hashlib, json, re, time
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from dotenv import load_dotenv
load_dotenv()

API_USER = os.getenv("PROFITSHARE_API_USER", "")
API_KEY = os.getenv("PROFITSHARE_API_KEY", "")
BASE = Path(__file__).resolve().parent.parent
DEALS = BASE / "data" / "deals.json"
BAD = BASE / "logs" / "bad_images.json"

# Advertiser IDs (same mapping as ps_feed_to_deals.py)
ADV_IDS = {
    "vegis": 58221, "mathaus": 124829, "hiris": 71041,
    "case-smart": 111470, "novodoors": 166234, "techstar": 88017,
    "hotpick": 142963, "alecoair": 96348, "streamstore": 166230,
}
OG = re.compile(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', re.I)
OG_ALT = re.compile(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', re.I)

def ps_call(method, endpoint, query=""):
    date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    sig = f"{method}{endpoint}/?{query}/{API_USER}{date_str}"
    auth = hmac.new(API_KEY.encode(), sig.encode(), hashlib.sha1).hexdigest()
    headers = {"Date": date_str, "X-PS-Client": API_USER, "X-PS-Accept": "json", "X-PS-Auth": auth}
    url = f"https://api.profitshare.ro/{endpoint}/" + (f"?{query}" if query else "")
    return requests.get(url, headers=headers, timeout=30)

def fetch_ps_feed(adv_id, max_pages=30):
    out = {}
    for page in range(1, max_pages + 1):
        r = None
        for attempt in range(3):
            try:
                r = ps_call("GET","affiliate-products",f"filters[advertiser]={adv_id}&page={page}")
                if r.ok: break
                if r.status_code == 429:
                    time.sleep(2**attempt); continue
                break
            except Exception: time.sleep(1)
        if not r or not r.ok: break
        prods = r.json().get("result",{}).get("products",[])
        if not prods: break
        for p in prods:
            url = p.get("link","")
            if not url: continue
            img = p.get("image_original") or p.get("image") or ""
            if img.startswith("http://"): img = "https://" + img[7:]
            if "lazy-loader" in img or not img: continue
            out[url] = img
        time.sleep(0.2)
    return out

def scrape_og(url, timeout=12):
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=timeout, allow_redirects=True)
        if not r.ok: return None, f"HTTP {r.status_code}"
        m = OG.search(r.text) or OG_ALT.search(r.text)
        if not m: return None, "no og:image"
        img = m.group(1).strip()
        if "lazy-loader" in img or "no-image" in img or not img:
            return None, "placeholder"
        return img, "ok"
    except Exception as e:
        return None, type(e).__name__

def main():
    if not BAD.exists():
        print(f"ERR: {BAD} not found. Run agents/audit_live_images.py first."); return
    if not API_USER or not API_KEY:
        print("WARN: PS credentials missing; og:image-only mode")
    bad_list = json.loads(BAD.read_text(encoding="utf-8"))
    print(f"loaded {len(bad_list)} broken images")

    with open(DEALS, encoding="utf-8") as f:
        deals = json.load(f)
    deals_by_id = {d.get("id"): d for d in deals}

    # Group bad by magazin
    by_mag = {}
    for b in bad_list:
        by_mag.setdefault(b["magazin"], []).append(b)
    print("by magazin:", {k: len(v) for k, v in by_mag.items()})

    # Fetch feeds once per magazin
    feeds = {}
    for mag in by_mag:
        adv = ADV_IDS.get(mag)
        if not adv or not API_USER:
            feeds[mag] = {}; continue
        print(f"\n[{mag}] fetching feed (adv={adv})...")
        feeds[mag] = fetch_ps_feed(adv, max_pages=30)
        print(f"  feed: {len(feeds[mag])} products")

    now = datetime.now().isoformat() + "Z"
    stats = {"feed_match":0, "ogscrape":0, "fail":0}
    failed_samples = []

    # Phase 1: feed match (fast)
    scrape_queue = []
    for bad in bad_list:
        d = deals_by_id.get(bad["id"])
        if not d: continue
        feed = feeds.get(bad["magazin"], {})
        url = d.get("product_url") or d.get("link") or ""
        new_img = feed.get(url)
        if new_img:
            d["image"] = new_img
            d["imagine_url"] = new_img
            d["image_fixed_at"] = now
            d["image_fix_source"] = "ps-feed-refresh"
            stats["feed_match"] += 1
        else:
            scrape_queue.append(bad)

    print(f"\nafter feed phase: {stats['feed_match']} fixed, {len(scrape_queue)} need og:image scrape")

    # Phase 2: og:image scrape (concurrent)
    def scrape_one(bad):
        d = deals_by_id.get(bad["id"])
        if not d: return (bad["id"], None, "no-deal")
        url = d.get("product_url","")
        img, status = scrape_og(url)
        return (bad["id"], img, status)

    if scrape_queue:
        print(f"\nscraping og:image for {len(scrape_queue)} deals...")
        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = {ex.submit(scrape_one, b): b for b in scrape_queue}
            done = 0
            for fut in as_completed(futures):
                did, img, status = fut.result()
                d = deals_by_id.get(did)
                if d and img:
                    d["image"] = img
                    d["imagine_url"] = img
                    d["image_fixed_at"] = now
                    d["image_fix_source"] = "og-image-scrape"
                    stats["ogscrape"] += 1
                else:
                    stats["fail"] += 1
                    if len(failed_samples) < 5:
                        failed_samples.append(f"{did} | {status}")
                done += 1
                if done % 20 == 0:
                    print(f"  progress: {done}/{len(futures)}")

    print(f"\n=== RESULT ===")
    print(f"  feed match:  {stats['feed_match']}")
    print(f"  og:image:    {stats['ogscrape']}")
    print(f"  FAILED:      {stats['fail']}")
    for s in failed_samples: print(f"    {s}")

    with open(DEALS, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2, ensure_ascii=False)
    print(f"\nwrote {DEALS}")

if __name__ == "__main__":
    main()
