#!/usr/bin/env python3
"""
image_repair.py — Reparare automata imagini lipsa/invalide din deals.json
=========================================================================
Strategie automata in 3 niveluri (fara liste hard-codate de magazine):

  Nivel 1 — urllib cu Referer:
    Scrape pagina produsului → gaseste og:image → verifica daca URL-ul imaginii
    e accesibil direct (probe HEAD). Daca da, salveaza URL-ul remote.

  Nivel 2 — Playwright response interception (download local):
    Daca pagina sau imaginea e blocata de CloudFlare/WAF → Playwright headless
    deschide pagina produsului, intercepteaza raspunsul imaginii din fluxul
    browserului (care are cookies CF valide), descarca bytes-ii imaginii si
    o salveaza local in public/images/{magazin}/. URL devine /images/{magazin}/...

  Nivel 3 — Canvas capture:
    Daca nu se intercepteaza nimic in flux, incearca sa extraga imaginea din
    DOM via JavaScript canvas.

Avantaj: orice magazin nou cu CloudFlare CDN e acoperit automat, fara config.

Utilizare:
  python scripts/image_repair.py                   # fix all, salveaza
  python scripts/image_repair.py --dry-run          # raporteaza fara a salva
  python scripts/image_repair.py --store mathaus    # doar un magazin
  python scripts/image_repair.py --workers 4        # parallelism urllib
"""
import sys
import json
import time
import re
import base64
import argparse
import logging
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
DEALS_PATH = ROOT / "data" / "deals.json"
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "image_repair.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("image_repair")

# ─── Configuratie ────────────────────────────────────────────────────────────

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

FETCH_HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
}

# Referer per magazin (derivat din domeniu daca nu e specificat explicit)
KNOWN_REFERERS: dict[str, str] = {
    "mathaus": "https://www.mathaus.ro/",
    "vegis": "https://www.vegis.ro/",
    "hiris": "https://www.hiris.ro/",
    "novodoors": "https://www.novodoors.ro/",
    "casesmart": "https://www.casesmart.ro/",
    "case-smart": "https://www.casesmart.ro/",
}

# Patterns pentru imagini invalide / placeholder
BAD_PATTERNS = (
    "lazy-loader", "/layout/", "placeholder", "no-image",
    "noimage", "nopicture", "no_image", "default-product",
)

OG_RE = re.compile(
    r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']'
    r'|<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
    re.I,
)


# ─── Utilitare ───────────────────────────────────────────────────────────────

def is_bad_image(url: str | None) -> bool:
    if not url or not url.startswith("http"):
        return True
    u = url.lower()
    if u.endswith(".gif"):
        return True
    return any(p in u for p in BAD_PATTERNS)


def is_local_url(url: str | None) -> bool:
    """True daca imaginea e deja servita local (nu mai necesita repair)."""
    return bool(url and url.startswith("/images/"))


def needs_repair(deal: dict) -> bool:
    img = deal.get("imagine_url") or ""
    if is_local_url(img):
        return False  # deja downloadata local, OK
    return is_bad_image(img)


def store_referer(magazin: str) -> str:
    """Returneaza Referer pentru un magazin (explicit sau derivat din slug)."""
    if magazin in KNOWN_REFERERS:
        return KNOWN_REFERERS[magazin]
    return f"https://www.{magazin}.ro/"


def safe_filename(deal_id: str, ext: str = "jpg") -> str:
    safe = re.sub(r"[^a-z0-9-]", "", deal_id.lower())[:60]
    return f"{safe}.{ext}"


def ext_from_url(url: str) -> str:
    e = url.split("?")[0].rsplit(".", 1)[-1].lower()
    return e if e in ("jpg", "jpeg", "png", "webp") else "jpg"


def local_img_dir(magazin: str) -> Path:
    d = ROOT / "public" / "images" / magazin
    d.mkdir(parents=True, exist_ok=True)
    return d


def local_img_url(magazin: str, filename: str) -> str:
    return f"/images/{magazin}/{filename}"


# ─── Nivel 1: urllib ─────────────────────────────────────────────────────────

def fetch_page_html(url: str, referer: str = "") -> str | None:
    """Descarca HTML pagina via urllib. Returneaza HTML sau None."""
    try:
        headers = dict(FETCH_HEADERS)
        if referer:
            headers["Referer"] = referer
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=14) as resp:
            return resp.read(80_000).decode("utf-8", errors="ignore")
    except Exception:
        return None


def probe_image_url(url: str, referer: str = "") -> bool:
    """
    Verifica daca un URL de imagine e accesibil direct (HEAD request).
    Returneaza True daca poate fi descarcata de Next.js /_next/image.
    """
    try:
        headers = {
            "User-Agent": "NextJS-Image-Optimizer/14",
            "Accept": "image/*",
        }
        if referer:
            headers["Referer"] = referer
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status < 400
    except Exception:
        return False


def fix_via_urllib(deal: dict) -> str | None:
    """
    Nivel 1: Scrape og:image via urllib + verifica daca URL-ul e accesibil.
    Returneaza URL imagine valid sau None.
    """
    product_url = (
        deal.get("product_url") or deal.get("link_afiliat") or deal.get("url") or ""
    )
    if not product_url or not product_url.startswith("http"):
        return None

    magazin = deal.get("magazin", "")
    referer = store_referer(magazin)

    html = fetch_page_html(product_url, referer)
    if not html:
        log.debug("  L1: pagina inaccesibila urllib: %s", product_url[:60])
        return None

    m = OG_RE.search(html)
    if not m:
        log.debug("  L1: no og:image pe %s", product_url[:60])
        return None

    img_url = (m.group(1) or m.group(2) or "").strip()
    if not img_url or not img_url.startswith("http") or is_bad_image(img_url):
        return None

    # Verifica daca imaginea e accesibila direct (nu blocata de CDN)
    if probe_image_url(img_url, referer):
        return img_url

    log.debug("  L1: imaginea gasita dar CDN blocat (403): %s", img_url[:60])
    return None  # Trecem la Nivel 2


# ─── Nivel 2 & 3: Playwright ─────────────────────────────────────────────────

def fix_via_playwright(deal: dict) -> str | None:
    """
    Nivel 2+3: Playwright response interception + download local.
    Deschide pagina produsului cu un context browser proaspat (fara cache),
    intercepteaza bytele imaginilor din fluxul browserului, descarca cea mai
    mare imagine si o salveaza local in public/images/{magazin}/.
    Returneaza URL local (/images/{magazin}/...) sau None.
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        log.warning("  L2: Playwright nu e instalat — skip")
        return None

    product_url = (
        deal.get("product_url") or deal.get("link_afiliat") or deal.get("url") or ""
    )
    if not product_url or not product_url.startswith("http"):
        return None

    magazin = deal.get("magazin", "")
    deal_id = deal["id"]
    current_img = deal.get("imagine_url", "")

    captured: dict[str, bytes] = {}

    def on_resp(r):
        if r.status != 200:
            return
        ct = r.headers.get("content-type", "")
        if "image" not in ct:
            return
        url = r.url
        # Exclude imagini mici (icoane, tracking pixels)
        try:
            b = r.body()
            if len(b) > 2000:
                captured[url] = b
        except Exception:
            pass

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            # Context NOU per deal = fara cache intre requesturi
            ctx = browser.new_context(
                user_agent=BROWSER_UA,
                viewport={"width": 1280, "height": 800},
                locale="ro-RO",
            )
            ctx.route("**/*.{woff,woff2,ttf,mp4,avi}", lambda r: r.abort())

            page = ctx.new_page()
            page.on("response", on_resp)

            try:
                page.goto(product_url, timeout=25000, wait_until="domcontentloaded")
                page.evaluate("window.scrollTo(0, 500)")
                page.wait_for_timeout(2500)
            except PWTimeout:
                log.debug("  L2: TIMEOUT pentru %s", product_url[:60])
                browser.close()
                return None

            # Nivel 2: alege cea mai mare imagine captata din flux
            if captured:
                best_url = max(captured, key=lambda u: len(captured[u]))
                best_bytes = captured[best_url]
                act_ext = ext_from_url(best_url)
                fn = safe_filename(deal_id, act_ext)
                dest = local_img_dir(magazin) / fn
                dest.write_bytes(best_bytes)
                size_kb = len(best_bytes) // 1024
                log.info("  L2: OK %dKB -> /images/%s/%s", size_kb, magazin, fn)
                browser.close()
                return local_img_url(magazin, fn)

            # Nivel 3: Canvas capture din DOM
            log.debug("  L3: nicio imagine interceptata, incerc canvas")
            img_b64 = page.evaluate("""() => {
                const selectors = [
                    '.pdp-main-image img', '.product-image img',
                    'img[itemprop="image"]', '.gallery-image img',
                    '.product-detail img', 'img.product-main-image',
                    'picture img', '[class*="product"] img'
                ];
                for (const sel of selectors) {
                    const img = document.querySelector(sel);
                    if (img && img.complete && img.naturalWidth > 50) {
                        try {
                            const c = document.createElement('canvas');
                            c.width = img.naturalWidth;
                            c.height = img.naturalHeight;
                            c.getContext('2d').drawImage(img, 0, 0);
                            return c.toDataURL('image/jpeg', 0.9).split(',')[1];
                        } catch(e) {}
                    }
                }
                return null;
            }""")

            browser.close()

            if img_b64:
                bts = base64.b64decode(img_b64)
                fn = safe_filename(deal_id, "jpg")
                dest = local_img_dir(magazin) / fn
                dest.write_bytes(bts)
                log.info("  L3: canvas OK %dKB -> /images/%s/%s", len(bts) // 1024, magazin, fn)
                return local_img_url(magazin, fn)

    except Exception as e:
        log.debug("  L2/L3 error pentru %s: %s", deal_id, e)

    return None


# ─── Core ────────────────────────────────────────────────────────────────────

def fix_one(deal: dict) -> tuple[str, str | None]:
    """
    Incearca sa repare imaginea unui deal.
    Returneaza (deal_id, new_url_or_None).
    """
    deal_id = deal["id"]
    magazin = deal.get("magazin", "")

    # Nivel 1: urllib (rapid, fara Playwright)
    result = fix_via_urllib(deal)
    if result:
        log.debug("  L1 success: %s -> %s", deal_id[:40], result[:60])
        return deal_id, result

    # Nivel 2+3: Playwright response interception + download local
    log.debug("  L1 fail, incerc L2 Playwright: %s", deal_id[:40])
    result = fix_via_playwright(deal)
    return deal_id, result


def fix_all_sequential(deals: list[dict]) -> dict[str, str]:
    """
    Repara toate deal-urile secvential (Playwright nu e thread-safe).
    Returneaza {deal_id: new_url}.
    """
    results: dict[str, str] = {}
    for i, deal in enumerate(deals):
        did, url = fix_one(deal)
        if url:
            results[did] = url
        if (i + 1) % 10 == 0:
            log.info("  Progres: %d/%d (%d fixate)", i + 1, len(deals), len(results))
    return results


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Repara imagini invalide din deals.json (3 niveluri automate)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Nu salva, doar raporteaza")
    parser.add_argument("--store", default="", help="Filtreaza pe un singur magazin")
    parser.add_argument(
        "--workers", type=int, default=1,
        help="Parallelism pentru Nivel 1 urllib (default 1 — Playwright e secvential)"
    )
    args = parser.parse_args()

    data = json.loads(DEALS_PATH.read_text(encoding="utf-8"))
    log.info("Deals totale: %d", len(data))

    bad: list[dict] = []
    for d in data:
        if args.store and d.get("magazin") != args.store:
            continue
        if needs_repair(d):
            bad.append(d)

    if not bad:
        log.info("Toate imaginile sunt OK. Nimic de reparat.")
        return {"fixed": 0, "failed": 0, "total_bad": 0}

    by_store: dict[str, int] = {}
    for d in bad:
        s = d.get("magazin", "necunoscut")
        by_store[s] = by_store.get(s, 0) + 1
    log.info("Imagini de reparat: %d", len(bad))
    for store, cnt in sorted(by_store.items(), key=lambda x: -x[1]):
        log.info("  %s: %d", store, cnt)

    if args.dry_run:
        log.info("[DRY RUN] Nu se modifica nimic.")
        return {"fixed": 0, "failed": len(bad), "total_bad": len(bad)}

    t0 = time.time()
    fixes = fix_all_sequential(bad)
    elapsed = round(time.time() - t0, 1)
    log.info("Terminat in %.1fs — %d/%d fixate", elapsed, len(fixes), len(bad))

    now = datetime.now(timezone.utc).isoformat()
    fixed = 0
    for d in data:
        if d["id"] in fixes:
            new_img = fixes[d["id"]]
            d["imagine_url"] = new_img
            d["image"] = new_img
            d["image_fixed_at"] = now
            d["image_fix_source"] = "image_repair_v2"
            fixed += 1

    failed = len(bad) - fixed
    log.info("Salvat: %d fixate, %d esuate.", fixed, failed)
    DEALS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"fixed": fixed, "failed": failed, "total_bad": len(bad)}


if __name__ == "__main__":
    result = main()
    sys.exit(0)
