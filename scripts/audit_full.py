#!/usr/bin/env python3
"""
GhidulReducerilor.ro — Audit Complet al Site-ului
==================================================
Verificari:
  1. Homepage health (status, response time, content markers)
  2. Affiliate link audit (reuse link_checker + flag direct Profitshare links)
  3. Store coverage (cross-reference magazines.json vs deals)
  4. Image audit (Unsplash/placeholder detection)
  5. Data quality (missing prices, duplicates, expired deals)
  6. Security headers (HSTS, CSP, X-Content-Type-Options)
  7. Page accessibility (all site pages respond 200)

Utilizare:
  python scripts/audit_full.py
  python scripts/audit_full.py --skip-links     # Skip link checking (faster)
  python scripts/audit_full.py --output json     # JSON only, no markdown update

Reuse: link_checker.py, utils.py, monitor_agent.py
"""

import json
import os
import sys
import time
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Setup paths
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'agents'))

from utils import normalize_deal, is_profitshare_direct  # noqa: E402
from link_checker import create_session, load_deals, check_link, check_profitshare_link  # noqa: E402

try:
    from monitor_agent import check_site_pages  # noqa: E402
except ImportError:
    check_site_pages = None

DATA_DIR = ROOT / 'data'
CONFIG_DIR = ROOT / 'config'
LOGS_DIR = ROOT / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'audit_full.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('audit_full')

SITE_URL = os.getenv('SITE_URL', 'https://ghidulreducerilor.ro')


def load_magazines() -> dict:
    """Load store config from magazines.json."""
    path = CONFIG_DIR / 'magazines.json'
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f).get('magazines', {})
    return {}


def load_codes() -> list:
    """Load promo codes."""
    path = DATA_DIR / 'codes.json'
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


# ═══════════════════════════════════════════════════
# CHECK 1: Homepage Health
# ═══════════════════════════════════════════════════

def audit_homepage(session) -> dict:
    """Check homepage loads correctly with expected content."""
    logger.info("=== CHECK 1: Homepage Health ===")
    result = {
        'check': 'homepage',
        'status': 'unknown',
        'issues': [],
        'details': {}
    }

    try:
        start = time.time()
        resp = session.get(SITE_URL, timeout=15)
        elapsed_ms = round((time.time() - start) * 1000)

        result['details']['status_code'] = resp.status_code
        result['details']['response_time_ms'] = elapsed_ms
        result['details']['content_length'] = len(resp.text)

        if resp.status_code != 200:
            result['issues'].append(f"Homepage returned HTTP {resp.status_code}")
            result['status'] = 'fail'
            return result

        if elapsed_ms > 5000:
            result['issues'].append(f"Homepage slow: {elapsed_ms}ms (>5s)")
        elif elapsed_ms > 3000:
            result['issues'].append(f"Homepage somewhat slow: {elapsed_ms}ms (>3s)")

        html = resp.text.lower()

        # Check for deal cards
        if 'reducere' not in html and 'ofert' not in html and 'deal' not in html:
            result['issues'].append("No deal/offer content found on homepage")

        # Check meta tags
        if '<meta name="description"' not in html and '<meta property="og:description"' not in html:
            result['issues'].append("Missing meta description")
        if '<meta name="viewport"' not in html:
            result['issues'].append("Missing viewport meta tag (not responsive)")

        result['status'] = 'pass' if not result['issues'] else 'warn'

    except Exception as e:
        result['status'] = 'fail'
        result['issues'].append(f"Homepage unreachable: {str(e)[:100]}")

    logger.info(f"  Homepage: {result['status']} ({len(result['issues'])} issues)")
    return result


# ═══════════════════════════════════════════════════
# CHECK 2: Affiliate Link Audit
# ═══════════════════════════════════════════════════

def audit_affiliate_links(deals: list, session) -> dict:
    """Check all affiliate links for health and tracking."""
    logger.info("=== CHECK 2: Affiliate Link Audit ===")
    result = {
        'check': 'affiliate_links',
        'status': 'unknown',
        'issues': [],
        'details': {
            'total_deals': len(deals),
            'active_deals': 0,
            'links_ok': 0,
            'links_broken': 0,
            'links_timeout': 0,
            'links_no_url': 0,
            'direct_profitshare': 0,
            'broken_list': []
        }
    }

    active_deals = [d for d in deals if d.get('is_active', True) or d.get('activ', True)]
    result['details']['active_deals'] = len(active_deals)

    for deal in active_deals:
        link = deal.get('affiliate_url') or deal.get('link_afiliat', '')
        deal_id = deal.get('id', 'unknown')

        # Check for direct Profitshare links (blocked on mobile)
        if is_profitshare_direct(link):
            result['details']['direct_profitshare'] += 1
            result['issues'].append(
                f"Direct Profitshare link (blocked on mobile): {deal_id} -> {link[:60]}"
            )

        # Check link health
        check = check_link(session, deal)

        if check['status'] == 'ok':
            result['details']['links_ok'] += 1
        elif check['status'] == 'no_url':
            result['details']['links_no_url'] += 1
            result['issues'].append(f"No affiliate URL: {deal_id}")
        elif check['status'] == 'timeout':
            result['details']['links_timeout'] += 1
        else:
            result['details']['links_broken'] += 1
            result['details']['broken_list'].append({
                'id': deal_id,
                'url': link[:80],
                'status': check['status'],
                'store': deal.get('store') or deal.get('magazin', '')
            })

    broken = result['details']['links_broken']
    no_url = result['details']['links_no_url']
    direct_ps = result['details']['direct_profitshare']

    if broken > 0 or no_url > 0:
        result['status'] = 'fail'
    elif direct_ps > 0:
        result['status'] = 'warn'
    else:
        result['status'] = 'pass'

    logger.info(
        f"  Links: {result['details']['links_ok']} OK, "
        f"{broken} broken, {result['details']['links_timeout']} timeout, "
        f"{direct_ps} direct Profitshare"
    )
    return result


# ═══════════════════════════════════════════════════
# CHECK 3: Store Coverage
# ═══════════════════════════════════════════════════

def audit_store_coverage(deals: list, magazines: dict) -> dict:
    """Cross-reference magazines.json with actual deals."""
    logger.info("=== CHECK 3: Store Coverage ===")
    result = {
        'check': 'store_coverage',
        'status': 'unknown',
        'issues': [],
        'details': {
            'configured_stores': len(magazines),
            'stores_with_deals': 0,
            'stores_no_deals': [],
            'pending_stores': [],
            'store_deal_counts': {}
        }
    }

    # Count deals per store
    deal_counts: dict[str, int] = {}
    for deal in deals:
        store = deal.get('store') or deal.get('magazin', '')
        if store:
            deal_counts[store] = deal_counts.get(store, 0) + 1

    result['details']['store_deal_counts'] = deal_counts
    result['details']['stores_with_deals'] = len(deal_counts)

    for slug, config in magazines.items():
        status = config.get('status', '')

        if status == 'activ':
            # Active store should have deals
            if slug not in deal_counts and config.get('name', slug) not in deal_counts:
                result['details']['stores_no_deals'].append(slug)
                result['issues'].append(
                    f"Active store '{config.get('name', slug)}' has 0 deals"
                )

        elif status == 'pending_approval':
            result['details']['pending_stores'].append({
                'slug': slug,
                'name': config.get('name', slug),
                'network': config.get('affiliate_network', ''),
                'applied': config.get('data_aplicare', 'unknown')
            })

    if result['details']['stores_no_deals']:
        result['status'] = 'warn'
    else:
        result['status'] = 'pass'

    logger.info(
        f"  Stores: {result['details']['stores_with_deals']} with deals, "
        f"{len(result['details']['stores_no_deals'])} empty, "
        f"{len(result['details']['pending_stores'])} pending"
    )
    return result


# ═══════════════════════════════════════════════════
# CHECK 4: Image Audit
# ═══════════════════════════════════════════════════

def audit_images(deals: list) -> dict:
    """Detect placeholder images (Unsplash, via.placeholder.com)."""
    logger.info("=== CHECK 4: Image Audit ===")
    result = {
        'check': 'images',
        'status': 'unknown',
        'issues': [],
        'details': {
            'total_deals': len(deals),
            'placeholder_count': 0,
            'missing_count': 0,
            'real_count': 0,
            'placeholder_domains': {}
        }
    }

    # Generic placeholder hosts + CDN-side lazy-load placeholders
    placeholder_patterns = [
        'unsplash.com', 'placeholder.com', 'placehold.co', 'placekitten.com',
        'lazy-loader', 'lazy_loader', 'lazyload', '/loader.gif', 'no-image', 'noimage',
        'coming-soon', 'default.jpg', 'default.png'
    ]

    for deal in deals:
        img = deal.get('image') or deal.get('imagine_url', '')

        if not img:
            result['details']['missing_count'] += 1
            continue

        is_placeholder = any(p in img.lower() for p in placeholder_patterns)
        if is_placeholder:
            result['details']['placeholder_count'] += 1
            for p in placeholder_patterns:
                if p in img.lower():
                    result['details']['placeholder_domains'][p] = \
                        result['details']['placeholder_domains'].get(p, 0) + 1
        else:
            result['details']['real_count'] += 1

    total = len(deals)
    placeholders = result['details']['placeholder_count']
    missing = result['details']['missing_count']

    if total > 0 and placeholders / total > 0.5:
        result['issues'].append(
            f"{placeholders}/{total} deals ({round(placeholders/total*100)}%) use placeholder images"
        )
        result['status'] = 'fail'
    elif placeholders > 0:
        result['issues'].append(f"{placeholders} deals still use placeholder images")
        result['status'] = 'warn'
    else:
        result['status'] = 'pass'

    if missing > 0:
        result['issues'].append(f"{missing} deals have no image at all")

    logger.info(
        f"  Images: {result['details']['real_count']} real, "
        f"{placeholders} placeholder, {missing} missing"
    )
    return result


# ============================================================
# CHECK 4b: Image Hosts Whitelist (Next/Image)
# ============================================================
def audit_image_hosts(deals: list) -> dict:
    """Verify every image host is in next.config.js remotePatterns, else Next/Image returns 400."""
    import re as _re
    logger.info("=== CHECK 4b: Image Hosts Whitelist ===")
    result = {
        'check': 'image_hosts',
        'status': 'pass',
        'issues': [],
        'details': {'hosts': {}, 'blocked': []}
    }

    # Parse whitelist from next.config.js
    cfg_path = ROOT / 'next.config.js'
    whitelist = []
    if cfg_path.exists():
        text = cfg_path.read_text(encoding='utf-8')
        whitelist = _re.findall(r"hostname:\s*['\"]([^'\"]+)['\"]", text)

    def matches(host: str) -> bool:
        for pat in whitelist:
            if pat.startswith('**.'):
                if host.endswith(pat[2:]) or host == pat[3:]:
                    return True
            elif host == pat:
                return True
        return False

    counts = {}
    blocked_deals = []
    for d in deals:
        img = d.get('image') or d.get('imagine_url', '')
        if not img: continue
        m = _re.match(r'https?://([^/]+)/', img)
        if not m: continue
        host = m.group(1)
        counts[host] = counts.get(host, 0) + 1
        if not matches(host):
            blocked_deals.append(d.get('id', '<no-id>'))

    result['details']['hosts'] = counts
    result['details']['blocked'] = blocked_deals[:20]

    if blocked_deals:
        bad_hosts = {h for h in counts if not matches(h)}
        result['issues'].append(
            f"{len(blocked_deals)} deals have image hosts NOT in next.config.js whitelist: {sorted(bad_hosts)}"
        )
        result['status'] = 'fail'

    logger.info(
        f"  Image hosts: {len(counts)} unique, "
        f"{len(blocked_deals)} deals blocked by Next/Image"
    )
    return result


# ═══════════════════════════════════════════════════
# CHECK 5: Data Quality
# ═══════════════════════════════════════════════════

def audit_data_quality(deals: list, codes: list) -> dict:
    """Check for data quality issues in deals and codes."""
    logger.info("=== CHECK 5: Data Quality ===")
    result = {
        'check': 'data_quality',
        'status': 'unknown',
        'issues': [],
        'details': {
            'total_deals': len(deals),
            'total_codes': len(codes),
            'missing_price': 0,
            'zero_discount': 0,
            'duplicate_ids': 0,
            'expired_but_active': 0,
            'missing_affiliate_url': 0,
            'negative_discount': 0
        }
    }

    seen_ids = set()
    now = datetime.now(timezone.utc)

    for deal in deals:
        deal_id = deal.get('id', '')

        # Duplicate IDs
        if deal_id in seen_ids:
            result['details']['duplicate_ids'] += 1
            result['issues'].append(f"Duplicate deal ID: {deal_id}")
        seen_ids.add(deal_id)

        # Missing price
        price = deal.get('price') or deal.get('pret_redus', 0)
        if not price or price <= 0:
            result['details']['missing_price'] += 1

        # Zero or negative discount
        discount = deal.get('discount_percent') or deal.get('procent_reducere', 0)
        if discount <= 0:
            result['details']['zero_discount'] += 1
        if discount < 0:
            result['details']['negative_discount'] += 1
            result['issues'].append(f"Negative discount on {deal_id}: {discount}%")

        # Missing affiliate URL
        aff = deal.get('affiliate_url') or deal.get('link_afiliat', '')
        if not aff or aff == '#':
            result['details']['missing_affiliate_url'] += 1

        # Expired but still active
        is_active = deal.get('is_active', True) or deal.get('activ', True)
        expiry = deal.get('data_expirare') or deal.get('expiry_date')
        if is_active and expiry:
            try:
                exp_date = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
                if exp_date < now:
                    result['details']['expired_but_active'] += 1
                    result['issues'].append(f"Expired but active: {deal_id} (expired {expiry})")
            except (ValueError, TypeError):
                pass

    # Severity
    critical_issues = (
        result['details']['duplicate_ids'] +
        result['details']['negative_discount'] +
        result['details']['expired_but_active']
    )

    if critical_issues > 0:
        result['status'] = 'fail'
    elif result['details']['missing_price'] > 0 or result['details']['missing_affiliate_url'] > 0:
        result['status'] = 'warn'
    else:
        result['status'] = 'pass'

    logger.info(
        f"  Data quality: {result['details']['missing_price']} missing price, "
        f"{result['details']['zero_discount']} zero discount, "
        f"{result['details']['duplicate_ids']} duplicate IDs"
    )
    return result


# ═══════════════════════════════════════════════════
# CHECK 6: Security Headers
# ═══════════════════════════════════════════════════

def audit_security_headers(session) -> dict:
    """Check security headers on live site."""
    logger.info("=== CHECK 6: Security Headers ===")
    result = {
        'check': 'security_headers',
        'status': 'unknown',
        'issues': [],
        'details': {'headers_present': {}, 'headers_missing': []}
    }

    expected_headers = {
        'x-content-type-options': 'nosniff',
        'x-frame-options': None,  # Any value is fine
        'strict-transport-security': None,
        'content-security-policy': None,
        'referrer-policy': None,
        'x-xss-protection': None,
    }

    try:
        resp = session.get(SITE_URL, timeout=15)
        headers = {k.lower(): v for k, v in resp.headers.items()}

        for header, expected_value in expected_headers.items():
            if header in headers:
                result['details']['headers_present'][header] = headers[header][:100]
            else:
                result['details']['headers_missing'].append(header)
                result['issues'].append(f"Missing security header: {header}")

    except Exception as e:
        result['status'] = 'fail'
        result['issues'].append(f"Could not check headers: {str(e)[:100]}")
        return result

    missing = len(result['details']['headers_missing'])
    if missing >= 3:
        result['status'] = 'fail'
    elif missing > 0:
        result['status'] = 'warn'
    else:
        result['status'] = 'pass'

    logger.info(
        f"  Security headers: {len(result['details']['headers_present'])} present, "
        f"{missing} missing"
    )
    return result


# ═══════════════════════════════════════════════════
# CHECK 7: Page Accessibility
# ═══════════════════════════════════════════════════

def audit_pages() -> dict:
    """Check all site pages return 200."""
    logger.info("=== CHECK 7: Page Accessibility ===")
    result = {
        'check': 'pages',
        'status': 'unknown',
        'issues': [],
        'details': {'pages_ok': 0, 'pages_down': 0, 'results': []}
    }

    if check_site_pages:
        page_results = check_site_pages()
        for page in page_results:
            result['details']['results'].append(page)
            if page.get('ok'):
                result['details']['pages_ok'] += 1
            else:
                result['details']['pages_down'] += 1
                result['issues'].append(
                    f"Page down: {page.get('page')} (status {page.get('status', 'N/A')})"
                )
    else:
        result['issues'].append("monitor_agent not available, skipping page checks")

    if result['details']['pages_down'] > 0:
        result['status'] = 'fail'
    elif not check_site_pages:
        result['status'] = 'skip'
    else:
        result['status'] = 'pass'

    logger.info(
        f"  Pages: {result['details']['pages_ok']} OK, "
        f"{result['details']['pages_down']} down"
    )
    return result


# ═══════════════════════════════════════════════════
# MAIN: Run All Checks
# ═══════════════════════════════════════════════════

def run_audit(skip_links: bool = False) -> dict:
    """Run all audit checks and return combined report."""
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("AUDIT COMPLET — GhidulReducerilor.ro")
    logger.info("=" * 60)

    session = create_session()
    deals = load_deals()
    codes = load_codes()
    magazines = load_magazines()

    checks = []

    # 1. Homepage
    checks.append(audit_homepage(session))

    # 2. Affiliate links (optional skip for speed)
    if not skip_links:
        checks.append(audit_affiliate_links(deals, session))
    else:
        logger.info("=== CHECK 2: Affiliate Links — SKIPPED ===")
        checks.append({'check': 'affiliate_links', 'status': 'skip', 'issues': [], 'details': {}})

    # 3. Store coverage
    checks.append(audit_store_coverage(deals, magazines))

    # 4. Images
    checks.append(audit_images(deals))

    # 4b. Image hosts whitelist (Next/Image remotePatterns)
    checks.append(audit_image_hosts(deals))

    # 5. Data quality
    checks.append(audit_data_quality(deals, codes))

    # 6. Security headers
    checks.append(audit_security_headers(session))

    # 7. Page accessibility
    checks.append(audit_pages())

    # ═══ Summary ═══
    elapsed_s = round(time.time() - start_time, 1)
    total_issues = sum(len(c['issues']) for c in checks)
    passes = sum(1 for c in checks if c['status'] == 'pass')
    fails = sum(1 for c in checks if c['status'] == 'fail')
    warns = sum(1 for c in checks if c['status'] == 'warn')
    skips = sum(1 for c in checks if c['status'] == 'skip')

    # Score: start at 100, deduct for issues
    score = 100
    for check in checks:
        if check['status'] == 'fail':
            score -= 15
        elif check['status'] == 'warn':
            score -= 5
    score = max(0, score)

    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'site': SITE_URL,
        'duration_seconds': elapsed_s,
        'score': score,
        'summary': {
            'total_checks': len(checks),
            'pass': passes,
            'fail': fails,
            'warn': warns,
            'skip': skips,
            'total_issues': total_issues
        },
        'checks': checks
    }

    logger.info("=" * 60)
    logger.info(f"AUDIT COMPLET in {elapsed_s}s")
    logger.info(f"Score: {score}/100 | Pass: {passes} | Fail: {fails} | Warn: {warns} | Skip: {skips}")
    logger.info(f"Total issues: {total_issues}")
    logger.info("=" * 60)

    return report


def save_report(report: dict, output_format: str = 'both'):
    """Save report as JSON and optionally update AUDIT_LOG.md."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')

    # JSON report
    json_path = LOGS_DIR / f'audit_full_{timestamp}.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON report saved: {json_path}")

    # Also save as latest
    latest_path = LOGS_DIR / 'audit_full_latest.json'
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    if output_format in ('both', 'markdown'):
        update_audit_log(report)

    return json_path


def update_audit_log(report: dict):
    """Append latest audit results to AUDIT_LOG.md."""
    log_path = ROOT / 'AUDIT_LOG.md'
    if not log_path.exists():
        return

    content = log_path.read_text(encoding='utf-8')

    # Replace the automated results section
    marker = "## Automated Audit Results"
    if marker in content:
        before = content.split(marker)[0]

        summary = report['summary']
        score = report['score']
        timestamp = report['timestamp']

        section = f"""{marker}

**Last run:** {timestamp}
**Score:** {score}/100
**Checks:** {summary['pass']} pass, {summary['fail']} fail, {summary['warn']} warn, {summary['skip']} skip
**Total issues:** {summary['total_issues']}

| Check | Status | Issues |
|-------|--------|--------|
"""
        for check in report['checks']:
            status_icon = {'pass': 'PASS', 'fail': 'FAIL', 'warn': 'WARN', 'skip': 'SKIP'}.get(check['status'], '?')
            issue_count = len(check.get('issues', []))
            top_issue = check['issues'][0][:60] if check['issues'] else '—'
            section += f"| {check['check']} | {status_icon} | {issue_count} ({top_issue}) |\n"

        section += f"\n> Full report: `logs/audit_full_latest.json`\n"

        log_path.write_text(before + section, encoding='utf-8')
        logger.info("Updated AUDIT_LOG.md")


def print_summary(report: dict):
    """Print human-readable summary to terminal."""
    print("\n" + "=" * 60)
    print(f"  AUDIT REPORT — ghidulreducerilor.ro")
    print(f"  Score: {report['score']}/100 | Duration: {report['duration_seconds']}s")
    print("=" * 60)

    for check in report['checks']:
        status_emoji = {
            'pass': '[PASS]', 'fail': '[FAIL]',
            'warn': '[WARN]', 'skip': '[SKIP]'
        }.get(check['status'], '[????]')
        print(f"\n{status_emoji} {check['check']}")
        for issue in check.get('issues', [])[:5]:
            print(f"  - {issue}")

    s = report['summary']
    print(f"\n{'=' * 60}")
    print(f"  TOTAL: {s['pass']} pass, {s['fail']} fail, {s['warn']} warn, {s['skip']} skip")
    print(f"  Issues: {s['total_issues']}")
    print(f"  Report: logs/audit_full_latest.json")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='GhidulReducerilor Full Site Audit')
    parser.add_argument('--skip-links', action='store_true',
                        help='Skip affiliate link checking (faster)')
    parser.add_argument('--output', choices=['json', 'markdown', 'both'], default='both',
                        help='Output format')
    args = parser.parse_args()

    report = run_audit(skip_links=args.skip_links)
    save_report(report, output_format=args.output)
    print_summary(report)

    # Exit code based on score
    if report['score'] < 50:
        sys.exit(2)  # Critical
    elif report['score'] < 80:
        sys.exit(1)  # Warnings
    sys.exit(0)


if __name__ == '__main__':
    main()
