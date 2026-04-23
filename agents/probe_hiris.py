"""Probe hiris product page to find where image URL lives."""
import json
from pathlib import Path
import requests

BASE = Path(__file__).resolve().parent.parent
with open(BASE/"data"/"deals.json", encoding="utf-8") as f:
    deals = json.load(f)
hiris = [d for d in deals if d.get("magazin")=="hiris" and "profitsmart.ro" in (d.get("image") or "")]
print(f"hiris broken: {len(hiris)}")
if not hiris: raise SystemExit

url = hiris[0].get("product_url","")
print(f"probe: {url}")
r = requests.get(url, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 Chrome/128"}, timeout=15, allow_redirects=True)
print(f"HTTP {r.status_code} | {len(r.text)} bytes")
html = r.text

import re
# All image patterns
patterns = {
    "og:image": r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
    "og:image (rev)": r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
    "twitter:image": r'<meta[^>]*(?:name|property)=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']',
    "link image_src": r'<link[^>]*rel=["\']image_src["\'][^>]*href=["\']([^"\']+)["\']',
    "data-src": r'data-src=["\']([^"\']+\.(?:jpg|jpeg|png|webp))[^"\']*["\']',
    "data-zoom": r'data-zoom[^=]*=["\']([^"\']+\.(?:jpg|jpeg|png|webp))[^"\']*["\']',
    "ld+json image": r'"image"\s*:\s*["\[]([^"\]]+)',
    "src jpg/png": r'<img[^>]*src=["\']([^"\']+\.(?:jpg|jpeg|png|webp))[^"\']*["\']',
    "hiris-specific product": r'(https://hiris\.ro/[^"\']+\.(?:jpg|jpeg|png|webp))',
}
for name, p in patterns.items():
    matches = re.findall(p, html, re.I)[:3]
    print(f"\n  {name}: {len(matches)}")
    for m in matches: print(f"    {m[:120]}")
