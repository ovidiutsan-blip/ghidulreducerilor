"""2Performant feed -> data/deals.json transformer.

Pentru fiecare program aprobat, fetch paginated /affiliate/programs/{unique_code}/products,
filtreaza produsele cu reducere reala (sale_price < price), mapeaza la Deal schema,
merge in deals.json (dedupe by product_url + id).

Auth: DeviseTokenAuth — auto-login cu email+parola sau token static.
Credentials (din env / GitHub Secrets):
  TWO_PERFORMANT_EMAIL         = email cont (stabil, nu expira) — RECOMANDAT
  TWO_PERFORMANT_PASSWORD      = parola cont (stabila, nu expira) — RECOMANDAT
  --- SAU ---
  TWO_PERFORMANT_ACCESS_TOKEN  = token temporar (expira ~14 zile)
  TWO_PERFORMANT_CLIENT_ID     = client id temporar
  TWO_PERFORMANT_UID           = uid (email)
  TWO_PERFORMANT_MARKETER_CODE = aff_code pentru quicklinks (d8b71657a)

Daca sunt setati EMAIL+PASSWORD, scriptul se auto-logheaza la fiecare run.
Nu mai e nevoie sa reimprospatezi manual tokenul.

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
from urllib.parse import quote
import requests
from dotenv import load_dotenv


def fix_mojibake(s: str) -> str:
    """Fix text encodat greșit (UTF-8 bytes interpretate ca cp1252).
    Unele API-uri returnează mojibake: 'Äƒ' în loc de 'ă', 'È›' în loc de 'ț' etc.
    """
    if not s:
        return s
    try:
        return s.encode('cp1252').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s

load_dotenv()

API_BASE     = "https://api.2performant.com"
def _clean_env(key: str, default: str = "") -> str:
    """Get env var, stripping BOM and whitespace (gh secret set via echo can prepend BOM)."""
    return os.getenv(key, default).lstrip("\ufeff").strip()

EMAIL        = _clean_env("TWO_PERFORMANT_EMAIL")
PASSWORD     = _clean_env("TWO_PERFORMANT_PASSWORD")
ACCESS_TOKEN = _clean_env("TWO_PERFORMANT_ACCESS_TOKEN")
CLIENT_ID    = _clean_env("TWO_PERFORMANT_CLIENT_ID")
UID          = _clean_env("TWO_PERFORMANT_UID", "ovidiutsan@yahoo.com")
AFF_CODE     = _clean_env("TWO_PERFORMANT_MARKETER_CODE", "d8b71657a")

# Sesiune auth — populata la primul apel auth_headers()
_session_token: str = ACCESS_TOKEN
_session_client: str = CLIENT_ID
_session_uid: str = UID

BASE            = Path(__file__).resolve().parent.parent
DEALS_PATH      = BASE / "data" / "deals.json"
LOG_PATH        = BASE / "logs" / "two_performant_import.log"
MERCHANTS_PATH  = Path(__file__).resolve().parent / "2p_merchants.json"
LOG_PATH.parent.mkdir(exist_ok=True)

# ─── Programe aprobate — citite din agents/2p_merchants.json ─────────────────
# Pentru a adauga un program nou: editeaza agents/2p_merchants.json (nu acest fisier).
# Format entry: {"slug", "unique_code", "categorie", "max_pages", "min_pct",
#                "cat_whitelist": null|[...], "activ": true}
def _load_targets() -> list:
    with open(MERCHANTS_PATH, encoding="utf-8") as f:
        merchants = json.load(f)
    return [
        (m["slug"], m["unique_code"], m["categorie"],
         m.get("max_pages", 20), m.get("min_pct", 10), m.get("cat_whitelist"))
        for m in merchants if m.get("activ", True)
    ]

TARGETS = _load_targets()
# TARGETS = [  # (kept for reference, now loaded from 2p_merchants.json)
#     ("answear",      "a5e9e1225",  "fashion",             20,  10, None),
#     ("drmax",        "6390e3cfb",  "farmacie-sanatate",   20,  10, None),
#     ("springfarma",  "1ec3596e6",  "farmacie-sanatate",   20,  10, None),
#     ("scule365",     "8e59c17b0",  "casa-gradina",        20,  10, None),
# ]

# ─── Auth + API (sesiune partajată, throttle + backoff 429 + circuit breaker) ─
sys.path.insert(0, str(Path(__file__).resolve().parent))
from two_performant_session import (  # noqa: E402
    api_get, auth_headers, _safe_json, TwoPerformantRateLimited,
)


def get_all_feeds() -> list[dict]:
    """Fetch toate feed-urile de produse disponibile pentru acest afiliat.
    Endpoint: GET /affiliate/product_feeds (nu se filtreaza per program; returneaza toate).
    Fiecare feed are: id, name, products_count, updated_at, program:{id,name,unique_code}
    """
    data = api_get("affiliate/product_feeds")
    return data.get("product_feeds") or (data if isinstance(data, list) else [])


def get_feed_products_page(feed_id: int, page: int = 1, per_page: int = 50) -> dict:
    """Fetch o pagina de produse dintr-un feed specific.
    Endpoint: GET /affiliate/product_feeds/{feed_id}/products
    """
    return api_get(f"affiliate/product_feeds/{feed_id}/products",
                   params={"page": page, "per_page": per_page})


def get_programs() -> list:
    """Fetch lista de programe (state=accepted) — pentru diagnosticare."""
    data = api_get("affiliate/programs", params={"per_page": 100})
    return data.get("programs") or (data if isinstance(data, list) else [])


# ─── Mapping & Filtering ─────────────────────────────────────────────────────
def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]


def build_affiliate_link(program_unique_code: str, product_url: str) -> str:
    """Construieste link afiliat 2Performant pentru un produs (format quicklink).

    Formatul ad_type=product cu unique-ul produsului ajunge pe notoolerror.html
    (tool nerecunoscut => click nemonetizat). Quicklink-ul cu unique-ul PROGRAMULUI
    si redirect_to salveaza click-ul si trimite userul pe pagina produsului.
    """
    return (
        f"https://event.2performant.com/events/click"
        f"?ad_type=quicklink&unique={program_unique_code}&aff_code={AFF_CODE}"
        f"&redirect_to={quote(product_url, safe='')}"
    )


def product_to_deal(p: dict, magazin: str, unique_code: str, categorie: str,
                    allowed_cats: list | None = None,
                    reject_stats: dict | None = None) -> dict | None:
    """Mapeaza un product dict 2P la schema deals.json. Returneaza None daca nu e eligibil.

    Structura campuri in feed 2P:
      price          = pretul CURENT (redus)
      old_price      = pretul ORIGINAL (inainte de reducere)
      title          = numele produsului
      url            = link produs
      structured_image_urls = lista de imagini (list of str sau list of dict)
      unique_code    = codul unic AL PRODUSULUI (folosit in link afiliat)
      id / prid      = ID numeric produs
    """
    # In feed-ul 2P: price = pret curent/redus, old_price = pret original
    try:
        price_sale = float(p.get("price") or 0)
    except (ValueError, TypeError):
        price_sale = 0.0

    price_orig_raw = p.get("old_price")
    try:
        price_orig = float(price_orig_raw) if price_orig_raw not in (None, "", 0, "0") else None
    except (ValueError, TypeError):
        price_orig = None

    if price_orig is None or price_orig <= 0 or price_sale <= 0 or price_sale >= price_orig:
        if reject_stats is not None:
            key = 'fara_old_price' if price_orig is None else 'fara_discount_real'
            reject_stats[key] = reject_stats.get(key, 0) + 1
        return None

    pct = round((1 - price_sale / price_orig) * 100)

    if allowed_cats is not None:
        feed_cat = (p.get("category") or p.get("category_name") or "").strip()
        if feed_cat not in allowed_cats:
            if reject_stats is not None:
                reject_stats['categorie_exclusa'] = reject_stats.get('categorie_exclusa', 0) + 1
            return None

    name    = fix_mojibake((p.get("title") or p.get("name") or "").strip())
    url     = p.get("url") or p.get("product_url") or p.get("link") or ""

    # structured_image_urls poate fi lista de stringuri sau lista de dict-uri
    img_raw = p.get("structured_image_urls") or p.get("image_url") or p.get("image") or ""
    if isinstance(img_raw, list) and img_raw:
        first = img_raw[0]
        if isinstance(first, dict):
            img = (first.get("url") or first.get("src") or first.get("original") or
                   next(iter(first.values()), ""))
        else:
            img = str(first)
    else:
        img = str(img_raw) if img_raw else ""

    # ID numeric produs
    prod_id = p.get("id") or p.get("prid") or ""

    if not name or not url:
        return None

    if img.startswith("http://"):
        img = "https://" + img[7:]

    # Link afiliat: quicklink cu unique-ul programului + redirect_to pagina produsului.
    # NU folosim affiliate_url din feed / formatul ad_type=product — ambele dau notoolerror.
    aff_link = build_affiliate_link(unique_code, url)

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
_feeds_cache: list[dict] | None = None  # cached in-process so we only fetch once per run

def _get_feeds_for_program(unique_code: str) -> list[dict]:
    """Returneaza feed-urile asociate unui program, dupa unique_code."""
    global _feeds_cache
    if _feeds_cache is None:
        log("  Fetching all product feeds...")
        _feeds_cache = get_all_feeds()
        log(f"  Total feeds disponibile: {len(_feeds_cache)}")
    return [f for f in _feeds_cache
            if (f.get("program") or {}).get("unique_code") == unique_code]


def fetch_merchant(magazin: str, unique_code: str, categorie: str,
                   max_pages: int, min_pct: int, allowed_cats: list | None) -> tuple[list[dict], set[str], bool]:
    """Fetch toate paginile din feed-urile programului si returneaza (deals, valid_urls, fetch_success).
    valid_urls = set de product_url pentru toate produsele cu reducere valida.
    fetch_success = True daca am primit cel putin un produs brut de la API (nu eroare).
    """
    deals = []
    valid_urls: set[str] = set()
    total_raw = 0
    reject_stats: dict[str, int] = {}
    log(f"  Fetching {magazin} (unique_code={unique_code})...")

    feeds = _get_feeds_for_program(unique_code)
    if not feeds:
        log(f"  {magazin}: niciun feed gasit pentru unique_code={unique_code}")
        return deals

    for feed in feeds:
        feed_id = feed["id"]
        feed_name = feed.get("name", f"feed-{feed_id}")
        log(f"    Feed: {feed_name} (id={feed_id}, products_count={feed.get('products_count',0)})")

        for page in range(1, max_pages + 1):
            try:
                data = get_feed_products_page(feed_id, page=page)
            except TwoPerformantRateLimited:
                raise  # propaga la main() — circuit breaker
            except requests.HTTPError as e:
                log(f"      HTTP error pagina {page}: {e}")
                break
            except Exception as e:
                log(f"      Eroare pagina {page}: {e}")
                break

            products = (data.get("products") or data.get("items") or
                        data.get("data") or (data if isinstance(data, list) else []))

            if not products:
                log(f"      Pagina {page}: 0 produse — stop")
                break

            meta = data.get("metadata") or data.get("meta") or {}
            total_pages = (meta.get("total_pages") or meta.get("pages") or
                           meta.get("last_page") or max_pages)

            hits = 0
            total_raw += len(products)
            for p in products:
                deal = product_to_deal(p, magazin, unique_code, categorie, allowed_cats,
                                       reject_stats=reject_stats)
                if deal and deal["procent_reducere"] >= min_pct:
                    deals.append(deal)
                    valid_urls.add(deal["product_url"])
                    hits += 1
                elif deal:
                    reject_stats['sub_min_pct'] = reject_stats.get('sub_min_pct', 0) + 1

            log(f"      Pagina {page}/{total_pages}: {len(products)} produse, {hits} eligibile")

            if page >= int(total_pages):
                break
            time.sleep(0.3)

    log(f"  {magazin}: {len(deals)} deals eligibile total")
    if reject_stats:
        # Diagnostic: de ce nu trec produsele filtrul (ex: feed fara old_price)
        detail = ", ".join(f"{k}={v}" for k, v in sorted(reject_stats.items()))
        log(f"  {magazin}: respinse din {total_raw} brute — {detail}")
    return deals, valid_urls, total_raw > 0


# ─── Merge in deals.json ──────────────────────────────────────────────────────
def merge_deals(new_deals: list[dict], dry_run: bool = False,
                expire_slugs: set | None = None, valid_urls: set | None = None) -> dict:
    with open(DEALS_PATH, encoding="utf-8") as f:
        existing = json.load(f)

    # ─── Expire 2P deals no longer in feed ───────────────────────────────────
    # Only expire for merchants where fetch succeeded (expire_slugs populated).
    expired = 0
    if expire_slugs and valid_urls is not None:
        now_date = datetime.utcnow().strftime("%Y-%m-%d")
        for d in existing:
            if (d.get("activ") and
                    d.get("magazin") in expire_slugs and
                    (d.get("id", "").startswith("2p-") or d.get("sursa") == "2performant") and
                    d.get("product_url") not in valid_urls):
                d["activ"] = False
                d["is_active"] = False
                d["expired_at"] = now_date
                expired += 1
        if expired:
            log(f"  Expired: {expired} 2P deals no longer in feed (reducere incheiata)")

    # Index existing deals by product_url and id for O(1) lookup.
    existing_by_url: dict[str, dict] = {}
    existing_by_id:  dict[str, dict] = {}
    for d in existing:
        if d.get("product_url"):
            existing_by_url[d["product_url"]] = d
        if d.get("id"):
            existing_by_id[d["id"]] = d

    added = 0
    updated_links = 0
    for d in new_deals:
        # Daca dealul exista deja (by product_url sau by id), actualizam link_afiliat
        # si pretul (link-ul 2P contine un unique code care expira la fiecare feed refresh).
        existing_deal = existing_by_url.get(d["product_url"]) or existing_by_id.get(d["id"])
        if existing_deal:
            # Duplicatele dezactivate de dedup NU se reactualizează/reactivează.
            if str(existing_deal.get("expired_reason", "")).startswith("dedup"):
                continue
            old_link = existing_deal.get("link_afiliat", "")
            new_link = d.get("link_afiliat", "")
            if new_link and new_link != old_link:
                existing_deal["link_afiliat"] = new_link
                existing_deal["affiliate_url"] = new_link
            # Prețul se actualizează NECONDIȚIONAT la match — altfel deal-urile
            # rămân cu prețul din ziua adăugării cât timp linkul nu se schimbă.
            existing_deal["pret_redus"] = d["pret_redus"]
            existing_deal["pret_original"] = d["pret_original"]
            existing_deal["procent_reducere"] = d["procent_reducere"]
            existing_deal["scraped_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            # Re-activam dacă fusese marcat inactiv din cauza lipsei din feed anterior
            if not existing_deal.get("activ", True):
                existing_deal["activ"] = True
                existing_deal["is_active"] = True
                existing_deal.pop("expired_at", None)
            updated_links += 1
            continue
        # Deal nou — adaugam
        existing.append(d)
        existing_by_url[d["product_url"]] = d
        existing_by_id[d["id"]] = d
        added += 1

    if updated_links:
        log(f"  Updated: {updated_links} link_afiliat-uri 2P reimprospatate (anti-expired)")

    existing.sort(key=lambda x: (not x.get("activ", True), -x.get("procent_reducere", 0)))

    if not dry_run:
        with open(DEALS_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    return {"added": added, "expired": expired, "updated_links": updated_links, "total": len(existing)}


# ─── Probe mode ──────────────────────────────────────────────────────────────
def probe():
    """Probe mode: descoperire endpoint-uri produse + structura program."""
    log("=== PROBE MODE: endpoint discovery ===")

    # Step 1: Get program list with full details incl. integer IDs
    log("\n=== Step 1: Lista programe (primele 50) ===")
    try:
        r = requests.get(f"{API_BASE}/affiliate/programs", headers=auth_headers(),
                         params={"per_page": 50}, timeout=30)
        r.raise_for_status()
        data = _safe_json(r)
        programs = data.get("programs") or (data if isinstance(data, list) else [])
        log(f"Total programe: {len(programs)}")
        targets_map = {}
        target_codes = {t[1] for t in TARGETS}
        for p in programs:
            uc = p.get("unique_code") or ""
            if uc in target_codes:
                targets_map[uc] = p
                log(f"  {p.get('name')} | unique_code={uc} | id={p.get('id')}")
                log(f"    keys: {list(p.keys())}")
                # Look for product-feed related fields
                for k in p:
                    if "product" in k.lower() or "feed" in k.lower() or "catalog" in k.lower():
                        log(f"    ** {k}: {str(p[k])[:100]}")
    except Exception as e:
        log(f"ERROR programs: {e}")
        targets_map = {t[1]: {"unique_code": t[1], "id": None} for t in TARGETS}

    # Step 2: Try multiple endpoint patterns for first target
    if not targets_map:
        log("Nu s-au gasit programele target in lista.")
        return

    first_uc, first_prog = next(iter(targets_map.items()))
    first_id = first_prog.get("id")
    log(f"\n=== Step 2: Probe endpoints pentru {first_prog.get('name','?')} "
        f"(unique={first_uc}, id={first_id}) ===")

    endpoints = [
        f"/affiliate/programs/{first_uc}/products",
        f"/affiliate/programs/{first_id}/products",
        f"/affiliate/programs/{first_uc}/product_feeds",
        f"/affiliate/programs/{first_id}/product_feeds",
        f"/affiliate/product_feeds?program_id={first_id}",
        f"/affiliate/product_feeds?unique_code={first_uc}",
        f"/affiliate/programs/{first_uc}/product_feed",
        f"/affiliate/programs/{first_id}/product_feed",
        f"/affiliate/programs/{first_id}",  # single program detail
    ]
    for ep in endpoints:
        url = f"{API_BASE}{ep}"
        try:
            resp = requests.get(url, headers=auth_headers(),
                                params={"page": 1, "per_page": 3}, timeout=15)
            preview = resp.content[:200].decode("utf-8-sig", errors="replace").replace("\n", " ")
            log(f"  {ep} → {resp.status_code} | {preview[:120]}")
            # For successful product_feeds, print full first feed object
            if resp.status_code == 200 and "product_feeds" in ep.lower():
                try:
                    pf_data = _safe_json(resp)
                    feeds = pf_data.get("product_feeds") or []
                    if feeds:
                        log(f"    [product_feeds] count={len(feeds)}, first feed keys:")
                        for k, v in feeds[0].items():
                            log(f"      {k}: {str(v)[:150]}")
                except Exception as pe:
                    log(f"    [parse error] {pe}")
        except Exception as e:
            log(f"  {ep} → ERROR: {e}")

    # Step 3: Find actual feeds for each target program and test /product_feeds/{id}/products
    log("\n=== Step 3: Feeds per target program + products endpoint test ===")
    try:
        all_feeds = get_all_feeds()
        log(f"Total feeds: {len(all_feeds)}")
        for t_slug, t_uc, t_cat, _, _, _ in TARGETS:
            matching = [f for f in all_feeds
                        if (f.get("program") or {}).get("unique_code") == t_uc]
            log(f"\n  {t_slug} (unique={t_uc}): {len(matching)} feed(s)")
            for feed in matching[:2]:  # test max 2 feeds per program
                fid = feed["id"]
                log(f"    Feed id={fid}, name={feed.get('name')}, "
                    f"products_count={feed.get('products_count')}")
                try:
                    fp = get_feed_products_page(fid, page=1, per_page=3)
                    prods = (fp.get("products") or fp.get("items") or
                             fp.get("data") or (fp if isinstance(fp, list) else []))
                    log(f"    → /product_feeds/{fid}/products → {len(prods)} products, "
                        f"keys: {list(prods[0].keys()) if prods else 'EMPTY'}")
                    if prods:
                        p0 = prods[0]
                        for k in ("name", "price", "sale_price", "image_url", "url", "id",
                                  "category", "original_price", "discounted_price"):
                            if k in p0:
                                log(f"      {k}: {str(p0[k])[:100]}")
                except Exception as fe:
                    log(f"    → ERROR: {fe}")
    except Exception as e:
        log(f"ERROR Step 3: {e}")


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
    if EMAIL and PASSWORD:
        log(f"AUTH:         auto-login cu EMAIL ({EMAIL})")
    elif ACCESS_TOKEN and CLIENT_ID:
        log(f"AUTH:         token static (access-token set, {len(ACCESS_TOKEN)} chars)")
    else:
        log("ABORT: Seteaza TWO_PERFORMANT_EMAIL + TWO_PERFORMANT_PASSWORD in GitHub Secrets.")
        sys.exit(1)
    log(f"AFF_CODE:     {AFF_CODE}")

    if list_mode:
        list_programs()
        return

    if probe_mode:
        probe()
        return

    all_new_deals: list[dict] = []
    all_seen_urls: set[str]   = set()
    successful_slugs: set[str] = set()

    for i, (magazin, unique_code, categorie, max_pages, min_pct, allowed_cats) in enumerate(TARGETS):
        if i > 0:
            time.sleep(5)  # Pauza intre marchanti pentru a evita rate limiting 429
        try:
            deals, valid_urls, success = fetch_merchant(
                magazin, unique_code, categorie, max_pages, min_pct, allowed_cats)
        except TwoPerformantRateLimited as e:
            # Circuit breaker deschis — nu mai lovim API-ul pentru restul merchantilor.
            # Fara expire pentru merchantii nefetch-uiti (successful_slugs ramane cum e).
            log(f"  ABORT rate-limit: {e} — restul merchantilor sar peste acest run.")
            break
        all_new_deals.extend(deals)
        if success:
            all_seen_urls |= valid_urls
            successful_slugs.add(magazin)

    log(f"\nTotal deal-uri noi eligibile: {len(all_new_deals)}")

    result = merge_deals(
        all_new_deals, dry_run=dry_run,
        expire_slugs=successful_slugs if not dry_run else None,
        valid_urls=all_seen_urls if not dry_run else None,
    )
    log(f"Merge: +{result['added']} adaugate, -{result['expired']} expirate, {result['total']} total in deals.json")
    if dry_run:
        log("[DRY-RUN] deals.json NU a fost modificat")


if __name__ == "__main__":
    main()
