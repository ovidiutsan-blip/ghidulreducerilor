"""
Sprint #39 scan - al treilea val: 12 advertiseri PS neprobati in S37/S38.
Focus: IT&C general retailers (majoritatea), cărți, casa (Fornello cross-check), ambient.
Serviciile/financiare/alcool/turism au fost filtrate ca fiind non-relevante.
"""
import os, sys, json, hmac, hashlib, time
from datetime import datetime
from pathlib import Path
from collections import Counter
import requests
from dotenv import load_dotenv

load_dotenv()

BASE = Path(__file__).resolve().parent.parent
OUT_PATH = BASE / "_ps_scan_candidates_v3.json"
API_URL = "https://api.profitshare.ro"
API_USER = os.getenv("PROFITSHARE_API_USER", "")
API_KEY = os.getenv("PROFITSHARE_API_KEY", "")

CANDIDATES = [
    # BOOKS / MEDIA
    ("libris",         61047,  "carti"),
    # IT&C general retailers
    ("abdcomputer",    62479,  "it-c"),
    ("citgrup",        67678,  "it-c"),
    ("vonmag",         88324,  "it-c"),
    ("seku",           98562,  "it-c"),
    ("vexio",         103131,  "it-c"),
    ("dualstore",     127683,  "it-c"),
    ("contakt",       130510,  "it-c"),
    ("forit",         138584,  "it-c"),
    ("streamstore",   166230,  "it-c"),
    # CASA/AMBIENT
    ("alecoair",       96348,  "casa-gradina"),
    ("fornello-ps",   148979,  "casa-gradina"),  # cross-check daca PS feed e viabil vs scraper
]

def call(method, endpoint, query=""):
    date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    sig = f"{method}{endpoint}/?{query}/{API_USER}{date_str}"
    auth = hmac.new(API_KEY.encode(), sig.encode(), hashlib.sha1).hexdigest()
    headers = {"Date": date_str, "X-PS-Client": API_USER, "X-PS-Accept": "json", "X-PS-Auth": auth}
    url = f"{API_URL}/{endpoint}/" + (f"?{query}" if query else "")
    return requests.get(url, headers=headers, timeout=30)

def scan(slug, adv_id, hub, max_pages=3):
    print(f"[scan] {slug:20s} id={adv_id:<7} hub={hub}", flush=True)
    total=0; real_disc=0; disc_pcts=[]; categories=Counter(); samples=[]; status="ok"
    for page in range(1, max_pages+1):
        try:
            resp = call("GET", "affiliate-products", f"filters[advertiser]={adv_id}&page={page}")
        except Exception as e:
            status=f"exception:{e}"; break
        if not resp.ok:
            if resp.status_code == 429:
                time.sleep(3); continue
            status=f"http_{resp.status_code}"; break
        try:
            data=resp.json()
        except Exception:
            status="json_parse_error"; break
        products=(data.get("result") or {}).get("products") or []
        pagination=(data.get("result") or {}).get("pagination") or {}
        if not products: break
        for p in products:
            total += 1
            try:
                price_vat=float(p.get("price_vat") or 0)
                pd_raw=p.get("price_discounted")
                price_disc=float(pd_raw) if pd_raw not in (None,"",0,"0") else 0
            except (ValueError, TypeError):
                continue
            cat=(p.get("category_name") or "").strip() or "(none)"
            categories[cat] += 1
            if price_vat > 0 and price_disc > 0 and price_disc < price_vat:
                pct=round((1 - price_disc/price_vat)*100, 1)
                real_disc += 1; disc_pcts.append(pct)
                if len(samples) < 3:
                    samples.append({"title":(p.get("name") or "")[:70], "pct":pct, "cat":cat})
        total_pages=int(pagination.get("pages") or pagination.get("total_pages") or 1)
        if page >= total_pages: break
        time.sleep(0.35)
    hit=round(100*real_disc/total, 1) if total else 0
    avg=round(sum(disc_pcts)/len(disc_pcts), 1) if disc_pcts else 0
    return {"slug":slug, "adv_id":adv_id, "hub":hub, "status":status, "total_sampled":total,
            "real_discounts":real_disc, "hit_rate_pct":hit, "avg_discount_pct":avg,
            "top_categories":dict(categories.most_common(5)), "samples":samples}

def main():
    if not API_USER or not API_KEY:
        print("ERROR: creds missing"); sys.exit(1)
    results=[]
    for slug, adv_id, hub in CANDIDATES:
        r = scan(slug, adv_id, hub, max_pages=3)
        results.append(r)
        time.sleep(0.8)  # gentle inter-merchant to avoid per-advertiser rate limit
    results_sorted=sorted(results, key=lambda r: (-r["real_discounts"], -r["hit_rate_pct"]))
    print("\n" + "="*100)
    print(f"{'slug':20s} {'hub':15s} {'sampled':>8s} {'real':>5s} {'hit%':>6s} {'avg%':>6s}  status")
    print("="*100)
    for r in results_sorted:
        print(f"{r['slug']:20s} {r['hub']:15s} {r['total_sampled']:>8d} {r['real_discounts']:>5d} {r['hit_rate_pct']:>5.1f}% {r['avg_discount_pct']:>5.1f}%  {r['status']}")
    OUT_PATH.write_text(json.dumps(results_sorted, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT_PATH}")

if __name__ == "__main__":
    main()
