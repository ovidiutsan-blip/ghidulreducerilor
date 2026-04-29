"""
codes_scraper.py — Agent automat pentru colectarea codurilor promoționale.

Surse:
  1. Profitshare API — campanii active cu cod promoțional
  2. 2Performant API  — campanii cu voucher cod
  3. Verificare expirare — elimină coduri expirate din codes.json

Output: data/codes.json (actualizat)

Rulare:
  python agents/marketing/codes_scraper.py
  python agents/marketing/codes_scraper.py --dry-run   # fără scriere

Integrat în pipeline după ps_feed și two_performant.
"""

import json
import os
import re
import sys
import time
import hashlib
import requests
import argparse
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Optional

BASE = Path(__file__).parent.parent.parent
CODES_PATH   = BASE / "data" / "codes.json"
STORES_PATH  = BASE / "data" / "stores.json"
LOG_DIR      = BASE / "logs"

# ─── Env ──────────────────────────────────────────────────────────────────────
PS_API_USER  = os.environ.get("PROFITSHARE_API_USER", "")
PS_API_KEY   = os.environ.get("PROFITSHARE_API_KEY", "")
TWO_P_EMAIL  = os.environ.get("TWO_PERFORMANT_EMAIL", "")
TWO_P_PASS   = os.environ.get("TWO_PERFORMANT_PASSWORD", "")
TWO_P_CODE   = os.environ.get("TWO_PERFORMANT_MARKETER_CODE", "")

TODAY = date.today().isoformat()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_codes() -> list[dict]:
    if CODES_PATH.exists():
        with open(CODES_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_codes(codes: list[dict]):
    CODES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CODES_PATH, "w", encoding="utf-8") as f:
        json.dump(codes, f, ensure_ascii=False, indent=2)


def load_stores() -> dict[str, dict]:
    """Returnează dict slug→store."""
    if STORES_PATH.exists():
        with open(STORES_PATH, encoding="utf-8") as f:
            stores = json.load(f)
        return {s.get("slug", s.get("name", "")): s for s in stores}
    return {}


def make_id(magazin: str, cod: str) -> str:
    """ID unic și stabil pentru un cod (magazin + cod)."""
    raw = f"{magazin.lower()}:{cod.strip().upper()}"
    return "code-" + hashlib.md5(raw.encode()).hexdigest()[:10]


def is_expired(data_expirare: Optional[str]) -> bool:
    if not data_expirare:
        return False
    try:
        return date.fromisoformat(data_expirare) < date.today()
    except Exception:
        return False


# Cuvinte comune EN/RO care nu sunt niciodată coduri promoționale
# (extins față de versiunea inițială ca să elimine false positives masive)
_CODE_BLACKLIST = {
    # Internet / generic
    "HTTP", "HTTPS", "WWW", "COM", "RO", "NET", "ORG", "PHP", "HTML", "JSON",
    "URL", "API", "PDF", "JPG", "PNG", "GIF", "SVG", "MP3", "MP4",
    # English filler
    "AND", "THE", "FOR", "NEW", "ALL", "OFF", "GET", "BUY", "SHOP", "FREE",
    "SALE", "DEAL", "BEST", "TOP", "HOT", "BIG", "MAX", "MIN", "PRO", "PLUS",
    # RO marketing filler ("PROMO" e text generic, nu cod)
    "PROMO", "OFERTA", "OFERTE", "REDUCERE", "REDUS", "CADOU", "GRATIS",
    "GRATUIT", "CUPON", "CUPOANE", "VOUCHER", "COD", "CODURI", "NOU",
    "NOUA", "NOUL", "PRET", "PRETURI", "STOC", "LIVRARE", "RAMBURS",
    # Brand-uri populare în RO (nu sunt coduri promo)
    "EMAG", "ALTEX", "NIKE", "APPLE", "SAMSUNG", "XIAOMI", "HUAWEI", "LENOVO",
    "ASUS", "ACER", "DELL", "HP", "MSI", "INTEL", "AMD", "SONY", "LG", "BOSCH",
    "PHILIPS", "WHIRLPOOL", "BEKO", "ARCTIC", "ELECTROLUX", "ZARA", "ADIDAS",
    "PUMA", "REEBOK", "NIVEA", "LOREAL", "GARNIER", "MAYBELLINE", "AVON",
    "ORIFLAME", "FARMEC", "DACIA", "RENAULT",
}

# "Cod-shape" definit strict: măcar o cifră (un cod marketing real are aproape mereu cifre,
# ex: SUMMER20, BLACK10, VARA25) SAU caractere mixte alfanumerice care nu formează un cuvânt
_CODE_SHAPE_RE = re.compile(r'^(?=.*\d)[A-Z0-9]{3,20}$|^[A-Z]{6,20}\d+[A-Z0-9]*$')


def _is_plausible_code(candidate: str) -> bool:
    candidate = candidate.upper().strip("-_")
    if len(candidate) < 4 or len(candidate) > 20:
        return False
    if candidate in _CODE_BLACKLIST:
        return False
    # Trebuie să aibă măcar o cifră — altfel e probabil un cuvânt
    if not any(c.isdigit() for c in candidate):
        return False
    return True


def detect_code_in_text(text: str) -> Optional[str]:
    """Caută un cod promoțional într-un text (ex: 'foloseste codul VARA25')."""
    if not text:
        return None
    # Pattern-uri context-aware (text RO normal, mixed case)
    contextual_patterns = [
        r'cod(?:ul)?[\s:]+([A-Za-z0-9\-]{3,20})',        # "codul VARA25"
        r'voucher(?:ul)?[\s:]+([A-Za-z0-9\-]{3,20})',    # "voucher BF50"
        r'cupon(?:ul)?[\s:]+([A-Za-z0-9\-]{3,20})',      # "cupon NEW10"
        r'promo[\s:]+([A-Za-z0-9\-]{3,20})',             # "promo XMAS"
        r'discount[\s:]+([A-Za-z0-9\-]{3,20})',          # "discount SAVE15"
    ]
    for pat in contextual_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).upper()
            if _is_plausible_code(candidate):
                return candidate

    # Fallback: orice șir alfanumeric all-caps cu cifră (PROMO10, BLACK20OFF)
    for m in re.finditer(r'\b([A-Z][A-Z0-9]{2,19})\b', text):
        candidate = m.group(1).upper()
        if _is_plausible_code(candidate):
            return candidate

    return None


# ─── Sursa 1: Profitshare API ──────────────────────────────────────────────────

def _ps_auth_header(method: str, uri: str) -> dict:
    """Generează header HMAC pentru Profitshare API."""
    import hmac
    import hashlib as _h
    ts = str(int(time.time()))
    msg = f"{method}\n{uri}\n{ts}"
    sig = hmac.new(PS_API_KEY.encode(), msg.encode(), _h.sha256).hexdigest()
    return {
        "Authorization": f"HMAC {PS_API_USER}:{ts}:{sig}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def fetch_ps_codes() -> list[dict]:
    """Extrage coduri promoționale din campaniile Profitshare active."""
    if not PS_API_USER or not PS_API_KEY:
        print("[codes] PS: credentiale lipsă — skip")
        return []

    results = []
    url = "https://api.profitshare.ro/campaigns?status=accepted&per_page=100"

    try:
        hdrs = _ps_auth_header("GET", "/campaigns")
        resp = requests.get(url, headers=hdrs, timeout=20)
        if resp.status_code != 200:
            print(f"[codes] PS: HTTP {resp.status_code} — {resp.text[:200]}")
            return []

        campaigns = resp.json().get("data", [])
        print(f"[codes] PS: {len(campaigns)} campanii active")

        for c in campaigns:
            # Caută câmpuri care pot conține un cod promo
            texts_to_scan = [
                c.get("name", ""),
                c.get("description", ""),
                c.get("terms", ""),
                c.get("promo_code", ""),
                c.get("voucher", ""),
                c.get("coupon", ""),
            ]
            full_text = " ".join(str(t) for t in texts_to_scan if t)

            cod = (
                c.get("promo_code") or
                c.get("voucher") or
                c.get("coupon") or
                detect_code_in_text(full_text)
            )
            if not cod:
                continue

            # Determină magazinul
            store_slug = (
                c.get("store_slug") or
                c.get("program_slug") or
                ""
            ).lower().replace("-", "_")

            descriere = c.get("description") or c.get("name") or "Reducere"
            valoare   = c.get("value") or c.get("discount") or ""
            end_date  = c.get("end_date") or c.get("expires_at") or ""
            aff_url   = c.get("affiliate_url") or c.get("tracking_url") or ""

            entry = {
                "id":            make_id(store_slug, cod),
                "magazin":       store_slug,
                "cod":           cod.strip().upper(),
                "descriere":     descriere[:200],
                "valoare":       str(valoare),
                "tip":           "procent" if "%" in str(valoare) else "fix",
                "data_expirare": end_date[:10] if end_date else "",
                "link_afiliat":  aff_url,
                "affiliate_url": aff_url,
                "verificat":     True,
                "sursa":         "profitshare",
                "updated_at":    TODAY,
            }
            results.append(entry)
            print(f"[codes] PS: găsit cod '{cod}' pentru '{store_slug}'")

    except Exception as e:
        print(f"[codes] PS eroare: {e}")

    return results


# ─── Sursa 2: 2Performant API ──────────────────────────────────────────────────

def _2p_get_token() -> Optional[str]:
    """Obține token JWT 2Performant."""
    if not TWO_P_EMAIL or not TWO_P_PASS:
        return None
    try:
        resp = requests.post(
            "https://api.2performant.com/users/sign_in",
            json={"email": TWO_P_EMAIL, "password": TWO_P_PASS},
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("user", {}).get("authentication_token")
    except Exception as e:
        print(f"[codes] 2P auth error: {e}")
    return None


def fetch_2p_codes() -> list[dict]:
    """Extrage coduri promoționale din programele 2Performant."""
    if not TWO_P_EMAIL or not TWO_P_PASS:
        print("[codes] 2P: credentiale lipsă — skip")
        return []

    token = _2p_get_token()
    if not token:
        print("[codes] 2P: auth eșuată")
        return []

    results = []
    headers = {
        "X-User-Email": TWO_P_EMAIL,
        "X-User-Token": token,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.get(
            "https://api.2performant.com/affiliate/programs?filter[affilated]=true&per_page=100",
            headers=headers,
            timeout=15,
        )
        if resp.status_code != 200:
            print(f"[codes] 2P: HTTP {resp.status_code}")
            return []

        programs = resp.json().get("data", [])
        print(f"[codes] 2P: {len(programs)} programe afiliate")

        for prog in programs:
            attrs = prog.get("attributes", prog)
            texts = [
                attrs.get("name", ""),
                attrs.get("description", ""),
                attrs.get("promo_code", ""),
                attrs.get("voucher_code", ""),
                attrs.get("special_offer", ""),
            ]
            full_text = " ".join(str(t) for t in texts if t)
            cod = (
                attrs.get("promo_code") or
                attrs.get("voucher_code") or
                detect_code_in_text(full_text)
            )
            if not cod:
                continue

            slug = (attrs.get("slug") or attrs.get("unique_code") or "").lower()
            aff_url = attrs.get("affiliate_url") or ""
            end_date = attrs.get("campaign_end_date") or ""

            entry = {
                "id":            make_id(slug, cod),
                "magazin":       slug,
                "cod":           cod.strip().upper(),
                "descriere":     (attrs.get("description") or attrs.get("name") or "")[:200],
                "valoare":       str(attrs.get("commission", "")),
                "tip":           "procent",
                "data_expirare": end_date[:10] if end_date else "",
                "link_afiliat":  aff_url,
                "affiliate_url": aff_url,
                "verificat":     True,
                "sursa":         "2performant",
                "updated_at":    TODAY,
            }
            results.append(entry)
            print(f"[codes] 2P: găsit cod '{cod}' pentru '{slug}'")

    except Exception as e:
        print(f"[codes] 2P eroare: {e}")

    return results


# ─── Curățare coduri expirate ──────────────────────────────────────────────────

def remove_expired(codes: list[dict]) -> tuple[list[dict], int]:
    """Elimină codurile expirate. Returnează (lista_curata, nr_eliminate)."""
    active = []
    removed = 0
    for c in codes:
        if is_expired(c.get("data_expirare")):
            print(f"[codes] Expirat: '{c['cod']}' ({c.get('magazin','')}) — {c.get('data_expirare')}")
            removed += 1
        else:
            active.append(c)
    return active, removed


# ─── Merge fără duplicate ─────────────────────────────────────────────────────

def merge_codes(existing: list[dict], new_codes: list[dict]) -> tuple[list[dict], int, int]:
    """
    Combină listele fără duplicate (pe baza id).
    Actualizează codurile existente dacă s-a schimbat ceva.
    Returnează (lista_finala, nr_adaugate, nr_actualizate).
    """
    existing_map = {c["id"]: c for c in existing}
    added = 0
    updated = 0

    for nc in new_codes:
        cid = nc["id"]
        if cid not in existing_map:
            existing_map[cid] = nc
            added += 1
        else:
            # Actualizează câmpurile relevante
            old = existing_map[cid]
            changed = False
            for field in ("data_expirare", "descriere", "valoare", "link_afiliat", "affiliate_url"):
                if nc.get(field) and nc[field] != old.get(field):
                    old[field] = nc[field]
                    changed = True
            old["updated_at"] = TODAY
            if changed:
                updated += 1

    return list(existing_map.values()), added, updated


# ─── Runner principal ─────────────────────────────────────────────────────────

def run(dry_run: bool = False) -> dict:
    print(f"\n{'='*55}")
    print(f"🎟️  Codes Scraper — {TODAY}")
    print(f"{'='*55}\n")

    existing = load_codes()
    print(f"Coduri existente: {len(existing)}")

    # 1. Elimină expirate
    existing, removed_count = remove_expired(existing)
    if removed_count:
        print(f"→ {removed_count} coduri expirate eliminate")

    # 2. Fetch din Profitshare
    print("\n[1/2] Fetch Profitshare...")
    ps_codes = fetch_ps_codes()
    print(f"      → {len(ps_codes)} coduri găsite")

    # 3. Fetch din 2Performant
    print("\n[2/2] Fetch 2Performant...")
    two_p_codes = fetch_2p_codes()
    print(f"      → {len(two_p_codes)} coduri găsite")

    # 4. Merge
    all_new = ps_codes + two_p_codes
    final, added, updated = merge_codes(existing, all_new)

    print(f"\n📊 Sumar:")
    print(f"   Expirate eliminate: {removed_count}")
    print(f"   Noi adăugate:       {added}")
    print(f"   Actualizate:        {updated}")
    print(f"   Total final:        {len(final)}")

    if not dry_run:
        save_codes(final)
        print(f"\n✅ Salvat: {CODES_PATH}")
    else:
        print("\n⚠️  DRY-RUN — nu s-a scris nimic")

    # Log
    log_dir = LOG_DIR / "codes"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"codes_run_{TODAY}.json"
    log_data = {
        "date":             TODAY,
        "expired_removed":  removed_count,
        "ps_found":         len(ps_codes),
        "2p_found":         len(two_p_codes),
        "added":            added,
        "updated":          updated,
        "total":            len(final),
    }
    if not dry_run:
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)

    return log_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Codes Scraper — actualizare coduri promoționale")
    parser.add_argument("--dry-run", action="store_true", help="Rulează fără a scrie codes.json")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
