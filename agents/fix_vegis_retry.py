"""Retry remaining broken vegis (HTTP 403 from rate-limit) — sequential, 2s delay."""
import json, re, time
from pathlib import Path
from datetime import datetime
import requests

BASE = Path(__file__).resolve().parent.parent
DEALS = BASE / "data" / "deals.json"
OG = re.compile(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', re.I)
OG_ALT = re.compile(r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', re.I)

UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
]

def fetch_og(url, ua):
    try:
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
        }
        r = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
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
    print(f"remaining broken: {len(broken)}")

    now = datetime.now().isoformat() + "Z"
    ok, fail = 0, 0
    for i, d in enumerate(broken):
        ua = UAS[i % len(UAS)]
        img, status = fetch_og(d.get("product_url",""), ua)
        if img:
            d["image"] = img
            d["imagine_url"] = img
            d["image_fixed_at"] = now
            d["image_fix_source"] = "og-image-retry"
            ok += 1
            print(f"  [{i+1}/{len(broken)}] OK {d['id']}")
        else:
            fail += 1
            print(f"  [{i+1}/{len(broken)}] FAIL {d['id']} ({status})")
        time.sleep(1.8)

    print(f"\nretry FIXED: {ok}   still failed: {fail}")

    with open(DEALS, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2, ensure_ascii=False)
    print(f"wrote {DEALS}")

if __name__ == "__main__":
    main()
