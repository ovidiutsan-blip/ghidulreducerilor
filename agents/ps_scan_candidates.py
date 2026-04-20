"""
Profitshare advertiser scanner: probes candidate merchants for real discount rates.

For each advertiser in CANDIDATES, fetches ~3 feed pages and reports:
- total products sampled
- real discount count (price_discounted < price_vat)
- hit rate %
- avg discount % on real-discount subset
- top categories in feed

Pattern based on working ps_feed_to_deals.py::call().
"""
import os
import sys
import json
import hmac
import hashlib
import time
from datetime import datetime
from pathlib import Path
from collections import Counter
import requests
from dotenv import load_dotenv

load_dotenv()

BASE = Path(__file__).resolve().parent.parent
OUT_PATH = BASE / "_ps_scan_candidates.json"
API_URL = "https://api.profitshare.ro"
API_USER = os.getenv("PROFITSHARE_API_USER", "")
API_KEY = os.getenv("PROFITSHARE_API_KEY", "")

# Exclude already-integrated: vegis(58221), mathaus(124829), watch24(118702), fornello(148979),
# emag, libris(61047), fashiondays(88736), forit
CANDIDATES = [
    # BEAUTY — close notino gap on /categorii/beauty
    ("colorcosmetics",    62877,  "beauty"),
    ("dalisticq",         118697, "beauty"),
    ("hiris",             71041,  "beauty"),
    ("magazinuldegene",   130078, "beauty"),

    # FASHION — fashiondays feed returned 0, need alternatives
    ("iconicul",          68331,  "fashion"),
    ("mycloset",          69959,  "fashion"),
    ("priveboutique",     63454,  "fashion"),
    ("rubyfashion",       56983,  "fashion"),
    ("vesa",              115529, "fashion"),

    # FARMACIE — boost farmacie-sanatate
    ("minuneanaturii",    163307, "farmacie-sanatate"),
    ("nosugarshop",       77002,  "farmacie-sanatate"),
    ("parmashop",         141953, "farmacie-sanatate"),
    ("scufita-rosie",     112145, "farmacie-sanatate"),
    ("unicorn-naturals",  159248, "farmacie-sanatate"),

    # CASA — more variety
    ("case-smart",        111470, "casa-gradina"),
    ("decolandia",        134190, "casa-gradina"),
    ("depozitsolar",      163312, "casa-gradina"),
    ("emobili",           100816, "casa-gradina"),
    ("evrik",             166235, "casa-gradina"),
    ("exclusive-home",    160977, "casa-gradina"),
    ("kaercher",          149514, "casa-gradina"),
    ("novodoors",         166234, "casa-gradina"),
    ("startdecor",        166563, "casa-gradina"),

    # Others
    ("perfectbijoux",     62570,  "ceasuri"),
    ("watchzone",         96347,  "ceasuri"),
    ("educlass",          58867,  "copii"),
    ("sportpartner",      81396,  "sport"),
]


def call(method, endpoint, query=""):
    """Same pattern as ps_feed_to_deals.py::call()."""
    date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    sig = f"{method}{endpoint}/?{query}/{API_USER}{date_str}"
    auth = hmac.new(API_KEY.encode(), sig.encode(), hashlib.sha1).hexdigest()
    headers = {
        "Date": date_str,
        "X-PS-Client": API_USER,
        "X-PS-Accept": "json",
        "X-PS-Auth": auth,
    }
    url = f"{API_URL}/{endpoint}/" + (f"?{query}" if query else "")
    return requests.get(url, headers=headers, timeout=30)


def scan(slug: str, adv_id: int, hub: str, max_pages: int = 3) -> dict:
    print(f"[scan] {slug:20s} id={adv_id:<7} hub={hub}", flush=True)

    total = 0
    real_disc = 0
    disc_pcts = []
    categories = Counter()
    samples = []
    status = "ok"

    for page in range(1, max_pages + 1):
        try:
            resp = call("GET", "affiliate-products", f"filters[advertiser]={adv_id}&page={page}")
        except Exception as e:
            status = f"exception:{e}"
            break

        if not resp.ok:
            if resp.status_code == 429:
                time.sleep(2)
                continue
            status = f"http_{resp.status_code}"
            break

        try:
            data = resp.json()
        except Exception:
            status = "json_parse_error"
            break

        products = (data.get("result") or {}).get("products") or []
        pagination = (data.get("result") or {}).get("pagination") or {}
        if not products:
            break

        for p in products:
            total += 1
            try:
                price_vat = float(p.get("price_vat") or 0)
                price_disc_raw = p.get("price_discounted")
                price_disc = float(price_disc_raw) if price_disc_raw not in (None, "", 0, "0") else 0
            except (ValueError, TypeError):
                continue

            cat = (p.get("category_name") or "").strip() or "(none)"
            categories[cat] += 1

            if price_vat > 0 and price_disc > 0 and price_disc < price_vat:
                pct = round((1 - price_disc / price_vat) * 100, 1)
                real_disc += 1
                disc_pcts.append(pct)
                if len(samples) < 2:
                    samples.append({
                        "title": (p.get("name") or "")[:60],
                        "pct": pct,
                        "cat": cat,
                    })

        total_pages = int(pagination.get("pages") or pagination.get("total_pages") or 1)
        if page >= total_pages:
            break
        time.sleep(0.35)

    hit = round(100 * real_disc / total, 1) if total else 0
    avg = round(sum(disc_pcts) / len(disc_pcts), 1) if disc_pcts else 0

    return {
        "slug": slug,
        "adv_id": adv_id,
        "hub": hub,
        "status": status,
        "total_sampled": total,
        "real_discounts": real_disc,
        "hit_rate_pct": hit,
        "avg_discount_pct": avg,
        "top_categories": dict(categories.most_common(5)),
        "samples": samples,
    }


def main():
    if not API_USER or not API_KEY:
        print("ERROR: PROFITSHARE_API_USER / PROFITSHARE_API_KEY missing")
        sys.exit(1)

    results = []
    for slug, adv_id, hub in CANDIDATES:
        r = scan(slug, adv_id, hub, max_pages=3)
        results.append(r)
        time.sleep(0.4)

    # Sort by real_discounts desc, then hit_rate desc
    results_sorted = sorted(results, key=lambda r: (-r["real_discounts"], -r["hit_rate_pct"]))

    print("\n" + "=" * 95)
    print(f"{'slug':20s} {'hub':20s} {'sampled':>8s} {'real':>5s} {'hit%':>6s} {'avg%':>6s}  status")
    print("=" * 95)
    for r in results_sorted:
        print(f"{r['slug']:20s} {r['hub']:20s} {r['total_sampled']:>8d} {r['real_discounts']:>5d} {r['hit_rate_pct']:>5.1f}% {r['avg_discount_pct']:>5.1f}%  {r['status']}")

    OUT_PATH.write_text(json.dumps(results_sorted, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()
