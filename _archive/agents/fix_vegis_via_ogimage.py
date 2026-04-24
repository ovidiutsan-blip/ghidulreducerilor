"""Fix broken vegis images by scraping og:image from each product page.

Strategy: 103 vegis deals point to cdn.vegis.ro/.../lazy-loader.gif. PS feed doesn't
contain these products anymore (URLs differ). Solution: fetch product page, parse
<meta property="og:image" content="..."> (cdn.vegis.ro, already whitelisted).
"""
import json, re, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import requests

BASE = Path(__file__).resolve().parent.parent
DEALS = BASE / "data" / "deals.json"

OG = re.compile(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', re.I)
OG_ALT = re.compile(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', re.I)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) GhidulReducerilorBot/1.0"

def fetch_og(url: str, timeout: int = 15):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout, allow_redirects=True)
        if not r.ok:
            return None, f"HTTP {r.status_code}"
        m = OG.search(r.text) or OG_ALT.search(r.text)
        if not m:
            return None, "no og:image"
        img = m.group(1).strip()
        if "lazy-loader" in img or not img:
            return None, "still lazy-loader"
        return img, "ok"
    except Exception as e:
        return None, type(e).__name__

def main():
    with open(DEALS, encoding="utf-8") as f:
        deals = json.load(f)
    broken = [d for d in deals if (d.get("magazin") or d.get("store")) == "vegis"
              and "lazy-loader" in (d.get("image","") + d.get("imagine_url",""))]
    print(f"broken vegis deals: {len(broken)}")
    if not broken:
        print("nothing to do"); return

    # Concurrent fetch
    results = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(fetch_og, d["product_url"]): d["id"] for d in broken if d.get("product_url")}
        done = 0
        for fut in as_completed(futures):
            did = futures[fut]
            img, status = fut.result()
            results[did] = (img, status)
            done += 1
            if done % 10 == 0:
                print(f"  progress: {done}/{len(futures)}")

    # Apply
    now = datetime.now().isoformat() + "Z"
    ok, fail = 0, 0
    failed_samples = []
    for d in broken:
        did = d.get("id")
        img, status = results.get(did, (None, "missing"))
        if img:
            d["image"] = img
            d["imagine_url"] = img
            d["image_fixed_at"] = now
            d["image_fix_source"] = "og-image-scrape"
            ok += 1
        else:
            fail += 1
            if len(failed_samples) < 5:
                failed_samples.append(f"{did} | {status}")

    print(f"\nFIXED: {ok}   FAILED: {fail}")
    if failed_samples:
        print("  sample failures:")
        for s in failed_samples: print(f"    {s}")

    with open(DEALS, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2, ensure_ascii=False)
    print(f"wrote {DEALS}")

    # Sample success
    fixed = [d for d in deals if d.get("image_fix_source") == "og-image-scrape"]
    print("\nsample fixed:")
    for d in fixed[:3]:
        print(f"  {d['id']} | {d['image']}")

if __name__ == "__main__":
    main()
