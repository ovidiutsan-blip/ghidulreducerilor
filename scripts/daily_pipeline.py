#!/usr/bin/env python3
"""
GhidulReducerilor.ro — Pipeline Zilnic Principal
Orchestrează întregul flux de actualizare: scraping → validare → publicare → distribuție.

Utilizare:
  python scripts/daily_pipeline.py --mode full
  python scripts/daily_pipeline.py --mode cleanup
"""

import json
import os
import sys
import shutil
import logging
import argparse
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('pipeline')

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / 'data'
LOGS_DIR = ROOT / 'logs'
BACKUP_DIR = ROOT / 'data' / 'backups'
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(Path(__file__).parent))
from utils import normalize_deal, is_legit_deal  # noqa: E402


def load_deals() -> list:
    """Încarcă deals.json curent (normalizate EN+RO)."""
    deals_path = DATA_DIR / 'deals.json'
    if deals_path.exists():
        with open(deals_path, 'r', encoding='utf-8') as f:
            return [normalize_deal(d) for d in json.load(f)]
    return []


def save_deals(deals: list):
    """Salvează deals.json actualizat."""
    deals_path = DATA_DIR / 'deals.json'
    with open(deals_path, 'w', encoding='utf-8') as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)
    logger.info(f"Deals salvate: {len(deals)} intrări")


def backup_data():
    """Creează backup zilnic al datelor."""
    timestamp = datetime.now().strftime('%Y-%m-%d')

    for filename in ['deals.json', 'codes.json']:
        src = DATA_DIR / filename
        if src.exists():
            dst = BACKUP_DIR / f"{filename.replace('.json', '')}_{timestamp}.json"
            shutil.copy2(src, dst)
            logger.info(f"Backup creat: {dst.name}")

    # Curăță backup-uri mai vechi de 30 de zile
    cutoff = datetime.now() - timedelta(days=30)
    for backup_file in BACKUP_DIR.glob('*.json'):
        if backup_file.stat().st_mtime < cutoff.timestamp():
            backup_file.unlink()
            logger.info(f"Backup vechi șters: {backup_file.name}")


STALE_DAYS = 14  # deal fără nicio actualizare (scrape/feed/link-check) în N zile => expirat


def _last_touch(deal: dict) -> datetime | None:
    """Cea mai recentă atingere a deal-ului: scraped_at, link_checked_at sau
    data_adaugare. Intenționat FĂRĂ omnibus_checked_at — price_validator îl
    setează zilnic pe toate deal-urile și ar anula regula de prospețime.
    None dacă nu există nicio dată parsabilă."""
    latest = None
    for field in ('scraped_at', 'link_checked_at', 'data_adaugare'):
        raw = deal.get(field)
        if not raw:
            continue
        try:
            dt = datetime.fromisoformat(str(raw).replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if latest is None or dt > latest:
            latest = dt
    return latest


def mark_expired_deals(deals: list) -> tuple[list, int]:
    """
    Marchează ofertele expirate.
    O ofertă este considerată expirată dacă:
    - Are data_expirare în trecut
    - Are is_active = false
    - Sau are mai mult de STALE_DAYS zile fără nicio actualizare
      (prețul nu mai e verificabil => risc Omnibus + utilizatori induși în eroare)
    """
    now = datetime.now(timezone.utc)
    stale_cutoff = now - timedelta(days=STALE_DAYS)
    expired_count = 0
    stale_count = 0
    active_deals = []

    for deal in deals:
        is_expired = False

        # Verifică data expirare explicită
        expiry = deal.get('expiry_date') or deal.get('validUntil')
        if expiry:
            try:
                expiry_dt = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
                if expiry_dt < now:
                    is_expired = True
            except (ValueError, AttributeError):
                pass

        # Verifică is_active flag
        if deal.get('is_active') is False:
            is_expired = True

        # Regula de prospețime: fără nicio actualizare în STALE_DAYS zile => expirat.
        # Feed-urile PS/2P refreshează scraped_at zilnic la produsele încă în ofertă,
        # deci doar deal-urile fără sursă vie ajung aici.
        if not is_expired:
            touch = _last_touch(deal)
            if touch is not None and touch < stale_cutoff:
                is_expired = True
                stale_count += 1

        if is_expired:
            expired_count += 1
            deal['archived_at'] = now.isoformat()
            logger.debug(f"Ofertă expirată: {deal.get('id', 'unknown')}")
        else:
            active_deals.append(deal)

    if stale_count:
        logger.info(f"Oferte stale (> {STALE_DAYS} zile fără actualizare): {stale_count}")

    logger.info(f"Oferte expirate și arhivate: {expired_count}")
    return active_deals, expired_count


def drop_garbage_deals(deals: list) -> list:
    """
    Elimină deals cu preț parsat greșit (ex. placeholder evomag 99 lei / -100%).
    Scraperul le poate re-adăuga corect la următoarea rulare dacă produsul
    există cu preț valid.
    """
    kept = [d for d in deals if is_legit_deal(d)]
    removed = len(deals) - len(kept)
    if removed > 0:
        logger.info(f"Deals garbage eliminate (preț invalid): {removed}")
    return kept


def deduplicate_deals(deals: list) -> list:
    """Elimină oferte duplicate pe baza URL-ului produsului."""
    seen_urls = set()
    unique_deals = []

    for deal in deals:
        url = deal.get('url') or deal.get('product_url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_deals.append(deal)

    removed = len(deals) - len(unique_deals)
    if removed > 0:
        logger.info(f"Duplicate eliminate: {removed}")

    return unique_deals


def sort_deals_by_score(deals: list) -> list:
    """Sortează ofertele după scor (descrescător)."""
    return sorted(deals, key=lambda d: (
        d.get('score', 5),
        d.get('discount_percent', 0)
    ), reverse=True)


def update_sitemap():
    """Sitemap-ul e generat automat de Next.js (app/sitemap.ts) la fiecare deploy.
    Google a retras endpoint-ul de ping (google.com/ping → 404 din iunie 2023);
    indexarea se face prin Search Console + crawl organic al sitemap-ului.
    """
    logger.info("Sitemap generat de Next.js la deploy — nimic de făcut aici.")


def run_full_pipeline():
    """
    Pipeline complet:
    1. Scraping
    2. Validare
    3. Merge cu date existente
    4. Cleanup duplicate + expirate
    5. Sortare
    6. Salvare
    7. Update sitemap
    """
    logger.info("=== PIPELINE FULL START ===")
    stats = {
        'start_time': datetime.now().isoformat(),
        'mode': 'full',
        'deals_inainte': 0,
        'deals_noi': 0,
        'deals_expirate': 0,
        'deals_dupa': 0,
        'erori': []
    }

    # Pas 1: Încarcă date existente
    existing_deals = load_deals()
    stats['deals_inainte'] = len(existing_deals)
    logger.info(f"Deals existente: {len(existing_deals)}")

    # Pas 2: Scraping (apelăm scraper.py)
    new_deals = []
    scrape_start = datetime.now()
    try:
        result = subprocess.run(
            [sys.executable, 'scripts/scraper.py', '--mode', 'full'],
            capture_output=True, text=True, cwd=ROOT, timeout=300
        )
        if result.returncode == 0:
            logger.info("Scraping finalizat cu succes")
            # Încarcă fișierele raw create în această rulare
            raw_dir = DATA_DIR / 'raw'
            if raw_dir.exists():
                for raw_file in sorted(raw_dir.glob('scrape_full_*.json')):
                    if raw_file.stat().st_mtime >= scrape_start.timestamp():
                        try:
                            with open(raw_file, 'r', encoding='utf-8') as f:
                                raw = json.load(f)
                            new_deals.extend([normalize_deal(d) for d in raw])
                            logger.info(f"Încărcat {len(raw)} oferte noi din {raw_file.name}")
                        except Exception as re:
                            logger.error(f"Eroare la citire {raw_file}: {re}")
        else:
            logger.error(f"Eroare scraping: {result.stderr}")
            stats['erori'].append(f"Scraping error: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        logger.error("Scraping timeout după 5 minute")
        stats['erori'].append("Scraping timeout")
    except Exception as e:
        logger.error(f"Eroare la lansare scraper: {e}")

    # Pas 3: Merge date noi cu existente
    all_deals = existing_deals + new_deals
    stats['deals_noi'] = len(new_deals)

    # Pas 4: Cleanup
    all_deals = drop_garbage_deals(all_deals)
    all_deals = deduplicate_deals(all_deals)
    all_deals, expired = mark_expired_deals(all_deals)
    stats['deals_expirate'] = expired

    # Pas 5: Sortare
    all_deals = sort_deals_by_score(all_deals)

    # Pas 6: Salvare
    save_deals(all_deals)
    stats['deals_dupa'] = len(all_deals)

    # Pas 7: Update sitemap
    update_sitemap()

    logger.info(f"=== PIPELINE COMPLET ===")
    logger.info(f"Înainte: {stats['deals_inainte']} | Noi: {stats['deals_noi']} | Expirate: {stats['deals_expirate']} | Final: {stats['deals_dupa']}")

    # Salvează stats
    stats_path = LOGS_DIR / f"pipeline_stats_{datetime.now().strftime('%Y%m%d')}.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)

    return stats


def repair_dead_images(deals: list, max_workers: int = 16) -> list:
    """
    Repară imaginile moarte, pe tot site-ul:
    - ofertele cu imagine_url gol sau care răspunde 404/410 primesc og:image
      de pe pagina produsului (feed-urile 2P livrează uneori URL-uri de
      imagini expirate — ex. casanewconcept și-a mutat imaginile pe ImageKit,
      dar feed-ul trimite în continuare căile vechi, moarte);
    - dacă pagina nu oferă o imagine validă (200 + content-type imagine),
      imagine_url rămâne gol → DealCard randează FallbackImage server-side,
      nu iconița de imagine spartă a browserului (onError pe next/image nu
      prinde erorile dinainte de hidratare).
    Doar 404/410 e considerat definitiv; erorile de rețea și 5xx sunt
    tranzitorii și nu ating URL-ul existent.
    """
    import requests
    from concurrent.futures import ThreadPoolExecutor
    from urllib.parse import urljoin

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'}

    def status_of(url: str):
        """Status HTTP sau None la eroare tranzitorie de rețea."""
        try:
            r = requests.get(url, headers=headers, timeout=10, stream=True)
            r.close()
            return r.status_code
        except Exception:
            return None

    def jsonld_product_images(soup) -> list:
        """URL-urile de imagine din blocurile JSON-LD cu @type Product
        (unele magazine — ex. hotpick/OpenCart — nu au og:image deloc,
        dar publică schema.org Product cu image)."""
        urls = []

        def collect(node):
            if isinstance(node, list):
                for item in node:
                    collect(item)
                return
            if not isinstance(node, dict):
                return
            node_type = node.get('@type')
            if node_type == 'Product' or (isinstance(node_type, list) and 'Product' in node_type):
                img = node.get('image')
                for cand in img if isinstance(img, list) else [img]:
                    if isinstance(cand, dict):
                        cand = cand.get('url') or cand.get('contentUrl')
                    if isinstance(cand, str) and cand.strip():
                        urls.append(cand.strip())
            collect(node.get('@graph'))

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                collect(json.loads(script.string or ''))
            except Exception:
                continue
        return urls

    def og_image(product_url: str) -> str:
        """og:image / twitter:image / link[rel=image_src] / JSON-LD Product
        de pe pagina produsului, doar dacă răspunde 200. Altfel ''. """
        try:
            from bs4 import BeautifulSoup
            r = requests.get(product_url, headers=headers, timeout=15)
            if r.status_code != 200:
                return ''
            soup = BeautifulSoup(r.text, 'html.parser')
            candidates = []
            for el in [
                soup.find('meta', property='og:image'),
                soup.find('meta', attrs={'name': 'twitter:image'}),
                soup.find('link', rel='image_src'),
            ]:
                if el:
                    candidates.append((el.get('content') or el.get('href') or '').strip())
            candidates.extend(jsonld_product_images(soup))
            for cand in candidates:
                if not cand:
                    continue
                cand = urljoin(product_url, cand)
                if status_of(cand) == 200:
                    return cand
            return ''
        except Exception:
            return ''

    def process(d):
        """Returnează (deal, imagine_noua|None). None = nu se schimbă nimic."""
        img = d.get('imagine_url') or ''
        if img.startswith('http'):
            st = status_of(img)
            if st not in (404, 410):
                return (d, None)  # imagine ok sau eroare tranzitorie
        # imagine goală, invalidă sau moartă definitiv → încearcă repararea
        purl = d.get('product_url') or d.get('url') or ''
        new_img = og_image(purl) if purl.startswith('http') else ''
        return (d, new_img)

    with ThreadPoolExecutor(max_workers) as ex:
        results = list(ex.map(process, deals))

    repaired = cleared = 0
    for d, new_img in results:
        if new_img is None:
            continue
        old = d.get('imagine_url') or ''
        if new_img:
            repaired += 1
        elif old:
            cleared += 1
        d['imagine_url'] = new_img
        if 'image_url' in d:
            d['image_url'] = new_img
    if repaired or cleared:
        logger.info(f"Imagini reparate de pe pagina produsului (og:image/JSON-LD): {repaired} | golite (fără înlocuitor): {cleared}")
    return deals


def run_cleanup():
    """
    Cleanup noapte:
    - Backup date
    - Arhivare oferte expirate
    - Reparare imagini moarte (og:image de pe pagina produsului)
    - Curățare logs vechi
    """
    logger.info("=== CLEANUP NOAPTE ===")

    # Backup
    backup_data()

    # Arhivare expirate + eliminare garbage + imagini moarte
    deals = load_deals()
    deals = drop_garbage_deals(deals)
    deals = repair_dead_images(deals)
    active_deals, expired = mark_expired_deals(deals)
    save_deals(active_deals)

    # Curăță log-uri vechi (> 30 zile)
    cutoff = datetime.now() - timedelta(days=30)
    for log_file in LOGS_DIR.glob('*.log'):
        if log_file.stat().st_mtime < cutoff.timestamp():
            log_file.unlink()
            logger.info(f"Log vechi șters: {log_file.name}")

    logger.info(f"Cleanup finalizat. Oferte arhivate: {expired}")


def run_repair_images():
    """Doar repararea imaginilor moarte — rulată în pipeline-ul zilnic imediat
    după importurile de feed-uri, ca deal-urile noi cu URL-uri moarte la sursă
    să nu stea cu iconița spartă pe site toată ziua, până la cleanup-ul de 22:00
    (cazul watch24, 15 iul 2026)."""
    logger.info("=== REPAIR IMAGINI (post-import) ===")
    deals = load_deals()
    deals = repair_dead_images(deals)
    save_deals(deals)


def main():
    parser = argparse.ArgumentParser(description='GhidulReducerilor Daily Pipeline')
    parser.add_argument('--mode', choices=['full', 'cleanup', 'repair-images'], default='full')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    if args.mode == 'full':
        stats = run_full_pipeline()
        print(json.dumps(stats, indent=2))
    elif args.mode == 'cleanup':
        run_cleanup()
    elif args.mode == 'repair-images':
        run_repair_images()


if __name__ == '__main__':
    main()
