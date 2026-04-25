"""
link_validator_agent.py — Detectează linkuri 2Performant expirate și înlocuiește
dealurile afectate cu produse proaspete din același magazin.

Flow:
  1. Găsește toate dealurile 2P active cu link_afiliat
  2. Verifică rapid (HEAD request) dacă linkul duce la notoolerror
  3. Pentru fiecare deal expirat:
     a. Îl marchează inactiv în deals.json
     b. Caută un produs înlocuitor din același magazin via API 2P
     c. Adaugă produsul înlocuitor ca deal nou activ
  4. Salvează deals.json actualizat

Rulare:
  python agents/link_validator_agent.py           # dry-run (nu scrie)
  python agents/link_validator_agent.py --fix     # fix + salvează

Task Scheduler: zilnic 04:30 (după import 2P, înainte de audit 07:30)
"""
from __future__ import annotations
import os, sys, json, re, time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE       = Path(__file__).resolve().parent.parent
DEALS_PATH = BASE / "data" / "deals.json"
LOG_PATH   = BASE / "logs" / "link_validator.log"
LOG_PATH.parent.mkdir(exist_ok=True)

API_BASE = "https://api.2performant.com"

def _clean_env(key: str, default: str = "") -> str:
    return os.getenv(key, default).lstrip("﻿").strip()

EMAIL    = _clean_env("TWO_PERFORMANT_EMAIL")
PASSWORD = _clean_env("TWO_PERFORMANT_PASSWORD")
AFF_CODE = _clean_env("TWO_PERFORMANT_MARKETER_CODE", "d8b71657a")

# Sesiune auth (populata la nevoie)
_session_token: str = _clean_env("TWO_PERFORMANT_ACCESS_TOKEN")
_session_client: str = _clean_env("TWO_PERFORMANT_CLIENT_ID")
_session_uid: str   = _clean_env("TWO_PERFORMANT_UID", "ovidiutsan@yahoo.com")

CHECK_TIMEOUT  = 5    # secunde per HEAD request
CHECK_WORKERS  = 15   # fire paralele pentru verificare
MAX_REPLACEMENTS_PER_MAGAZIN = 5  # max înlocuiri per magazin per rulare

NOTOOLERROR_INDICATORS = ["notoolerror", "Link expired", "not found", "link_expired"]


def log(msg: str):
    ts = datetime.utcnow().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ─── 2P Auth ─────────────────────────────────────────────────────────────────
def _login():
    global _session_token, _session_client, _session_uid
    if not EMAIL or not PASSWORD:
        raise ValueError("Lipsesc TWO_PERFORMANT_EMAIL + TWO_PERFORMANT_PASSWORD")
    resp = requests.post(
        f"{API_BASE}/users/sign_in",
        json={"user": {"email": EMAIL, "password": PASSWORD}},
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=20,
    )
    resp.raise_for_status()
    _session_token  = resp.headers.get("access-token", "")
    _session_client = resp.headers.get("client", "")
    _session_uid    = resp.headers.get("uid", EMAIL)
    log(f"[auth] Login OK — uid={_session_uid}")


def auth_headers() -> dict:
    if not _session_token or not _session_client:
        _login()
    return {
        "access-token": _session_token,
        "token-type":   "Bearer",
        "client":       _session_client,
        "uid":          _session_uid,
        "Accept":       "application/json",
        "Content-Type": "application/json",
    }


def build_affiliate_link(unique_code: str, product_id) -> str:
    return (f"https://event.2performant.com/events/click"
            f"?ad_type=product&unique={unique_code}&aff_code={AFF_CODE}&product_id={product_id}")


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]


def fix_mojibake(s: str) -> str:
    if not s: return s
    try: return s.encode('cp1252').decode('utf-8')
    except: return s


# ─── Verificare link ──────────────────────────────────────────────────────────
def is_link_expired(url: str) -> bool:
    """Returnează True dacă link-ul afiliat duce la pagina de eroare 2P."""
    if not url or not url.startswith("http"):
        return True
    try:
        r = requests.get(
            url, timeout=CHECK_TIMEOUT, allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; GhidulReducerilor/1.0)"}
        )
        final_url = r.url.lower()
        return any(ind in final_url for ind in NOTOOLERROR_INDICATORS)
    except Exception:
        return False  # timeout = assume OK, nu dezactivam la incertitudine


def check_deals_batch(deals_2p: list[dict]) -> list[dict]:
    """Verifică paralel o listă de dealuri. Returnează cele cu link expirat."""
    expired = []
    with ThreadPoolExecutor(max_workers=CHECK_WORKERS) as pool:
        futures = {pool.submit(is_link_expired, d.get("link_afiliat", "")): d for d in deals_2p}
        for fut in as_completed(futures):
            deal = futures[fut]
            if fut.result():
                expired.append(deal)
    return expired


# ─── Fetch înlocuitor din 2P feed ────────────────────────────────────────────
def _get_feeds() -> list[dict]:
    r = requests.get(f"{API_BASE}/affiliate/product_feeds",
                     headers=auth_headers(), params={"per_page": 100}, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("product_feeds") or (data if isinstance(data, list) else [])


def _get_feed_products(feed_id: int, page: int = 1, per_page: int = 50) -> list[dict]:
    r = requests.get(f"{API_BASE}/affiliate/product_feeds/{feed_id}/products",
                     headers=auth_headers(),
                     params={"page": page, "per_page": per_page}, timeout=30)
    r.raise_for_status()
    data = r.json()
    prods = (data.get("products") or data.get("items") or
             data.get("data") or (data if isinstance(data, list) else []))
    return prods


def find_replacement(magazin: str, unique_code_program: str,
                     existing_product_urls: set[str],
                     existing_deal_ids: set[str],
                     categorie: str) -> dict | None:
    """
    Caută un produs înlocuitor din feed-ul 2P pentru magazin.
    Returneaza deal-dict gata de inserare, sau None dacă nu găsește.
    """
    try:
        feeds = _get_feeds()
        matching = [f for f in feeds
                    if (f.get("program") or {}).get("unique_code") == unique_code_program]
        if not matching:
            log(f"  [{magazin}] Niciun feed gasit pentru {unique_code_program}")
            return None

        for feed in matching:
            feed_id = feed["id"]
            for page in range(1, 5):
                prods = _get_feed_products(feed_id, page=page, per_page=50)
                if not prods:
                    break

                for p in prods:
                    try:
                        price_sale = float(p.get("price") or 0)
                        price_orig_raw = p.get("old_price")
                        price_orig = float(price_orig_raw) if price_orig_raw not in (None, "", 0, "0") else None
                    except (ValueError, TypeError):
                        continue

                    if not price_orig or price_orig <= 0 or price_sale <= 0 or price_sale >= price_orig:
                        continue

                    pct = round((1 - price_sale / price_orig) * 100)
                    if pct < 10:
                        continue

                    url = p.get("url") or p.get("product_url") or p.get("link") or ""
                    if not url or url in existing_product_urls:
                        continue

                    name = fix_mojibake((p.get("title") or p.get("name") or "").strip())
                    if not name:
                        continue

                    prod_id = p.get("id") or p.get("prid") or ""
                    prod_unique = p.get("unique_code") or ""
                    aff_link = p.get("affiliate_url") or build_affiliate_link(prod_unique or unique_code_program, prod_id)

                    # Verificăm rapid că noul link nu e și el expirat
                    if is_link_expired(aff_link):
                        continue

                    deal_id = f"2p-{magazin}-{slugify(name)[:40]}-{str(prod_id)[-8:]}"
                    if deal_id in existing_deal_ids:
                        continue

                    img_raw = p.get("structured_image_urls") or p.get("image_url") or p.get("image") or ""
                    if isinstance(img_raw, list) and img_raw:
                        first = img_raw[0]
                        img = (first.get("url") or first.get("src") or str(first)) if isinstance(first, dict) else str(first)
                    else:
                        img = str(img_raw) if img_raw else ""
                    if img.startswith("http://"):
                        img = "https://" + img[7:]

                    log(f"  [{magazin}] Gasit inlocuitor: {name[:50]} ({pct}% reducere)")
                    return {
                        "id": deal_id,
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
                        "replaced_reason": "link_validator_auto_replace",
                    }

                time.sleep(0.3)

    except Exception as e:
        log(f"  [{magazin}] Eroare la fetch inlocuitor: {e}")

    return None


# ─── 2P merchants map ─────────────────────────────────────────────────────────
def _load_2p_merchants() -> dict[str, dict]:
    """Returnează dict: magazin_slug → {unique_code, categorie}"""
    merchants_path = Path(__file__).resolve().parent / "2p_merchants.json"
    with open(merchants_path, encoding="utf-8") as f:
        merchants = json.load(f)
    return {
        m["slug"]: {"unique_code": m["unique_code"], "categorie": m.get("categorie", "general")}
        for m in merchants if m.get("activ", True)
    }


# ─── Main ─────────────────────────────────────────────────────────────────────
def run(fix_mode: bool = False):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)  # type: ignore

    log(f"=== Link Validator Agent {'[FIX]' if fix_mode else '[DRY-RUN]'} ===")

    with open(DEALS_PATH, encoding="utf-8") as f:
        deals = json.load(f)

    # Toate dealurile 2P active cu link_afiliat
    deals_2p = [
        d for d in deals
        if d.get("activ", True)
        and d.get("sursa") == "2performant"
        and d.get("link_afiliat", "").startswith("http")
    ]

    log(f"Verificare {len(deals_2p)} dealuri 2P active...")

    # Verificare paralelă
    expired_deals = check_deals_batch(deals_2p)

    if not expired_deals:
        log("✅ Niciun link expirat detectat.")
        return

    log(f"❌ {len(expired_deals)} linkuri expirate detectate:")
    for d in expired_deals:
        log(f"  • {d['id'][:60]} ({d.get('magazin')})")

    if not fix_mode:
        log("\n[DRY-RUN] Rulează cu --fix pentru a aplica corecțiile.")
        return

    # Load merchants config pentru unique_code
    merchants = _load_2p_merchants()

    # Index curent pentru deduplicare
    existing_urls: set[str] = {d.get("product_url", "") for d in deals}
    existing_ids:  set[str] = {d.get("id", "") for d in deals}

    # Track replacements per magazin
    replacements_per_magazin: dict[str, int] = {}

    now_date = datetime.utcnow().strftime("%Y-%m-%d")
    replaced = 0
    no_replacement = 0

    for exp_deal in expired_deals:
        magazin = exp_deal.get("magazin", "")
        merchant_info = merchants.get(magazin)

        # Marchează expirat
        exp_deal["activ"] = False
        exp_deal["is_active"] = False
        exp_deal["expired_at"] = now_date
        exp_deal["expired_reason"] = "link_afiliat_2p_notoolerror"

        if not merchant_info:
            log(f"  [{magazin}] Nu e in 2p_merchants.json, nu caut inlocuitor")
            no_replacement += 1
            continue

        if replacements_per_magazin.get(magazin, 0) >= MAX_REPLACEMENTS_PER_MAGAZIN:
            log(f"  [{magazin}] Atins limita de {MAX_REPLACEMENTS_PER_MAGAZIN} inlocuiri, skip")
            no_replacement += 1
            continue

        log(f"\n→ Caut inlocuitor pentru {magazin}...")
        replacement = find_replacement(
            magazin=magazin,
            unique_code_program=merchant_info["unique_code"],
            existing_product_urls=existing_urls,
            existing_deal_ids=existing_ids,
            categorie=merchant_info["categorie"],
        )

        if replacement:
            deals.append(replacement)
            existing_urls.add(replacement["product_url"])
            existing_ids.add(replacement["id"])
            replacements_per_magazin[magazin] = replacements_per_magazin.get(magazin, 0) + 1
            replaced += 1
            log(f"  ✅ Adaugat: {replacement['titlu'][:60]}")
        else:
            log(f"  ⚠️  Nu s-a gasit inlocuitor pentru {magazin}")
            no_replacement += 1

        time.sleep(1)

    # Salvare
    deals.sort(key=lambda x: (not x.get("activ", True), -x.get("procent_reducere", 0)))
    with open(DEALS_PATH, "w", encoding="utf-8") as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)

    log(f"\n{'='*50}")
    log(f"Expirate: {len(expired_deals)} | Inlocuite: {replaced} | Fara inlocuitor: {no_replacement}")
    log(f"deals.json actualizat: {len([d for d in deals if d.get('activ',True)])} dealuri active")


if __name__ == "__main__":
    fix_mode = "--fix" in sys.argv
    run(fix_mode=fix_mode)
