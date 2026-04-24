"""Probe: compare vegis deal URLs from deals.json vs PS feed URLs."""
import os, hmac, hashlib, json, time, re
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv
load_dotenv()

API_USER = os.getenv("PROFITSHARE_API_USER", "")
API_KEY = os.getenv("PROFITSHARE_API_KEY", "")
BASE = Path(__file__).resolve().parent.parent

def call(method, endpoint, query=""):
    date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    sig = f"{method}{endpoint}/?{query}/{API_USER}{date_str}"
    auth = hmac.new(API_KEY.encode(), sig.encode(), hashlib.sha1).hexdigest()
    headers = {"Date": date_str, "X-PS-Client": API_USER, "X-PS-Accept": "json", "X-PS-Auth": auth}
    url = f"https://api.profitshare.ro/{endpoint}/" + (f"?{query}" if query else "")
    return requests.get(url, headers=headers, timeout=30)

with open(BASE/"data"/"deals.json", encoding="utf-8") as f:
    deals = json.load(f)
broken = [d for d in deals if (d.get("magazin") or d.get("store")) == "vegis"
          and "lazy-loader" in (d.get("image","") + d.get("imagine_url",""))]
print(f"broken vegis: {len(broken)}")
print("\n=== sample broken deals: id, titlu, product_url, link_afiliat ===")
for d in broken[:5]:
    print(f"\n  id={d.get('id')}")
    print(f"  titlu={d.get('titlu','')[:70]}")
    print(f"  product_url={d.get('product_url','')}")
    print(f"  link_afiliat={(d.get('link_afiliat') or '')[:90]}")
    print(f"  url (alt)={d.get('url','')[:90]}")

# Fetch one feed page
print("\n=== feed product 0 URLs ===")
r = call("GET","affiliate-products","filters[advertiser]=58221&page=1")
products = r.json().get("result",{}).get("products",[])
for p in products[:3]:
    print(f"\n  name={p.get('name','')[:60]}")
    print(f"  link={p.get('link','')}")
    print(f"  affiliate_link={(p.get('affiliate_link') or '')[:90]}")

# Build set of normalized feed URLs
def norm(u):
    if not u: return ""
    u = u.rstrip('/').lower()
    u = re.sub(r'\?.*$','',u)
    return u

feed_urls = set()
for page in range(1, 31):
    r = call("GET","affiliate-products",f"filters[advertiser]=58221&page={page}")
    if not r.ok: break
    prods = r.json().get("result",{}).get("products",[])
    if not prods: break
    for p in prods:
        feed_urls.add(norm(p.get("link","")))
    time.sleep(0.25)

print(f"\nunique feed URLs: {len(feed_urls)}")
broken_norm = {norm(d.get("product_url","")) for d in broken}
match = broken_norm & feed_urls
print(f"broken URLs also in feed (normalized): {len(match)}/{len(broken_norm)}")

# sample unmatched
unmatched = list(broken_norm - feed_urls)[:5]
print(f"\nsample unmatched broken URLs:")
for u in unmatched: print(f"  {u}")
print(f"\nsample feed URLs:")
for u in list(feed_urls)[:5]: print(f"  {u}")
