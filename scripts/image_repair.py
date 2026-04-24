#!/usr/bin/env python3
"""
image_repair.py — Reparare automata imagini lipsa/invalide din deals.json
=========================================================================
Detecteaza produse cu imagine_url invalida (placeholder, GIF, CDN blocat, lipsa)
si incarca imaginea reala via OG scraping de pe pagina produsului.

Strategii:
  - urllib (default): fast, pentru magazine fara protectie CloudFlare
  - Playwright (fallback): pentru magazine cu CloudFlare WAF (mathaus, etc.)

Ruleaza dupa ps_feed_to_deals.py si agent_altemagazine.py in pipeline-ul zilnic.

Utilizare:
  python scripts/image_repair.py                  # fix all, salveaza
  python scripts/image_repair.py --dry-run         # raporteaza fara a salva
  python scripts/image_repair.py --store mathaus   # doar un magazin
  python scripts/image_repair.py --workers 4       # controleaza paralelismul
"""
import sys
import json
import time
import re
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
}

# Referer per magazin — necesar pentru CDN-uri cu hotlink protection
STORE_REFERER = {
    "mathaus": "https://www.mathaus.ro/",
    "vegis": "https://www.vegis.ro/",
    "hiris": "https://www.hiris.ro/",
    "novodoors": "https://www.novodoors.ro/",
    "casesmart": "https://www.casesmart.ro/",
    "case-smart": "https://www.casesmart.ro/",
}

# Placeholder patterns cunoscute
BAD_PATTERNS = ("lazy-loader", "/layout/", "placeholder", "no-image", "noimage", "nopicture")

# CDN-uri care blocheaza hotlinking (trebuie re-scraped mereu)
BLOCKED_CDN = ("cdn.mathaus.ro",)

# Magazine cu CloudFlare WAF — necesita Playwright in loc de urllib
CLOUDFLARE_STORES = {"mathaus"}

OG_RE = re.compile(
    r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']'
    r'|<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
    re.I,
)


# ─── Utilitare ───────────────────────────────────────────────────────────────

def is_bad_image(url: str | None) -> bool:
    """True daca url este un placeholder sau invalid."""
    if not url or not url.startswith("http"):
        return True
    u = url.lower()
    if u.endswith(".gif"):
        return True
    return any(p in u for p in BAD_PATTERNS)


def is_blocked_cdn(url: str | None) -> bool:
    """True daca url provine dintr-un CDN cu hotlink protection."""
    if not url:
        return False
    return any(h in url for h in BLOCKED_CDN)


def needs_repair(deal: dict) -> bool:
    img = deal.get("imagine_url") or ""
    return is_bad_image(img) or is_blocked_cdn(img)


def fetch_og_image(product_url: str, referer: str = "") -> str | None:
    """Fetch og:image de pe pagina produsului via urllib. Returneaza URL sau None."""
    if not product_url or not product_url.startswith("http"):
        return None
    try:
        headers = dict(HEADERS)
        if referer:
            headers["Referer"] = referer
        req = urllib.request.Request(product_url, headers=headers)
        with urllib.request.urlopen(req, timeout=14) as resp:
            html = resp.read(80_000).decode("utf-8", errors="ignore")
        m = OG_RE.search(html)
        if m:
            img = (m.group(1) or m.group(2) or "").strip()
            if img and img.startswith("http") and not is_bad_image(img):
                return img
        return None
    except Exception:
        return None


def fetch_og_image_playwright(product_url: str) -> str | None:
    """Fetch og:image via Playwright headless Chromium — bypass CloudFlare WAF.
    Folosit pentru magazine cu protectie CF (mathaus, etc.).
    Returneaza URL sau None daca Playwright nu e instalat sau fetch esueaza.
    """
    if not product_url or not product_url.startswith("http"):
        return None
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        log.warning("Playwright nu e instalat — fallback la urllib pentru %s", product_url)
        return fetch_og_image(product_url)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            ctx = browser.new_context(
                user_agent=HEADERS["User-Agent"],
                viewport={"width": 1280, "height": 800},
                locale="ro-RO",
            )
            page = ctx.new_page()
            # Blocheaza resurse inutile pentru viteza
            page.route("**/*.{woff,woff2,ttf,mp4,svg,ico}", lambda r: r.abort())
            try:
                page.goto(product_url, timeout=25000, wait_until="domcontentloaded")
                page.wait_for_timeout(1500)  # CF challenge poate dura ~1s
            except PWTimeout:
                browser.close()
                return None
            html = page.content()
            browser.close()
        m = OG_RE.search(html)
        if m:
            img = (m.group(1) or m.group(2) or "").strip()
            if img and img.startswith("http") and not is_bad_image(img):
                return img
        return None
    except Exception as e:
        log.debug("Playwright error pentru %s: %s", product_url, e)
        return None


# ─── Core ────────────────────────────────────────────────────────────────────

def _fix_one(deal: dict) -> tuple[str, str | None]:
    product_url = (
        deal.get("product_url")
        or deal.get("link_afiliat")
        or deal.get("url")
        or ""
    )
    magazin = deal.get("magazin", "")
    if magazin in CLOUDFLARE_STORES:
        # Magazine cu CloudFlare WAF necesita Playwright
        img = fetch_og_image_playwright(product_url)
    else:
        referer = STORE_REFERER.get(magazin, "")
        img = fetch_og_image(product_url, referer=referer)
    return deal["id"], img


def fix_batch(deals: list[dict], workers: int = 8) -> dict[str, str]:
    """Repara toate deal-urile in paralel. Returneaza {deal_id: new_url}.
    Magazine CloudFlare (Playwright) sunt procesate cu max 3 workers simultan
    pentru a evita detectia bot si a reduce incarcarea browserelor headless.
    """
    results: dict[str, str] = {}
    # Separa deals CF de cele normale
    cf_deals = [d for d in deals if d.get("magazin", "") in CLOUDFLARE_STORES]
    normal_deals = [d for d in deals if d.get("magazin", "") not in CLOUDFLARE_STORES]

    def _process_batch(batch, max_w):
        with ThreadPoolExecutor(max_workers=max_w) as ex:
            futures = {ex.submit(_fix_one, d): d["id"] for d in batch}
            done = 0
            for fut in as_completed(futures):
                did, img = fut.result()
                done += 1
                if img:
                    results[did] = img
                if done % 10 == 0:
                    log.info(f"  Progres: {done}/{len(batch)} ({len(results)} fixate)")

    if normal_deals:
        log.info(f"  urllib: {len(normal_deals)} produse cu {workers} workers")
        _process_batch(normal_deals, workers)

    if cf_deals:
        cf_workers = min(3, workers)  # max 3 browsere Playwright simultan
        log.info(f"  Playwright (CloudFlare): {len(cf_deals)} produse cu {cf_workers} workers")
        _process_batch(cf_deals, cf_workers)

    return results


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Repara imagini invalide din deals.json")
    parser.add_argument("--dry-run", action="store_true", help="Nu salva, doar raporteaza")
    parser.add_argument("--store", default="", help="Filtreaza pe un singur magazin")
    parser.add_argument("--workers", type=int, default=8, help="Nr. fire paralele (default 8)")
    args = parser.parse_args()

    data = json.loads(DEALS_PATH.read_text(encoding="utf-8"))
    log.info(f"Deals totale: {len(data)}")

    # Detecteaza deals cu imagini invalide
    bad: list[dict] = []
    for d in data:
        if args.store and d.get("magazin") != args.store:
            continue
        if needs_repair(d):
            bad.append(d)

    if not bad:
        log.info("Toate imaginile sunt OK. Nimic de reparat.")
        return {"fixed": 0, "failed": 0, "total_bad": 0}

    # Sumar pe magazin
    by_store: dict[str, int] = {}
    for d in bad:
        s = d.get("magazin", "necunoscut")
        by_store[s] = by_store.get(s, 0) + 1
    log.info(f"Imagini invalide: {len(bad)}")
    for store, cnt in sorted(by_store.items(), key=lambda x: -x[1]):
        log.info(f"  {store}: {cnt}")

    if args.dry_run:
        log.info("[DRY RUN] Nu se modifica nimic.")
        return {"fixed": 0, "failed": len(bad), "total_bad": len(bad)}

    # Repara in paralel
    log.info(f"Reparare cu {args.workers} workers...")
    t0 = time.time()
    fixes = fix_batch(bad, workers=args.workers)
    elapsed = round(time.time() - t0, 1)
    log.info(f"Terminat in {elapsed}s — {len(fixes)}/{len(bad)} fixate")

    # Aplica fix-urile in data
    now = datetime.now(timezone.utc).isoformat()
    fixed = 0
    for d in data:
        if d["id"] in fixes:
            new_img = fixes[d["id"]]
            d["imagine_url"] = new_img
            d["image"] = new_img
            d["image_fixed_at"] = now
            d["image_fix_source"] = "image_repair"
            fixed += 1

    failed = len(bad) - fixed
    log.info(f"Salvat: {fixed} fixate, {failed} esuate.")

    DEALS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"fixed": fixed, "failed": failed, "total_bad": len(bad)}


if __name__ == "__main__":
    result = main()
    sys.exit(0)
