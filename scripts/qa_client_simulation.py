#!/usr/bin/env python3
"""
GhidulReducerilor.ro — QA Client Simulation (Playwright)
=========================================================
Simuleaza un utilizator real care navigheaza site-ul si incearca sa cumpere.
Testeaza flow-ul complet: homepage -> deal card -> /out/[id] -> magazin.

Prerequisite:
  pip install playwright
  playwright install chromium

Utilizare:
  python scripts/qa_client_simulation.py
  python scripts/qa_client_simulation.py --base-url http://localhost:3000
  python scripts/qa_client_simulation.py --headed    # Cu browser vizibil

Rulare locala doar — NU in CI cron (prea lent/flaky).
"""

import json
import sys
import argparse
import time
import logging
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("Playwright nu este instalat. Rulati:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)

ROOT = Path(__file__).parent.parent
LOGS_DIR = ROOT / 'logs'
SCREENSHOTS_DIR = LOGS_DIR / 'screenshots'
LOGS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'qa_simulation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('qa_simulation')

DEFAULT_BASE_URL = 'https://ghidulreducerilor.ro'


def run_scenario(playwright, name, url, checks, headed=False):
    """
    Run a single QA scenario.
    Returns dict with pass/fail status and details.
    """
    result = {
        'scenario': name,
        'url': url,
        'timestamp': datetime.now().isoformat(),
        'steps': [],
        'status': 'unknown',
        'issues': [],
    }

    browser = playwright.chromium.launch(headless=not headed)
    context = browser.new_context(
        viewport={'width': 390, 'height': 844},
        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'
    )
    page = context.new_page()

    try:
        # Step 1: Navigate
        logger.info(f"  [{name}] Navigating to {url}")
        start = time.time()
        response = page.goto(url, timeout=15000, wait_until='domcontentloaded')
        load_time = round(time.time() - start, 2)

        status_code = response.status if response else 0
        result['steps'].append({
            'step': 'navigate',
            'status_code': status_code,
            'load_time_s': load_time,
            'ok': status_code == 200
        })

        # 404 is expected for the 404_handling scenario
        if status_code != 200 and status_code != 404:
            result['issues'].append(f"Page returned HTTP {status_code}")
            result['status'] = 'fail'
            return result

        if load_time > 5:
            result['issues'].append(f"Slow page load: {load_time}s")

        # Screenshot
        ss_path = str(SCREENSHOTS_DIR / f'{name}_1_page.png')
        page.screenshot(path=ss_path)

        # Run scenario-specific checks
        for check in checks:
            check_result = check(page, result)
            if check_result:
                result['steps'].append(check_result)

        # Determine final status
        has_critical = any('CRITICAL' in str(i) for i in result['issues'])
        if has_critical:
            result['status'] = 'fail'
        elif result['issues']:
            result['status'] = 'warn'
        else:
            result['status'] = 'pass'

    except PWTimeout:
        result['status'] = 'fail'
        result['issues'].append('CRITICAL: Page timeout (>15s)')
        try:
            page.screenshot(path=str(SCREENSHOTS_DIR / f'{name}_TIMEOUT.png'))
        except Exception:
            pass

    except Exception as e:
        result['status'] = 'fail'
        result['issues'].append(f'CRITICAL: {str(e)[:150]}')
        try:
            page.screenshot(path=str(SCREENSHOTS_DIR / f'{name}_ERROR.png'))
        except Exception:
            pass

    finally:
        browser.close()

    return result


# ═══════════════════════════════════════════════════
# Check Functions
# ═══════════════════════════════════════════════════

def check_deal_cards(page, result):
    """Check that deal cards are visible on the page."""
    cards = page.query_selector_all('[class*="card"], [class*="Card"], [class*="deal"], [class*="Deal"]')
    links = page.query_selector_all('a[href*="/out/"]')

    if not cards and not links:
        result['issues'].append('No deal cards found on page')

    return {
        'step': 'check_deal_cards',
        'cards_found': len(cards),
        'affiliate_links': len(links),
        'ok': len(cards) > 0 or len(links) > 0
    }


def check_affiliate_link_click(page, result):
    """Find and click an affiliate link, verify redirect pattern."""
    # Find any /out/ link
    link = page.query_selector('a[href*="/out/"]')
    if not link:
        result['issues'].append('No /out/ affiliate link found to click')
        return {'step': 'click_affiliate', 'ok': False, 'reason': 'no_link_found'}

    href = link.get_attribute('href') or ''

    # Click and check where it goes
    try:
        # Open in new tab to avoid losing our page
        with page.context.expect_page() as new_page_info:
            link.click()
        new_page = new_page_info.value
        new_page.wait_for_load_state('domcontentloaded', timeout=10000)

        final_url = new_page.url

        # Check if we ended up on a known store domain
        store_domains = [
            'emag.ro', 'fashiondays.ro', 'notino.ro', 'answear.ro',
            'decathlon.ro', 'cel.ro', 'pcgarage.ro', 'vexio.ro',
            'libris.ro', 'catena.ro', 'fornello.ro', 'forit.ro',
            'profitshare.ro', '2performant.com',
        ]
        landed_on_store = any(d in final_url.lower() for d in store_domains)

        if not landed_on_store:
            # Could be a Profitshare/2Performant redirect page — that's OK too
            if 'ghidulreducerilor.ro' in final_url:
                result['issues'].append(f'Affiliate link redirected back to own site: {final_url[:80]}')
            else:
                result['issues'].append(f'Unknown redirect destination: {final_url[:80]}')

        ss_path = str(SCREENSHOTS_DIR / f'{result["scenario"]}_affiliate_target.png')
        new_page.screenshot(path=ss_path)
        new_page.close()

        return {
            'step': 'click_affiliate',
            'href': href[:80],
            'final_url': final_url[:120],
            'landed_on_store': landed_on_store,
            'ok': landed_on_store
        }

    except PWTimeout:
        result['issues'].append('Affiliate link click timed out')
        return {'step': 'click_affiliate', 'ok': False, 'reason': 'timeout'}
    except Exception as e:
        result['issues'].append(f'Error clicking affiliate link: {str(e)[:100]}')
        return {'step': 'click_affiliate', 'ok': False, 'reason': str(e)[:100]}


def check_meta_tags(page, result):
    """Check essential meta tags."""
    title = page.title()
    desc = page.query_selector('meta[name="description"]')
    viewport = page.query_selector('meta[name="viewport"]')

    issues = []
    if not title:
        issues.append('Missing page title')
    if not desc:
        issues.append('Missing meta description')
    if not viewport:
        issues.append('Missing viewport meta (not mobile responsive)')

    result['issues'].extend(issues)

    return {
        'step': 'check_meta',
        'title': title[:60] if title else None,
        'has_description': desc is not None,
        'has_viewport': viewport is not None,
        'ok': len(issues) == 0
    }


def check_404_handling(page, result):
    """Verify 404 page works."""
    # This is run as its own scenario, page is already on the 404 URL
    text = page.text_content('body') or ''
    has_message = any(w in text.lower() for w in ['nu a fost', 'not found', '404', 'pagina nu exista'])

    if not has_message:
        result['issues'].append('404 page does not show an error message')

    return {
        'step': 'check_404',
        'has_error_message': has_message,
        'ok': has_message
    }


def check_store_page_deals(page, result):
    """Check that a store page shows deals for that store."""
    cards = page.query_selector_all('[class*="card"], [class*="Card"], a[href*="/out/"]')
    return {
        'step': 'check_store_deals',
        'deals_found': len(cards),
        'ok': len(cards) > 0
    }


# ═══════════════════════════════════════════════════
# Scenarios
# ═══════════════════════════════════════════════════

def build_scenarios(base_url):
    """Build all test scenarios."""
    return [
        {
            'name': 'homepage_load',
            'url': base_url,
            'checks': [check_meta_tags, check_deal_cards, check_affiliate_link_click]
        },
        {
            'name': 'store_page_emag',
            'url': f'{base_url}/reduceri/emag',
            'checks': [check_store_page_deals]
        },
        {
            'name': 'store_page_fashiondays',
            'url': f'{base_url}/reduceri/fashion-days',
            'checks': [check_store_page_deals]
        },
        {
            'name': 'about_page',
            'url': f'{base_url}/despre',
            'checks': [check_meta_tags]
        },
        {
            'name': 'subscribe_page',
            'url': f'{base_url}/abonare-alerte',
            'checks': [check_meta_tags]
        },
        {
            'name': '404_handling',
            'url': f'{base_url}/pagina-inexistenta-test-qa',
            'checks': [check_404_handling]
        },
    ]


def run_all_scenarios(base_url, headed=False):
    """Run all QA scenarios and return combined report."""
    logger.info("=" * 60)
    logger.info("QA CLIENT SIMULATION — GhidulReducerilor.ro")
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Mode: {'headed' if headed else 'headless'}")
    logger.info("=" * 60)

    scenarios = build_scenarios(base_url)
    results = []

    with sync_playwright() as p:
        for scenario in scenarios:
            logger.info(f"\n--- Scenario: {scenario['name']} ---")
            result = run_scenario(p, scenario['name'], scenario['url'], scenario['checks'], headed)
            results.append(result)

            color = 'green' if result['status'] == 'pass' else 'red'
            logger.info(f"  Status: {result['status']}")
            if result['issues']:
                for issue in result['issues']:
                    logger.info(f"  Issue: {issue}")

    # Summary
    total = len(results)
    passes = sum(1 for r in results if r['status'] == 'pass')
    fails = sum(1 for r in results if r['status'] == 'fail')
    warns = sum(1 for r in results if r['status'] == 'warn')

    report = {
        'timestamp': datetime.now().isoformat(),
        'base_url': base_url,
        'summary': {
            'total': total,
            'pass': passes,
            'fail': fails,
            'warn': warns,
        },
        'scenarios': results
    }

    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    report_path = LOGS_DIR / f'qa_simulation_{timestamp}.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"  QA RESULTS: {passes}/{total} pass, {fails} fail, {warns} warn")
    print(f"{'=' * 50}")
    for r in results:
        status_icon = {'pass': '[PASS]', 'fail': '[FAIL]', 'warn': '[WARN]'}.get(r['status'], '[????]')
        print(f"  {status_icon} {r['scenario']}")
        for issue in r.get('issues', [])[:3]:
            print(f"         {issue}")
    print(f"\n  Report: {report_path}")
    print(f"  Screenshots: {SCREENSHOTS_DIR}")
    print(f"{'=' * 50}")

    return report


def main():
    parser = argparse.ArgumentParser(description='GhidulReducerilor QA Client Simulation')
    parser.add_argument('--base-url', default=DEFAULT_BASE_URL,
                        help=f'Base URL to test (default: {DEFAULT_BASE_URL})')
    parser.add_argument('--headed', action='store_true',
                        help='Run with visible browser window')
    args = parser.parse_args()

    report = run_all_scenarios(args.base_url, headed=args.headed)

    if report['summary']['fail'] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
