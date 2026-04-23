"""Probe og:image host for each broken magazin (hiris, alecoair, hotpick, mathaus)."""
import json
import re
from pathlib import Path
import requests

BASE = Path(__file__).resolve().parent.parent
with open(BASE/"data"/"deals.json", encoding="utf-8") as f:
    deals = json.load(f)

OG = re.compile(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', re.I)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128"

mags = ["hiris","alecoair","hotpick","mathaus"]
for mag in mags:
    broken = [d for d in deals if d.get("magazin")==mag and "profitsmart.ro" in (d.get("image") or "")]
    print(f"\n=== {mag}: {len(broken)} broken ===")
    if not broken: continue
    for d in broken[:2]:
        url = d.get("product_url","")
        print(f"\nprobe: {url}")
        try:
            r = requests.get(url, headers={"User-Agent":UA}, timeout=12, allow_redirects=True)
            print(f"  HTTP {r.status_code} | {len(r.text)} bytes")
            m = OG.search(r.text)
            if m:
                img = m.group(1)
                host = re.match(r'https?://([^/]+)/', img)
                print(f"  og:image HOST = {host.group(1) if host else 'N/A'}")
                print(f"  full URL: {img[:140]}")
            else:
                print("  NO og:image")
                # Probe for other image patterns
                data_src = re.findall(r'data-src=["\']([^"\']+\.(?:jpg|png|webp))', r.text)
                print(f"  data-src hits: {len(data_src)}; sample: {data_src[0][:120] if data_src else 'none'}")
        except Exception as e:
            print(f"  EXCEPTION: {type(e).__name__}: {e}")
