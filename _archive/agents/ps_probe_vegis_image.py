"""Probe Profitshare feed for vegis to see which fields hold the real image URL."""
import os, hmac, hashlib, json
from datetime import datetime
import requests
from dotenv import load_dotenv
load_dotenv()

API_URL = "https://api.profitshare.ro"
API_USER = os.getenv("PROFITSHARE_API_USER", "")
API_KEY = os.getenv("PROFITSHARE_API_KEY", "")

def call(method, endpoint, query=""):
    date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    sig = f"{method}{endpoint}/?{query}/{API_USER}{date_str}"
    auth = hmac.new(API_KEY.encode(), sig.encode(), hashlib.sha1).hexdigest()
    headers = {"Date": date_str, "X-PS-Client": API_USER, "X-PS-Accept": "json", "X-PS-Auth": auth}
    url = f"{API_URL}/{endpoint}/" + (f"?{query}" if query else "")
    return requests.get(url, headers=headers, timeout=30)

if not API_USER or not API_KEY:
    print("ERR: PS credentials missing"); raise SystemExit(1)

# vegis adv_id = 58221
resp = call("GET", "affiliate-products", "filters[advertiser]=58221&page=1")
print("HTTP:", resp.status_code)
data = resp.json()
products = data.get("result", {}).get("products", [])
print("products:", len(products))
if products:
    p = products[0]
    print("\n=== all fields in product 0 ===")
    for k, v in p.items():
        s = str(v)[:100]
        print(f"  {k}: {s}")
    print("\n=== sample 3 products — image* fields only ===")
    for i, p in enumerate(products[:3]):
        print(f"\nproduct {i}: name={p.get('name','')[:50]}")
        for k, v in p.items():
            if 'image' in k.lower() or 'photo' in k.lower() or 'img' in k.lower() or 'pic' in k.lower():
                print(f"  {k} = {v}")
