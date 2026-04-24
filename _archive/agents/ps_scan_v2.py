"""
Sprint #38 scan - al doilea val advertiseri PS neprobati in Sprint #37.
Focus: auto, cadouri, IT&C top, retail specialty.
"""
import os, sys, json, hmac, hashlib, time
from datetime import datetime
from pathlib import Path
from collections import Counter
import requests
from dotenv import load_dotenv

load_dotenv()

BASE = Path(__file__).resolve().parent.parent
OUT_PATH = BASE / "_ps_scan_candidates_v2.json"
API_URL = "https://api.profitshare.ro"
API_USER = os.getenv("PROFITSHARE_API_USER", "")
API_KEY = os.getenv("PROFITSHARE_API_KEY", "")

CANDIDATES = [
    # AUTO & MOTO - 4 merchants
    ("anvelope-oferte",   124336, "auto-moto"),
    ("pint",              128052, "auto-moto"),
    ("navigatiiandroid",  150390, "auto-moto"),
    ("anvelino",          165505, "auto-moto"),
    # CADOURI & FLORI - 2 merchants
    ("mindblower",         74774, "cadouri"),
    ("giftspot",          167474, "cadouri"),
    # RETAIL SPECIALTY - coffee/lifestyle
    ("beanzcafe",         107680, "retail-specialty"),
    ("coffeepoint",       163078, "retail-specialty"),
    ("sole",              150852, "retail-specialty"),
    ("hotpick",           142963, "retail-specialty"),
    # IT&C top - probe 3 biggest general retailers
    ("dwyn",               87557, "it-c"),
    ("techstar",           88017, "it-c"),
    ("geekmall",          132216, "it-c"),
    ("itgalaxy",           83901, "it-c"),
    ("pcmadd",             59438, "it-c"),
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
                if len(samples) < 2:
                    samples.append({"title":(p.get("name") or "")[:60], "pct":pct, "cat":cat})
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
        time.sleep(0.5)
    results_sorted=sorted(results, key=lambda r: (-r["real_discounts"], -r["hit_rate_pct"]))
    print("\n" + "="*95)
    print(f"{'slug':20s} {'hub':20s} {'sampled':>8s} {'real':>5s} {'hit%':>6s} {'avg%':>6s}  status")
    print("="*95)
    for r in results_sorted:
        print(f"{r['slug']:20s} {r['hub']:20s} {r['total_sampled']:>8d} {r['real_discounts']:>5d} {r['hit_rate_pct']:>5.1f}% {r['avg_discount_pct']:>5.1f}%  {r['status']}")
    OUT_PATH.write_text(json.dumps(results_sorted, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT_PATH}")

if __name__ == "__main__":
    main()
