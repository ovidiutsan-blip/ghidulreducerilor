"""2Performant feed -> data/deals.json transformer.

Pentru fiecare program aprobat, fetch paginated /affiliate/programs/{unique_code}/products,
filtreaza produsele cu reducere reala (sale_price < price), mapeaza la Deal schema,
merge in deals.json (dedupe by product_url + id).

Auth: DeviseTokenAuth (access-token / client / uid headers).
Credentials (din env / .env):
  TWO_PERFORMANT_ACCESS_TOKEN  = access-token din cookie auth_headers
  TWO_PERFORMANT_CLIENT_ID     = client din cookie auth_headers
  TWO_PERFORMANT_UID           = uid (email) din cookie auth_headers
  TWO_PERFORMANT_MARKETER_CODE = aff_code pentru quicklinks (d8b71657a)

Reimprospatare credentials: expira dupa ~14 zile. Extrage din browser:
  1. Mergi la businessleague.2performant.com (logat)
  2. DevTools > Application > Cookies > auth_headers
  3. Actualizeaza secretele GitHub: TWO_PERFORMANT_ACCESS_TOKEN, TWO_PERFORMANT_CLIENT_ID

Rulare:
  python agents/two_performant_to_deals.py           # full import
  python agents/two_performant_to_deals.py --probe   # test API + afiseaza structura
  python agents/two_performant_to_deals.py --dry-run # fetch + filter, fara write
  python agents/two_performant_to_deals.py --list-programs  # listeaza programe aprobate
"""
from __future__ import annotations
import os, sys, json, re, time
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE     = "https://api.2performant.com"
def _clean_env(key: str, default: str = "") -> str:
    """Get env var, stripping BOM and whitespace (gh secret set via echo can prepend BOM)."""
    return os.getenv(key, default).lstrip("\ufeff").strip()

ACCESS_TOKEN = _clean_env("TWO_PERFORMANT_ACCESS_TOKEN")
CLIENT_ID    = _clean_env("TWO_PERFORMANT_CLIENT_ID")
UID          = _clean_env("TWO_PERFORMANT_UID", "ovidiutsan@yahoo.com")
AFF_CODE     = _clean_env("TWO_PERFORMANT_MARKETER_CODE", "d8b71657a")

BASE       = Path(__file__).resolve().parent.parent
DEALS_PATH = BASE / "data" / "deals.json"
LOG_PATH   = BASE / "logs" / "two_performant_import.log"
LOG_PATH.parent.mkdir(exist_ok=True)

# ─── Programe aprobate (unique_code din /affiliate/programs?state=accepted) ──
# Adauga noi randuri cand primesti aprobare de la un program nou.
# Status la 2026-04-23:
#   answear.ro    → aff=accepted  ✅
#   drmax.ro      → aff=accepted  ✅
#   springfarma   → aff=accepted  ✅ (adaugat 2026-04-23)
#   scule365.ro   → aff=accepted  ✅ (adaugat 2026-04-23)
#   elefant.ro    → aff=deleted   ❌ (afiliere revocata)
#   fashiondays   → aff=deleted   ❌ (afiliere revocata)
#   notino        → nu e pe 2P    ❌ (cauta pe alt network)
#   bookzone.ro   → aff=pending   ⏳ (in asteptare aprobare)
TARGETS = [
    # slug,          unique_code,   categorie site,       max_pages, min_pct, cat_whitelist
    ("answear",      "a5e9e1225",  "fashion",             20,  10, None),
    ("drmax",        "6390e3cfb",  "farmacie-sanatate",   20,  10, None),
    ("springfarma",  "1ec3596e6",  "farmacie-sanatate",   20,  10, None),
    ("scule365",     "8e59c17b0",  "casa-gradina",        20,  10, None),
]

# ─── Auth (DeviseTokenAuth) ───────────────────────────────────────────────────
def auth_headers() -> dict:
    if not ACCESS_TOKEN or not CLIENT_ID:
        raise ValueError(
            "TWO_PERFORMANT_ACCESS_TOKEN / TWO_PERFORMANT_CLIENT_ID nu sunt setate. "
            "Extrage din cookie auth_headers pe businessleague.2performant.com si "
            "seteaza ca GitHub Secrets."
        )
    return {
        "access-token": ACCESS_TOKEN,
        "token-type":   "Bearer",
        "client":       CLIENT_ID,
        "uid":          UID,
        "Accept":       "application/json",
        "Content-Type": "application/json",
    }


def _safe_json(r) -> any:
    """Parse JSON response, stripping UTF-8 BOM if present."""
    import json as _json
    return _json.loads(r.content.decode("utf-8-sig"))


def get_products_page(unique_code: str, page: int = 1, per_page: int = 50) -> dict:
    """Fetch one page of products for a 2P program."""
    url = f"{API_BASE}/affiliate/programs/{unique_code}/products"
    params = {"page": page, "per_page": per_page}
    r = requests.get(url, headers=auth_headers(), params=params, timeout=30)
    r.raise_for_status()
    return _safe_json(r)


def get_programs() -> list:
    """Fetch lista de programe (state=accepted) — pentru diagnosticare."""
    url = f"{API_BASE}/affiliate/programs"
    r = requests.get(url, headers=auth_headers(), params={"per_page": 100}, timeout=30)
    r.raise_for_status()
    data = _safe_json(r)
    return data.get("programs") or (data if isinstance(data, list) else [])


# ─── Mapping & Filtering ─────────────────────────────────────────────────────
def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]


def build_affiliate_link(unique_code: str, product_id) -> str:
    """Construieste link afiliat 2Performant pentru un produs."""
    return (
        f"https://event.2performant.com/events/click"
        f"?ad_type=product&unique={unique_code}&aff_code={AFF_CODE}&product_id={product_id}"
    )


def product_to_deal(p: dict, magazin: str, unique_code: str, categorie: str,
                    allowed_cats: list | None = None) -> dict | None:
    """Mapeaza un product dict 2P la schema deals.json. Returneaza None daca nu e eligibil."""
    price_orig = float(p.get("price") or p.get("original_price") or p.get("price_vat") or 0)
    price_sale_raw = p.get("sale_price") or p.get("discounted_price") or p.get("price_discounted")
    try:
        price_sale = float(price_sale_raw) if price_sale_raw not in (None, "", 0, "0") else None
    except (ValueError, TypeError):
        price_sale = None

    if price_sale is None or price_orig <= 0 or price_sale >= price_orig:
        return None

    pct = round((1 - price_sale / price_orig) * 100)

    if allowed_cats is not None:
        feed_cat = (p.get("category") or p.get("category_name") or "").strip()
        if feed_cat not in allowed_cats:
            return None

    name    = (p.get("name") or p.get("title") or "").strip()
    url     = p.get("url") or p.get("product_url") or p.get("link") or ""
    img     = p.get("image_url") or p.get("image") or p.get("image_original") or ""
    prod_id = p.get("id") or p.get("unique") or ""

    if not name or not url:
        return None

    if img.startswith("http://"):
        img = "https://" + img[7:]

    aff_link = p.get("affiliate_url") or build_affiliate_link(unique_code, prod_id)

    return {
        "id": f"2p-{magazin}-{slugify(name)[:40]}-{str(prod_id)[-8:]}",
        "slug": slugify(name),
        "magazin": magazin,
        "titlu": name[:200],
        "image": img,
        "imagine_url": img,
        "pret_original": round(price_orig, 2),
        "pret_redus": round(price_sale, 2),
        "procent_reducere": pct,
        "link_afiliat": aff_link,
        "product_url": url,
        "categorie": categorie,
        "data_adaugare": datetime.utcnow().strftime("%Y-%m-%d"),
        "activ": True,
        "is_active": True,
        "sursa": "2performant",
    }


# ─── Import per merchant ──────────────────────────────────────────────────────
def fetch_merchant(magazin: str, unique_code: str, categorie: str,
                   max_pages: int, min_pct: int, allowed_cats: list | None) -> list[dict]:
    """Fetch toate paginile si returneaza deal-urile eligibile."""
    deals = []
    log(f"  Fetching {magazin} (unique_code={unique_code})...")
    for page in range(1, max_pages + 1):
        try:
            data = get_products_page(unique_code, page=page)
        except requests.HTTPError as e:
            log(f"    HTTP error pagina {page}: {e}")
            break
        except Exception as e:
            log(f"    Eroare pagina {page}: {e}")
            break

        products = (data.get("products") or data.get("items") or
                    data.get("data") or (data if isinstance(data, list) else []))

        if not products:
            log(f"    Pagina {page}: 0 produse — stop")
            break

        meta = data.get("metadata") or data.get("meta") or {}
        total_pages = (meta.get("total_pages") or meta.get("pages") or
                       meta.get("last_page") or max_pages)

        hits = 0
        for p in products:
            deal = product_to_deal(p, magazin, unique_code, categorie, allowed_cats)
            if deal and deal["procent_reducere"] >= min_pct:
                deals.append(deal)
                hits += 1

        log(f"    Pagina {page}/{total_pages}: {len(products)} produse, {hits} eligibile")

        if page >= int(total_pages):
            break
        time.sleep(0.3)

    log(f"  {magazin}: {len(deals)} deals eligibile total")
    return deals


# ─── Merge in deals.json ──────────────────────────────────────────────────────
def merge_deals(new_deals: list[dict], dry_run: bool = False) -> dict:
    with open(DEALS_PATH, encoding="utf-8") as f:
        existing = json.load(f)

    existing_urls = {d.get("product_url") or d.get("link_afiliat") for d in existing}
    existing_ids  = {d.get("id") for d in existing}
    added = 0
    for d in new_deals:
        if d["product_url"] in existing_urls or d["id"] in existing_ids:
            continue
        existing.append(d)
        existing_urls.add(d["product_url"])
        existing_ids.add(d["id"])
        added += 1

    existing.sort(key=lambda x: (not x.get("activ", True), -x.get("procent_reducere", 0)))

    if not dry_run:
        with open(DEALS_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    return {"added": added, "total": len(existing)}


# ─── Probe mode ──────────────────────────────────────────────────────────────
def probe():
    log("=== PROBE MODE ===")
    for magazin, unique_code, categorie, _, _, _ in TARGETS:
        log(f"\n--- {magazin} (unique_code={unique_code}) ---")
        try:
            data = get_products_page(unique_code, page=1, per_page=3)
            log(f"Response keys: {list(data.keys())}")
            products = (data.get("products") or data.get("items") or
                        data.get("data") or (data if isinstance(data, list) else []))
            log(f"Products count in page: {len(products)}")
            if products:
                p = products[0]
                log(f"First product keys: {list(p.keys())}")
                for k, v in list(p.items())[:15]:
                    log(f"  {k}: {str(v)[:80]}")
        except Exception as e:
            log(f"ERROR: {e}")


def list_programs():
    """Listeaza toate programele disponibile cu unique_code si status afiliere."""
    log("=== LIST PROGRAMS (state=accepted) ===")
    try:
        all_programs = []
        for page in range(1, 5):
            r = requests.get(
                f"{API_BASE}/affiliate/programs",
                headers=auth_headers(),
                params={"per_page": 100, "page": page},
                timeout=30
            )
            if not r.ok:
                log(f"  Page {page}: HTTP {r.status_code}")
                break
            data = _safe_json(r)
            programs = data.get("programs") or (data if isinstance(data, list) else [])
            if not programs:
                break
            all_programs.extend(programs)
            log(f"  Page {page}: {len(programs)} programs")
            if len(programs) < 100:
                break

        log(f"\nTotal programe: {len(all_programs)}")
        log("{:<30} {:<12} {:<10} {:<45}".format("Advertiser", "Unique", "AffStatus", "URL"))
        log("-" * 100)
        for p in all_programs:
            name    = (p.get("name") or "").strip()
            unique  = p.get("unique_code") or p.get("slug") or str(p.get("id", "?"))
            url     = p.get("main_url") or p.get("base_url") or ""
            aff_st  = (p.get("affrequest") or {}).get("status") or "—"
            log("{:<30} {:<12} {:<10} {:<45}".format(
                str(name)[:30], str(unique)[:12], str(aff_st)[:10], str(url)[:45]
            ))
    except Exception as e:
        log(f"ERROR: {e}")


# ─── Logging ─────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.utcnow().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    # Ensure stdout uses UTF-8 in CI environments (avoids latin-1 BOM encoding errors)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = sys.argv[1:]
    dry_run    = "--dry-run" in args
    probe_mode = "--probe" in args
    list_mode  = "--list-programs" in args

    mode_str = "[LIST-PROGRAMS]" if list_mode else "[PROBE]" if probe_mode else "[DRY-RUN]" if dry_run else ""
    log(f"=== 2Performant Import {mode_str} ===")
    log(f"ACCESS_TOKEN: {'set (' + str(len(ACCESS_TOKEN)) + ' chars)' if ACCESS_TOKEN else 'NOT SET ⚠️'}")
    log(f"CLIENT_ID:    {'set (' + str(len(CLIENT_ID)) + ' chars)' if CLIENT_ID else 'NOT SET ⚠️'}")
    log(f"UID:          {UID}")
    log(f"AFF_CODE:     {AFF_CODE}")

    if not ACCESS_TOKEN or not CLIENT_ID:
        log("ABORT: Seteaza TWO_PERFORMANT_ACCESS_TOKEN si TWO_PERFORMANT_CLIENT_ID.")
        log("Extrage din: businessleague.2performant.com > DevTools > Cookies > auth_headers")
        sys.exit(1)

    if list_mode:
        list_programs()
        return

    if probe_mode:
        probe()
        return

    all_new_deals = []
    for magazin, unique_code, categorie, max_pages, min_pct, allowed_cats in TARGETS:
        deals = fetch_merchant(magazin, unique_code, categorie, max_pages, min_pct, allowed_cats)
        all_new_deals.extend(deals)

    log(f"\nTotal deal-uri noi eligibile: {len(all_new_deals)}")

    if all_new_deals:
        result = merge_deals(all_new_deals, dry_run=dry_run)
        log(f"Merge: +{result['added']} adaugate, {result['total']} total in deals.json")
        if dry_run:
            log("[DRY-RUN] deals.json NU a fost modificat")
    else:
        log("Niciun deal nou de adaugat.")


if __name__ == "__main__":
    main()
