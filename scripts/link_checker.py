#!/usr/bin/env python3
"""
GhidulReducerilor.ro — Verificator Universal Linkuri Afiliate
Detectează linkuri moarte pentru ORICE rețea de afiliere și ORICE magazin,
existent sau viitor: 2Performant, Profitshare, direct links, etc.

Strategii de detecție (în ordine):
  1. HTTP status  — 404/410 = mort sigur
  2. Redirect spre rețea de afiliere (produs = 200 dar rămas pe platforma afiliere = expirat)
  3. Redirect spre homepage (URL final = rădăcina domeniului, fără path produs)
  4. Body content — fraze de tip "pagina nu exista" / "product not found" (RO + EN)
  5. Patterns specifice per rețea (2Performant notoolerror, etc.)

Utilizare:
  python scripts/link_checker.py --mode full          # verifică toate deal-urile active
  python scripts/link_checker.py --mode quick         # max 50, nevericifate niciodată
  python scripts/link_checker.py --mode full --remove-dead  # verifică + șterge din deals.json
  python scripts/link_checker.py --deal-id emag-abc  # un deal specific
"""

import json
import sys
import time
import logging
import argparse
import concurrent.futures
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("Instalează requests: pip install requests")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/link_checker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('link_checker')

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / 'data'
LOGS_DIR = ROOT / 'logs'

sys.path.insert(0, str(Path(__file__).parent))
from utils import normalize_deal  # noqa: E402

REQUEST_TIMEOUT = 15
MAX_WORKERS = 8
RETRY_COUNT = 1

# ─── Patterns specifice per rețea de afiliere ────────────────────────────────
# Adaugă rețele noi aici fără să modifici altceva în cod.
AFFILIATE_NETWORK_DEAD_PATTERNS = {
    '2performant': {
        'url_contains': ['notoolerror', 'businessleague.2performant.com'],
        'stayed_on_network': True,   # dacă URL final e tot pe domeniul rețelei = expirat
        'network_domains': ['2performant.com', 'businessleague.2performant.com'],
    },
    'profitshare': {
        'url_contains': [],
        'stayed_on_network': True,   # dacă URL final e tot pe profitshare = expirat
        'network_domains': ['profitshare.ro'],
    },
}

# ─── Fraze "produs indisponibil" — RO + EN ───────────────────────────────────
# Acoperă orice magazin, orice limbă. Extinde lista pentru magazine noi.
DEAD_CONTENT_PHRASES = [
    # Română
    'produsul nu mai este disponibil',
    'produs indisponibil',
    'produsul nu este disponibil',
    'pagina nu a fost gasita',
    'pagina nu exista',
    'aceasta pagina nu exista',
    'produsul nu exista',
    'nu am gasit pagina',
    'eroare 404',
    'produsul a fost retras',
    'stoc epuizat',           # opțional — comentează dacă prea agresiv
    # Engleză
    'page not found',
    'product not found',
    'this page does not exist',
    "we couldn't find this page",
    "page doesn't exist",
    'link expired',
    'link no longer available',
    'houston, we have a problem',  # 2Performant Business League
    'item not found',
    'product is no longer available',
    '404 - not found',
    'the page you requested was not found',
]

# ─── Detectoare rețele de afiliere ───────────────────────────────────────────

def _detect_affiliate_network(url: str) -> Optional[str]:
    """Identifică rețeaua de afiliere din URL."""
    url_lower = url.lower()
    if '2performant.com' in url_lower or 'evt.4ps.ro' in url_lower:
        return '2performant'
    if 'profitshare.ro' in url_lower:
        return 'profitshare'
    return None  # link direct spre magazin


def _is_homepage_redirect(original_url: str, final_url: str) -> bool:
    """
    Detectează redirect spre homepage — semn că produsul nu mai există.
    Ex: https://emag.ro/produs-xyz → https://emag.ro/
    """
    try:
        orig = urlparse(original_url)
        final = urlparse(final_url)

        # Același domeniu, dar path-ul final e root
        same_domain = orig.netloc.replace('www.', '') == final.netloc.replace('www.', '')
        final_is_root = final.path in ('', '/', '/ro/', '/ro', '/home')

        if same_domain and final_is_root and orig.path not in ('', '/'):
            return True

        # Domain diferit și path root — probabil redirect spre homepage magazin
        if not same_domain and final_is_root:
            return True

    except Exception:
        pass
    return False


def _check_network_expired(original_url: str, final_url: str, network: str) -> bool:
    """
    Verifică dacă un link de rețea de afiliere a expirat.
    Strategii:
      - URL final conține pattern specific rețelei (ex: notoolerror)
      - URL final a rămas pe domeniul rețelei (produs nu a existat/expirat)
    """
    config = AFFILIATE_NETWORK_DEAD_PATTERNS.get(network, {})
    final_lower = final_url.lower()

    # Pattern-uri specifice în URL final
    for pattern in config.get('url_contains', []):
        if pattern in final_lower:
            return True

    # "Stayed on network" — URL final e tot pe platforma de afiliere = produs expirat
    if config.get('stayed_on_network'):
        for domain in config.get('network_domains', []):
            if domain in final_lower:
                return True

    return False


def _check_body_content(body: str) -> Optional[str]:
    """Caută fraze de 'produs indisponibil' în body-ul paginii."""
    body_lower = body.lower()
    for phrase in DEAD_CONTENT_PHRASES:
        if phrase in body_lower:
            return phrase
    return None

# ─── Checker principal ────────────────────────────────────────────────────────

def create_session() -> requests.Session:
    """Creează sesiune requests cu retry logic (fără retry pe 429)."""
    session = requests.Session()
    retry_strategy = Retry(
        total=RETRY_COUNT,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],  # NU 429 — nu are rost să insistăm
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      'Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,*/*;q=0.9',
        'Accept-Language': 'ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7',
    })
    return session


def check_link(session: requests.Session, deal: dict) -> dict:
    """
    Verifică un singur link afiliat cu toate strategiile de detecție.
    Returnează dict cu status, final_url, motiv.
    """
    link = deal.get('affiliate_url') or deal.get('link_afiliat') or deal.get('url', '')
    deal_id = deal.get('id', 'unknown')
    network = _detect_affiliate_network(link)

    result = {
        'id': deal_id,
        'url': link,
        'network': network or 'direct',
        'status': 'unknown',
        'status_code': None,
        'final_url': None,
        'dead_reason': None,
        'response_time_ms': None,
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'error': None,
    }

    if not link or link == '#':
        result['status'] = 'no_url'
        return result

    start_time = time.time()

    try:
        response = session.get(link, timeout=REQUEST_TIMEOUT, allow_redirects=True)

        elapsed_ms = round((time.time() - start_time) * 1000)
        result['response_time_ms'] = elapsed_ms
        result['status_code'] = response.status_code
        result['final_url'] = response.url

        # ── Strategie 1: HTTP status clar ────────────────────────────────────
        if response.status_code in (404, 410):
            result['status'] = 'dead'
            result['dead_reason'] = f'http_{response.status_code}'
            logger.warning(f"[DEAD-{response.status_code}] {deal_id}")
            return result

        if response.status_code >= 500:
            result['status'] = 'server_error'
            return result

        if response.status_code == 429:
            result['status'] = 'rate_limited'
            return result

        if response.status_code != 200:
            result['status'] = f'http_{response.status_code}'
            return result

        # ── Strategie 2: Pattern specific rețea de afiliere ──────────────────
        if network and _check_network_expired(link, response.url, network):
            result['status'] = 'dead'
            result['dead_reason'] = f'{network}_expired'
            logger.warning(f"[DEAD-{network.upper()}] {deal_id} → {response.url}")
            return result

        # ── Strategie 3: Redirect spre homepage ───────────────────────────────
        if _is_homepage_redirect(link, response.url):
            result['status'] = 'dead'
            result['dead_reason'] = 'redirect_to_homepage'
            logger.warning(f"[DEAD-HOMEPAGE] {deal_id}: {link} → {response.url}")
            return result

        # ── Strategie 4: Body content — fraze de produs indisponibil ─────────
        try:
            body = response.text[:8000]
            dead_phrase = _check_body_content(body)
            if dead_phrase:
                result['status'] = 'dead'
                result['dead_reason'] = f'body_phrase:{dead_phrase[:40]}'
                logger.warning(f"[DEAD-CONTENT] {deal_id}: '{dead_phrase[:40]}'")
                return result
        except Exception:
            pass  # body parse failure = nu blocăm

        # ── Toate verificările OK ─────────────────────────────────────────────
        result['status'] = 'ok'
        logger.debug(f"[OK] {deal_id} ({elapsed_ms}ms)")

    except requests.exceptions.Timeout:
        result['status'] = 'timeout'
        result['error'] = 'Request timeout'
    except requests.exceptions.ConnectionError as e:
        result['status'] = 'connection_error'
        result['error'] = str(e)[:100]
    except requests.exceptions.TooManyRedirects:
        result['status'] = 'dead'
        result['dead_reason'] = 'too_many_redirects'
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)[:100]

    return result

# ─── Update status deal ───────────────────────────────────────────────────────

def update_deal_link_status(deal: dict, check_result: dict) -> dict:
    """Actualizează statusul link-ului în obiectul deal."""
    deal['link_status'] = check_result['status']
    deal['link_checked_at'] = check_result['checked_at']

    if check_result.get('dead_reason'):
        deal['link_dead_reason'] = check_result['dead_reason']

    if check_result['status'] == 'dead':
        deal['is_active'] = False
        deal['activ'] = False
        deal['link_dead_count'] = deal.get('link_dead_count', 0) + 1
        logger.warning(
            f"Deal marcat inactiv: {deal.get('id')} — {check_result.get('dead_reason', 'unknown')}"
        )

    elif check_result['status'] == 'timeout':
        deal['link_timeout_count'] = deal.get('link_timeout_count', 0) + 1
        if deal.get('link_timeout_count', 0) >= 3:
            deal['is_active'] = False
            deal['activ'] = False
            logger.warning(f"Deal dezactivat după 3 timeout-uri: {deal.get('id')}")

    elif check_result['status'] == 'ok':
        # Reset contoare dacă link-ul e din nou ok
        deal['link_dead_count'] = 0
        deal['link_timeout_count'] = 0
        deal.pop('link_dead_reason', None)

    return deal

# ─── Runner principal ─────────────────────────────────────────────────────────

def load_deals() -> list:
    deals_path = DATA_DIR / 'deals.json'
    if deals_path.exists():
        with open(deals_path, 'r', encoding='utf-8') as f:
            return [normalize_deal(d) for d in json.load(f)]
    return []


def save_deals(deals: list):
    deals_path = DATA_DIR / 'deals.json'
    with open(deals_path, 'w', encoding='utf-8') as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)


def run_checks(
    deals: list,
    mode: str = 'full',
    deal_id: Optional[str] = None,
    remove_dead: bool = False,
) -> tuple[dict, list]:
    """
    Rulează verificările de linkuri.
    remove_dead=True → șterge fizic din deals lista deal-urile confirmate moarte.
    """
    if deal_id:
        deals_to_check = [d for d in deals if d.get('id') == deal_id]
    elif mode == 'quick':
        deals_to_check = [
            d for d in deals
            if d.get('is_active', True) and not d.get('link_checked_at')
        ][:50]
    else:
        deals_to_check = [d for d in deals if d.get('is_active', True)]

    logger.info(f"Verificare {len(deals_to_check)} linkuri (mod: {mode}, remove_dead: {remove_dead})")

    if not deals_to_check:
        logger.info("Nu există linkuri de verificat")
        return {'total': 0, 'ok': 0, 'dead': 0, 'dead_deals': []}, deals

    session = create_session()
    results = []
    dead_deals = []
    ok_count = 0
    rate_limited_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_deal = {
            executor.submit(check_link, session, deal): deal
            for deal in deals_to_check
        }

        for future in concurrent.futures.as_completed(future_to_deal):
            deal = future_to_deal[future]
            try:
                result = future.result()
                results.append(result)

                if result['status'] == 'ok':
                    ok_count += 1
                elif result['status'] == 'dead':
                    dead_deals.append({
                        'id': deal.get('id'),
                        'magazin': deal.get('magazin', deal.get('store', '?')),
                        'title': deal.get('titlu', deal.get('title', '')),
                        'url': result['url'],
                        'final_url': result.get('final_url', ''),
                        'dead_reason': result.get('dead_reason', ''),
                        'network': result.get('network', 'direct'),
                    })
                elif result['status'] == 'rate_limited':
                    rate_limited_count += 1

            except Exception as e:
                logger.error(f"Eroare la verificare {deal.get('id')}: {e}")

    # Actualizează statusul în deals
    results_by_id = {r['id']: r for r in results}
    for i, deal in enumerate(deals):
        if deal.get('id') in results_by_id:
            deals[i] = update_deal_link_status(deal, results_by_id[deal['id']])

    # Auto-remove deal-uri moarte dacă e cerut
    removed_count = 0
    if remove_dead and dead_deals:
        dead_ids = {d['id'] for d in dead_deals}
        before = len(deals)
        deals = [d for d in deals if d.get('id') not in dead_ids]
        removed_count = before - len(deals)
        logger.info(f"Auto-remove: {removed_count} deal-uri moarte șterse din deals.json")

    stats = {
        'total_checked': len(deals_to_check),
        'ok': ok_count,
        'dead': len(dead_deals),
        'rate_limited': rate_limited_count,
        'removed': removed_count,
        'dead_deals': dead_deals,
        'checked_at': datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        f"Verificare completă: {ok_count} OK | {len(dead_deals)} moarte"
        f" | {rate_limited_count} rate-limited | {removed_count} șterse"
    )

    return stats, deals


def save_report(stats: dict):
    report_path = LOGS_DIR / f"link_check_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    logger.info(f"Raport salvat: {report_path}")

# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='GhidulReducerilor — Link Checker Universal',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemple:
  python scripts/link_checker.py --mode full
  python scripts/link_checker.py --mode full --remove-dead
  python scripts/link_checker.py --deal-id emag-abc12345
        """
    )
    parser.add_argument('--mode', choices=['full', 'quick'], default='quick',
                        help='full=toate deal-urile active, quick=max 50 neverificate')
    parser.add_argument('--deal-id', help='Verifică doar un deal specific')
    parser.add_argument('--remove-dead', action='store_true',
                        help='Șterge automat din deals.json deal-urile confirmate moarte')
    parser.add_argument('--dry-run', action='store_true',
                        help='Verifică dar nu salvează nimic pe disc')
    args = parser.parse_args()

    logger.info(f"=== Link Checker Universal — mod: {args.mode} | remove-dead: {args.remove_dead} ===")

    deals = load_deals()
    stats, updated_deals = run_checks(
        deals,
        mode=args.mode,
        deal_id=args.deal_id,
        remove_dead=args.remove_dead and not args.dry_run,
    )

    save_report(stats)

    if not args.dry_run:
        save_deals(updated_deals)
        logger.info("deals.json actualizat")

    # Raport final
    print(f"\n=== RAPORT LINK CHECKER ===")
    print(f"Total verificate : {stats.get('total_checked', 0)}")
    print(f"✅ OK            : {stats.get('ok', 0)}")
    print(f"❌ Moarte        : {stats.get('dead', 0)}")
    print(f"⏱️  Rate-limited  : {stats.get('rate_limited', 0)}")
    if args.remove_dead:
        print(f"🗑️  Șterse        : {stats.get('removed', 0)}")

    if stats.get('dead_deals'):
        print(f"\nDeal-uri moarte ({len(stats['dead_deals'])}):")
        for d in stats['dead_deals']:
            print(f"  [{d['magazin']}] {d['title'][:45]} — {d['dead_reason']} ({d['network']})")

    return stats


if __name__ == '__main__':
    main()
