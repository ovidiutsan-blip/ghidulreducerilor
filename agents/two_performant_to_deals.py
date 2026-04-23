"""2Performant feed -> data/deals.json transformer.

Pentru fiecare program aprobat, fetch paginated /affiliate/programs/{unique}/products,
filtreaza produsele cu reducere reala (sale_price < price), mapeaza la Deal schema,
merge in deals.json (dedupe by product_url).

Credentials (din env / .env):
  TWO_PERFORMANT_USER_KEY    = 60-char hex, X-User-Auth-Token header
  TWO_PERFORMANT_MARKETER_CODE = aff_code (d8b71657a)

Rulare:
  python agents/two_performant_to_deals.py           # full import
  python agents/two_performant_to_deals.py --probe   # test API + afiseaza structura
  python agents/two_performant_to_deals.py --dry-run # fetch + filter, fara write
"""
from __future__ import annotations
import os, sys, json, re, time
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.2performant.com"
USER_KEY  = os.getenv("TWO_PERFORMANT_USER_KEY", "")
AFF_CODE  = os.getenv("TWO_PERFORMANT_MARKETER_CODE", "d8b71657a")

BASE      = Path(__file__).resolve().parent.parent
DEALS_PATH = BASE / "data" / "deals.json"
LOG_PATH   = BASE / "logs" / "two_performant_import.log"
LOG_PATH.parent.mkdir(exist_ok=True)

# ─── Programe aprobate ───────────────────────────────────────────────────────
# campaign_unique e din URL: businessleague.2performant.com/affiliate/program/{slug}
# -> link afiliat quicklink contine `unique=<campaign_unique>`
TARGETS = [
    # slug,       campaign_unique,  categorie site,  max_pages, min_pct, cat_whitelist
    ("answear",  "a5e9e1225",  "fashion",           20,  10, None),
    ("drmax",    "6390e3cfb",  "farmacie-sanatate", 20,  10, None),
    ("notino",   "c6dae5faa",  "beauty",            20,  10, None),
]

# ─── Auth header ─────────────────────────────────────────────────────────────
def auth_headers() -> dict:
    if not USER_KEY:
        raise ValueError("TWO_PERFORMANT_USER_KEY not set in env")
    return {
        "X-User-Auth-Token": USER_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def get_products_page(campaign_unique: str, page: int = 1, per_page: int = 50) -> dict:
    """Fetch one page of products for a 2P program."""
    url = f"{API_BASE}/affiliate/programs/{campaign_unique}/products"
    params = {"page": page, "per_page": per_page}
    r = requests.get(url, headers=auth_headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def get_programs() -> list:
    """Fetch lista de programe aprobate (pentru probe)."""
    url = f"{API_BASE}/affiliate/programs"
    r = requests.get(url, headers=auth_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


# ─── Mapping & Filtering ─────────────────────────────────────────────────────
def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]


def build_affiliate_link(campaign_unique: str, product_id) -> str:
    """Construieste link afiliat 2Performant pentru un produs."""
    return (
        f"https://event.2performant.com/events/click"
        f"?ad_type=product&unique={campaign_unique}&aff_code={AFF_CODE}&product_id={product_id}"
    )


def product_to_deal(p: dict, magazin: str, campaign_unique: str, categorie: str,
                    allowed_cats: list | None = None) -> dict | None:
    """Mapeaza un product dict 2P la schema deals.json. Returneaza None daca nu e eligibil."""
    # Suport multiple key names (API poate folosi price/sale_price sau price_vat/price_discounted)
    price_orig = float(p.get("price") or p.get("original_price") or p.get("price_vat") or 0)
    price_sale_raw = p.get("sale_price") or p.get("discounted_price") or p.get("price_discounted")
    try:
        price_sale = float(price_sale_raw) if price_sale_raw not in (None, "", 0, "0") else None
    except (ValueError, TypeError):
        price_sale = None

    # Filtru: reducere reala
    if price_sale is None or price_orig <= 0 or price_sale >= price_orig:
        return None

    pct = round((1 - price_sale / price_orig) * 100)

    # Filtru categorie (whitelist)
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

    # Normalize http -> https
    if img.startswith("http://"):
        img = "https://" + img[7:]

    aff_link = p.get("affiliate_url") or build_affiliate_link(campaign_unique, prod_id)

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
def fetch_merchant(magazin: str, campaign_unique: str, categorie: str,
                   max_pages: int, min_pct: int, allowed_cats: list | None) -> list[dict]:
    """Fetch toate paginile si returneaza deal-urile eligibile."""
    deals = []
    log(f"  Fetching {magazin} (campaign={campaign_unique})...")
    for page in range(1, max_pages + 1):
        try:
            data = get_products_page(campaign_unique, page=page)
        except requests.HTTPError as e:
            log(f"    HTTP error pagina {page}: {e}")
            break
        except Exception as e:
            log(f"    Eroare pagina {page}: {e}")
            break

        # Suport multiple response shapes
        products = (data.get("products") or data.get("items") or
                    data.get("data") or (data if isinstance(data, list) else []))

        if not products:
            log(f"    Pagina {page}: 0 produse — stop")
            break

        # Metadata pentru total pages
        meta = data.get("metadata") or data.get("meta") or {}
        total_pages = (meta.get("total_pages") or meta.get("pages") or
                       meta.get("last_page") or max_pages)

        hits = 0
        for p in products:
            deal = product_to_deal(p, magazin, campaign_unique, categorie, allowed_cats)
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

    existing_urls = {d.get("product_url") for d in existing}
    added = 0
    for d in new_deals:
        if d["product_url"] not in existing_urls:
            existing.append(d)
            existing_urls.add(d["product_url"])
            added += 1

    # Sort: activ first, procent_reducere desc
    existing.sort(key=lambda x: (not x.get("activ", True), -x.get("procent_reducere", 0)))

    if not dry_run:
        with open(DEALS_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    return {"added": added, "total": len(existing)}


# ─── Probe mode ──────────────────────────────────────────────────────────────
def probe():
    """Testeaza API-ul si afiseaza structura raspunsului."""
    log("=== PROBE MODE ===")
    # Test auth cu programele
    for magazin, campaign_unique, categorie, _, _, _ in TARGETS:
        log(f"\n--- {magazin} (campaign={campaign_unique}) ---")
        try:
            data = get_products_page(campaign_unique, page=1, per_page=3)
            log(f"Response keys: {list(data.keys())}")
            products = (data.get("products") or data.get("items") or
                        data.get("data") or (data if isinstance(data, list) else []))
            log(f"Products count in page: {len(products)}")
            if products:
                p = products[0]
                log(f"First product keys: {list(p.keys())}")
                log(f"First product sample:")
                for k, v in p.items():
                    log(f"  {k}: {str(v)[:80]}")
        except Exception as e:
            log(f"ERROR: {e}")


def list_programs():
    """Listeaza toate programele aprobate cu campaign_unique — pentru a gasi IDs noi."""
    log("=== LIST APPROVED PROGRAMS ===")
    try:
        # Incearca pagination: page 1, 2, ...
        all_programs = []
        for page in range(1, 10):
            url = f"{API_BASE}/affiliate/programs"
            params = {"filter": "accepted", "page": page, "per_page": 100}
            r = requests.get(url, headers=auth_headers(), params=params, timeout=30)
            if not r.ok:
                log(f"  Page {page}: HTTP {r.status_code} — {r.text[:200]}")
                break
            data = r.json()
            # Detecteaza structura raspunsului
            if isinstance(data, list):
                programs = data
            elif isinstance(data, dict):
                programs = (data.get("programs") or data.get("data") or
                            data.get("results") or data.get("items") or [])
            else:
                programs = []

            if not programs:
                if page == 1:
                    log(f"  Structura raspuns brut: {json.dumps(data)[:500]}")
                break
            all_programs.extend(programs)
            log(f"  Page {page}: {len(programs)} programs")
            if len(programs) < 50:
                break  # ultima pagina

        log(f"\nTotal programe aprobate: {len(all_programs)}")
        log("\n{:<30} {:<15} {:<40}".format("Advertiser", "Unique", "Domain/URL"))
        log("-" * 90)
        for p in all_programs:
            name = (p.get("name") or p.get("advertiser_name") or p.get("program_name") or
                    p.get("title") or str(p.get("id", "")))
            unique = (p.get("unique") or p.get("campaign_unique") or p.get("slug") or
                      p.get("id") or "?")
            domain = (p.get("domain") or p.get("url") or p.get("website") or
                      p.get("advertiser_domain") or "")
            log("{:<30} {:<15} {:<40}".format(str(name)[:30], str(unique)[:15], str(domain)[:40]))

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
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    probe_mode = "--probe" in args
    list_mode = "--list-programs" in args

    mode_str = "[LIST-PROGRAMS]" if list_mode else "[PROBE]" if probe_mode else "[DRY-RUN]" if dry_run else ""
    log(f"=== 2Performant Import {mode_str} ===")
    log(f"USER_KEY: {'set (' + str(len(USER_KEY)) + ' chars)' if USER_KEY else 'NOT SET'}")
    log(f"AFF_CODE: {AFF_CODE}")

    if not USER_KEY:
        log("ABORT: TWO_PERFORMANT_USER_KEY not set. Set in .env or GitHub Secrets.")
        sys.exit(1)

    if list_mode:
        list_programs()
        return

    if probe_mode:
        probe()
        return

    all_new_deals = []
    for magazin, campaign_unique, categorie, max_pages, min_pct, allowed_cats in TARGETS:
        deals = fetch_merchant(magazin, campaign_unique, categorie, max_pages, min_pct, allowed_cats)
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
