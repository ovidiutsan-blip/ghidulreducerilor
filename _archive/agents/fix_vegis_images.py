"""Fix vegis deal images: pull fresh image URLs from Profitshare feed and patch data/deals.json.

Problem: 102 vegis deals have image=cdn.vegis.ro/.../lazy-loader.gif (placeholder from old scrape).
Solution: re-fetch vegis via PS API, match by product_url (`link`), update `imagine_url` + `image` fields.
"""
import os, hmac, hashlib, json, time
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv
load_dotenv()

API_URL = "https://api.profitshare.ro"
API_USER = os.getenv("PROFITSHARE_API_USER", "")
API_KEY = os.getenv("PROFITSHARE_API_KEY", "")
BASE = Path(__file__).resolve().parent.parent
DEALS_PATH = BASE / "data" / "deals.json"

def call(method, endpoint, query=""):
    date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    sig = f"{method}{endpoint}/?{query}/{API_USER}{date_str}"
    auth = hmac.new(API_KEY.encode(), sig.encode(), hashlib.sha1).hexdigest()
    headers = {"Date": date_str, "X-PS-Client": API_USER, "X-PS-Accept": "json", "X-PS-Auth": auth}
    url = f"{API_URL}/{endpoint}/" + (f"?{query}" if query else "")
    return requests.get(url, headers=headers, timeout=30)

def https(u: str) -> str:
    if isinstance(u, str) and u.startswith("http://"):
        return "https://" + u[7:]
    return u

import re
def slugify(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]

def make_deal_id(magazin: str, name: str, part_number: str) -> str:
    # matches agents/ps_feed_to_deals.py:product_to_deal
    return f"ps-{magazin}-{slugify(name)[:40]}-{(part_number or '')[-8:]}"

def fetch_all(magazin: str, adv_id: int, max_pages: int = 30):
    """Return {reconstructed_id: {image, name}} and {product_url: {image, name}} from PS feed."""
    by_id = {}
    by_url = {}
    by_pn = {}
    for page in range(1, max_pages + 1):
        r = None
        for attempt in range(4):
            r = call("GET", "affiliate-products", f"filters[advertiser]={adv_id}&page={page}")
            if r.ok: break
            if r.status_code == 429:
                time.sleep(2 ** attempt); continue
            break
        if not r or not r.ok:
            print(f"  page {page}: fail {r.status_code if r else 'nores'}"); break
        products = r.json().get("result", {}).get("products", [])
        if not products:
            break
        for p in products:
            img = https(p.get("image_original") or p.get("image") or "")
            if not img or "lazy-loader" in img: continue
            name = p.get("name", "")
            pn = p.get("part_number", "") or ""
            url = p.get("link") or ""
            rid = make_deal_id(magazin, name, pn)
            rec = {"image": img, "name": name}
            by_id[rid] = rec
            if url: by_url[url] = rec
            if pn: by_pn[pn[-8:]] = rec
        time.sleep(0.3)
    return by_id, by_url, by_pn

def main():
    if not API_USER or not API_KEY:
        print("ERR: PS credentials missing"); return
    with open(DEALS_PATH, encoding="utf-8") as f:
        deals = json.load(f)
    print(f"loaded {len(deals)} deals")

    # Fetch vegis feed (3 indexes: by_id, by_url, by_pn-suffix)
    print("\n[vegis] fetching feed...")
    by_id, by_url, by_pn = fetch_all("vegis", 58221, max_pages=30)
    print(f"  feed: {len(by_id)} by_id | {len(by_url)} by_url | {len(by_pn)} by_pn")

    # Audit: which vegis deals have broken image?
    broken = [d for d in deals if (d.get("magazin") or d.get("store")) == "vegis"
              and "lazy-loader" in (d.get("image","") + d.get("imagine_url",""))]
    print(f"\nbroken vegis deals: {len(broken)}")

    patched = 0
    not_found = []
    match_stats = {"id":0, "url":0, "pn":0}
    for d in broken:
        # Try match cascade: id → url → part_number suffix extracted from existing id
        rec = by_id.get(d.get("id",""))
        if rec: match_stats["id"] += 1
        if not rec:
            rec = by_url.get(d.get("product_url") or "")
            if rec: match_stats["url"] += 1
        if not rec:
            # existing id has pn suffix as last 8 chars (after last '-')
            last = (d.get("id","").rsplit("-",1) or [""])[-1]
            if last and len(last) >= 4:
                rec = by_pn.get(last)
                if rec: match_stats["pn"] += 1
        if not rec:
            not_found.append(d.get("id",""))
            continue
        new_img = rec["image"]
        d["image"] = new_img
        d["imagine_url"] = new_img
        d["image_fixed_at"] = datetime.utcnow().isoformat() + "Z"
        patched += 1

    print(f"\nPATCHED: {patched}   NOT FOUND: {len(not_found)}   match via: {match_stats}")
    if not_found[:5]:
        print("  sample not found:", not_found[:5])
    if patched == 0:
        print("no changes, exiting"); return

    with open(DEALS_PATH, "w", encoding="utf-8") as f:
        json.dump(deals, f, indent=2, ensure_ascii=False)
    print(f"wrote {DEALS_PATH}")

    # Sample
    print("\nsample patched:")
    for d in [x for x in deals if x.get("image_fixed_at")][:3]:
        print(f"  {d['id']} | {d['image']}")

if __name__ == "__main__":
    main()
