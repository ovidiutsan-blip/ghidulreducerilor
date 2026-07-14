#!/usr/bin/env python3
"""
Merchant Scan — GhidulReducerilor.ro
=====================================
Discovery lunar: compara advertiserii disponibili in PS/2P cu ce e deja
configurat in ps_merchants.json / 2p_merchants.json si raporteaza candidati noi.

Pentru fiecare candidat face un probe rapid (pagina 1) si estimeaza
numarul de produse cu reducere reala. Sorteaza dupa potential.

NU modifica automat json-urile de config — necesita review uman.

Utilizare:
  python scripts/merchant_scan.py              # scan complet PS + 2P
  python scripts/merchant_scan.py --ps-only    # doar ProfitShare
  python scripts/merchant_scan.py --2p-only    # doar 2Performant
  python scripts/merchant_scan.py --no-probe   # lista candidati fara probe

Output: logs/merchant_scan_YYYYMMDD.json
"""
from __future__ import annotations
import os, sys, json, hmac, hashlib, time, argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import requests
from dotenv import load_dotenv

load_dotenv()

BASE       = Path(__file__).resolve().parent.parent
LOGS_DIR   = BASE / "logs"
LOGS_DIR.mkdir(exist_ok=True)

PS_MERCHANTS_PATH = BASE / "agents" / "ps_merchants.json"
P2_MERCHANTS_PATH = BASE / "agents" / "2p_merchants.json"

# ─── ProfitShare Auth ──────────────────────────────────────────────────────────
PS_API_URL  = "https://api.profitshare.ro"
# Secretele din GitHub au BOM (﻿) la început — fără strip, putheader()
# crapă cu UnicodeEncodeError (la fel ca în ps_feed_to_deals.py).
PS_API_USER = os.getenv("PROFITSHARE_API_USER", "").lstrip("﻿").strip()
PS_API_KEY  = os.getenv("PROFITSHARE_API_KEY", "").lstrip("﻿").strip()


def ps_call(method: str, endpoint: str, query: str = ""):
    date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    sig  = f"{method}{endpoint}/?{query}/{PS_API_USER}{date_str}"
    auth = hmac.new(PS_API_KEY.encode(), sig.encode(), hashlib.sha1).hexdigest()
    headers = {
        "Date": date_str, "X-PS-Client": PS_API_USER,
        "X-PS-Accept": "json", "X-PS-Auth": auth,
    }
    url = f"{PS_API_URL}/{endpoint}/" + (f"?{query}" if query else "")
    return requests.get(url, headers=headers, timeout=30)


# ─── 2Performant Auth ─────────────────────────────────────────────────────────
# Sesiunea partajată (agents/two_performant_session.py): auto-login cu
# email+parolă (stabile), throttle + backoff 429, re-login automat la 401.
# Token-ul static TWO_PERFORMANT_ACCESS_TOKEN expiră (~14 zile) — nu-l mai folosim.
sys.path.insert(0, str(BASE / "agents"))
from two_performant_session import (  # noqa: E402
    api_get as p2_api_get,
    TwoPerformantRateLimited,
    EMAIL as P2_EMAIL,
    PASSWORD as P2_PASSWORD,
)


def _safe_json(r):
    import json as _j
    return _j.loads(r.content.decode("utf-8-sig"))


# ─── ProfitShare scan ─────────────────────────────────────────────────────────
def scan_ps(probe: bool = True) -> list[dict]:
    """Returneaza lista de advertiseri PS noi (nu sunt in ps_merchants.json)."""
    if not PS_API_USER or not PS_API_KEY:
        log("PS scan skip: credentiale lipsa")
        return []

    # Incarca adv_id-urile deja configurate
    known_ids = set()
    if PS_MERCHANTS_PATH.exists():
        with open(PS_MERCHANTS_PATH, encoding="utf-8") as f:
            known_ids = {m["adv_id"] for m in json.load(f)}

    log(f"PS: {len(known_ids)} merchantii configurati deja")

    # Fetch toti advertiserii disponibili
    advertisers = []
    for page in range(1, 20):
        resp = ps_call("GET", "affiliate-advertisers", f"page={page}")
        if not resp.ok:
            log(f"  PS advertisers page {page}: {resp.status_code} — stop")
            break
        data = resp.json().get("result", {})
        # API-ul PS întoarce result ca DICT indexat pe id ({"35": {...}}),
        # verificat 2026-07-14; păstrăm fallback pe listă/advertisers/items.
        if isinstance(data, list):
            batch = data
        elif all(isinstance(v, dict) for v in data.values()) and data:
            batch = list(data.values())
        else:
            batch = data.get("advertisers") or data.get("items") or []
        if not batch:
            break
        advertisers.extend(batch)
        if len(batch) < 20:
            break
        time.sleep(0.3)

    log(f"PS: {len(advertisers)} advertiseri totali in program")

    candidates = []
    for adv in advertisers:
        adv_id = int(adv.get("id") or adv.get("advertiser_id") or 0)
        if not adv_id or adv_id in known_ids:
            continue
        name = adv.get("name") or adv.get("title") or f"adv_{adv_id}"
        candidate = {
            "sursa": "profitshare",
            "slug": name.lower().replace(" ", "-")[:30],
            "adv_id": adv_id,
            "name": name,
            "url": adv.get("url") or adv.get("main_url") or "",
            "discount_products": 0,
            "total_products_probed": 0,
            "hit_rate_pct": 0,
        }

        if probe:
            # Probe: pagina 1, max 50 produse
            try:
                resp = ps_call("GET", "affiliate-products", f"filters[advertiser]={adv_id}&page=1")
                if resp.ok:
                    products = resp.json().get("result", {}).get("products", [])
                    candidate["total_products_probed"] = len(products)
                    discounted = sum(
                        1 for p in products
                        if _ps_has_discount(p)
                    )
                    candidate["discount_products"] = discounted
                    if products:
                        candidate["hit_rate_pct"] = round(discounted / len(products) * 100)
                    log(f"  PS probe {name} (id={adv_id}): {discounted}/{len(products)} cu reducere")
                time.sleep(0.3)
            except Exception as e:
                log(f"  PS probe {name}: eroare {e}")

        candidates.append(candidate)

    # Sorteaza dupa numar de produse cu reducere
    candidates.sort(key=lambda x: (-x["discount_products"], x["name"]))
    log(f"PS: {len(candidates)} candidati noi gasiti")
    return candidates


def _ps_has_discount(p: dict) -> bool:
    try:
        price_vat  = float(p.get("price_vat") or 0)
        price_disc = float(p.get("price_discounted") or 0)
        return price_disc > 0 and price_disc < price_vat
    except Exception:
        return False


# ─── 2Performant scan ─────────────────────────────────────────────────────────
def scan_2p(probe: bool = True) -> list[dict]:
    """Returneaza lista de programe 2P noi (nu sunt in 2p_merchants.json)."""
    if not P2_EMAIL or not P2_PASSWORD:
        log("2P scan skip: TWO_PERFORMANT_EMAIL / TWO_PERFORMANT_PASSWORD lipsa")
        return []

    # Incarca unique_code-urile deja configurate
    known_codes = set()
    if P2_MERCHANTS_PATH.exists():
        with open(P2_MERCHANTS_PATH, encoding="utf-8") as f:
            known_codes = {m["unique_code"] for m in json.load(f)}

    log(f"2P: {len(known_codes)} merchantii configurati deja")

    # Fetch toate programele aprobate
    programs = []
    for page in range(1, 10):
        try:
            data = p2_api_get("affiliate/programs", params={"per_page": 100, "page": page})
        except TwoPerformantRateLimited as e:
            log(f"  2P programs page {page}: rate-limited ({e}) — stop")
            break
        except Exception as e:
            log(f"  2P programs page {page}: {e} — stop")
            break
        batch = data.get("programs") or (data if isinstance(data, list) else [])
        if not batch:
            break
        programs.extend(batch)
        if len(batch) < 100:
            break

    log(f"2P: {len(programs)} programe totale")

    # Fetch toate feed-urile disponibile o singura data
    feeds_by_code: dict[str, list] = defaultdict(list)
    if probe:
        try:
            feeds = p2_api_get("affiliate/product_feeds").get("product_feeds") or []
            for feed in feeds:
                prog_uc = (feed.get("program") or {}).get("unique_code") or ""
                if prog_uc:
                    feeds_by_code[prog_uc].append(feed)
            log(f"2P: {len(feeds)} feed-uri disponibile pentru {len(feeds_by_code)} programe")
        except Exception as e:
            log(f"2P: eroare la fetch feeds: {e}")

    candidates = []
    for prog in programs:
        uc = prog.get("unique_code") or prog.get("slug") or ""
        if not uc or uc in known_codes:
            continue

        # Accepta doar programele cu afiliere aprobata
        aff_status = (prog.get("affrequest") or {}).get("status") or ""
        if aff_status not in ("accepted", "approved", ""):
            continue

        name = prog.get("name") or uc
        candidate = {
            "sursa": "2performant",
            "slug": name.lower().replace(" ", "-")[:30],
            "unique_code": uc,
            "name": name,
            "url": prog.get("main_url") or prog.get("base_url") or "",
            "aff_status": aff_status,
            "feeds_count": len(feeds_by_code.get(uc, [])),
            "products_in_feed": sum(f.get("products_count", 0) for f in feeds_by_code.get(uc, [])),
            "discount_products": 0,
            "total_products_probed": 0,
            "hit_rate_pct": 0,
        }

        if probe and feeds_by_code.get(uc):
            # Probe: prima pagina din primul feed
            first_feed = feeds_by_code[uc][0]
            fid = first_feed["id"]
            try:
                data = p2_api_get(
                    f"affiliate/product_feeds/{fid}/products",
                    params={"page": 1, "per_page": 50},
                )
                prods = (data.get("products") or data.get("items") or
                         data.get("data") or (data if isinstance(data, list) else []))
                candidate["total_products_probed"] = len(prods)
                discounted = sum(1 for p in prods if _2p_has_discount(p))
                candidate["discount_products"] = discounted
                if prods:
                    candidate["hit_rate_pct"] = round(discounted / len(prods) * 100)
                log(f"  2P probe {name} ({uc}): {discounted}/{len(prods)} cu reducere")
            except TwoPerformantRateLimited as e:
                log(f"  2P probe {name}: rate-limited ({e}) — opresc probe-urile")
                probe = False
            except Exception as e:
                log(f"  2P probe {name}: eroare {e}")

        candidates.append(candidate)

    candidates.sort(key=lambda x: (-x["discount_products"], -x["products_in_feed"], x["name"]))
    log(f"2P: {len(candidates)} candidati noi gasiti")
    return candidates


def _2p_has_discount(p: dict) -> bool:
    try:
        price_sale = float(p.get("price") or 0)
        price_orig = float(p.get("old_price") or 0)
        return price_orig > 0 and price_sale > 0 and price_sale < price_orig
    except Exception:
        return False


# ─── Report ───────────────────────────────────────────────────────────────────
def save_report(ps_candidates: list, p2_candidates: list) -> Path:
    today = datetime.utcnow().strftime("%Y%m%d")
    path  = LOGS_DIR / f"merchant_scan_{today}.json"
    report = {
        "scan_date": datetime.utcnow().isoformat(),
        "ps_candidates": ps_candidates,
        "2p_candidates": p2_candidates,
        "total_candidates": len(ps_candidates) + len(p2_candidates),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return path


def print_report(ps_candidates: list, p2_candidates: list):
    print("\n" + "=" * 65)
    print(f"MERCHANT SCAN — {datetime.utcnow().strftime('%Y-%m-%d')}")
    print("=" * 65)

    def print_section(title, candidates, id_key):
        print(f"\n{'─'*30} {title} {'─'*30}")
        if not candidates:
            print("  (niciun candidat nou)")
            return
        print(f"  {'Slug':<28} {'ID/Code':<12} {'Disc/Probe':<12} {'Hit%':<6} URL")
        print(f"  {'-'*28} {'-'*12} {'-'*12} {'-'*6} {'-'*30}")
        for c in candidates[:20]:  # top 20
            id_val = c.get(id_key, "")
            probe  = f"{c['discount_products']}/{c['total_products_probed']}" if c['total_products_probed'] else "no probe"
            print(f"  {c['slug']:<28} {str(id_val):<12} {probe:<12} {c['hit_rate_pct']:<6} {c['url'][:40]}")

    print_section("PROFITSHARE — Candidati noi", ps_candidates, "adv_id")
    print_section("2PERFORMANT — Candidati noi", p2_candidates, "unique_code")

    total = len(ps_candidates) + len(p2_candidates)
    print(f"\nTotal candidati noi: {total}")
    print("Adauga manual in ps_merchants.json / 2p_merchants.json dupa review.")
    print("=" * 65)


# ─── Logging ──────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def dump_2p_raw():
    """Diagnostic: afișează programele + feed-urile 2P în formă brută,
    ca să vedem statusul real al afilierii și maparea feed→program.
    Include și răspunsul brut PS affiliate-advertisers."""
    if PS_API_USER and PS_API_KEY:
        for q in ("page=1", ""):
            r = ps_call("GET", "affiliate-advertisers", q)
            print(f"=== PS affiliate-advertisers?{q} -> {r.status_code} ===")
            print(r.text[:3000])
    if not P2_EMAIL or not P2_PASSWORD:
        log("dump 2P skip: credentiale lipsa")
        return
    programs = []
    for page in range(1, 10):
        data = p2_api_get("affiliate/programs", params={"per_page": 100, "page": page})
        batch = data.get("programs") or (data if isinstance(data, list) else [])
        if not batch:
            break
        programs.extend(batch)
        if len(batch) < 100:
            break
    print(f"=== {len(programs)} programe ===")
    for p in programs:
        aff = p.get("affrequest") or {}
        print(json.dumps({
            "name": p.get("name"), "unique_code": p.get("unique_code"),
            "slug": p.get("slug"), "status_program": p.get("status"),
            "affrequest": {k: aff.get(k) for k in ("status", "suspended", "created_at")},
            "commission": p.get("default_sale_commission_rate")
                          or p.get("commission") or p.get("default_lead_commission_amount"),
            "main_url": p.get("main_url"),
        }, ensure_ascii=False))
    try:
        feeds = p2_api_get("affiliate/product_feeds").get("product_feeds") or []
        print(f"=== {len(feeds)} feed-uri ===")
        known_codes = set()
        if P2_MERCHANTS_PATH.exists():
            with open(P2_MERCHANTS_PATH, encoding="utf-8") as fh:
                known_codes = {m["unique_code"] for m in json.load(fh)}
        for f in feeds:
            prog = f.get("program") or {}
            print(json.dumps({
                "feed_id": f.get("id"), "feed_name": f.get("name"),
                "products_count": f.get("products_count"),
                "program_name": prog.get("name"),
                "program_unique_code": prog.get("unique_code"),
            }, ensure_ascii=False))
        # Probe old_price pe TOATE feed-urile programelor NECONFIGURATE încă:
        # un feed fără old_price = 0 deal-uri structural (lecția answear/drmax).
        # Se probează și o pagină din mijloc — pagina 1 (bestsellers) e adesea
        # nedeductibilă (top-urile nu-s la reducere), mijlocul feed-ului da.
        print("=== probe old_price pe feed-uri neconfigurate ===")
        for f in feeds:
            prog = f.get("program") or {}
            uc = prog.get("unique_code") or ""
            if not uc or uc in known_codes:
                continue
            per_page = 20
            mid_page = max(2, (f.get("products_count") or 0) // (2 * per_page))
            for page in {1, mid_page}:
                try:
                    data = p2_api_get(
                        f"affiliate/product_feeds/{f['id']}/products",
                        params={"page": page, "per_page": per_page},
                    )
                    prods = (data.get("products") or data.get("items") or
                             data.get("data") or (data if isinstance(data, list) else []))
                    with_old = sum(1 for p in prods if _2p_has_discount(p))
                    print(f"PROBE {prog.get('name','?'):24} feed={f['id']:6} "
                          f"page={page:4} cu_old_price={with_old}/{len(prods)}")
                    time.sleep(1.5)
                except Exception as e:
                    print(f"PROBE {prog.get('name','?')} feed={f.get('id')} page={page}: eroare {e}")
    except Exception as e:
        log(f"dump feeds err: {e}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Merchant Discovery Scan — PS + 2P")
    parser.add_argument("--ps-only",  action="store_true", help="Doar ProfitShare")
    parser.add_argument("--2p-only",  action="store_true", help="Doar 2Performant")
    parser.add_argument("--no-probe", action="store_true", help="Fara probe (mai rapid)")
    parser.add_argument("--dump-2p", action="store_true",
                        help="Diagnostic: dump JSON brut programe + feed-uri 2P")
    args = parser.parse_args()

    if args.dump_2p:
        dump_2p_raw()
        return

    probe = not args.no_probe
    ps_candidates: list = []
    p2_candidates: list = []

    log("=== MERCHANT SCAN START ===")

    if not getattr(args, "2p_only", False):
        ps_candidates = scan_ps(probe=probe)

    if not args.ps_only:
        p2_candidates = scan_2p(probe=probe)

    print_report(ps_candidates, p2_candidates)
    report_path = save_report(ps_candidates, p2_candidates)
    log(f"Raport salvat: {report_path}")
    log("=== MERCHANT SCAN END ===")


if __name__ == "__main__":
    main()
