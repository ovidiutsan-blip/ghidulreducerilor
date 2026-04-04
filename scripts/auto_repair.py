#!/usr/bin/env python3
"""
GhidulReducerilor.ro — Reparare Automata
=========================================
Citeste raportul de audit si repara problemele gasite:
  1. Converteste linkuri Profitshare directe -> /out/[id]
  2. Dezactiveaza deals cu linkuri moarte
  3. Seteaza fallback URL pentru magazine pending approval
  4. Elimina deals expirate
  5. Raporteaza placeholder images (nu le inlocuieste automat)

Utilizare:
  python scripts/auto_repair.py --dry-run     # Arata ce s-ar repara (default)
  python scripts/auto_repair.py --apply        # Aplica reparatiile
  python scripts/auto_repair.py --apply --skip-links  # Aplica fara link check

Reuse: utils.py, link_checker.py, generate_profitshare_links.py
"""

import json
import sys
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

from utils import normalize_deal, fix_profitshare_link, is_profitshare_direct  # noqa: E402

DATA_DIR = ROOT / 'data'
CONFIG_DIR = ROOT / 'config'
LOGS_DIR = ROOT / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'auto_repair.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('auto_repair')


def load_data():
    """Load deals, codes, and magazine config."""
    deals_path = DATA_DIR / 'deals.json'
    codes_path = DATA_DIR / 'codes.json'
    mag_path = CONFIG_DIR / 'magazines.json'

    deals = []
    codes = []
    magazines = {}

    if deals_path.exists():
        with open(deals_path, 'r', encoding='utf-8') as f:
            deals = json.load(f)
    if codes_path.exists():
        with open(codes_path, 'r', encoding='utf-8') as f:
            codes = json.load(f)
    if mag_path.exists():
        with open(mag_path, 'r', encoding='utf-8') as f:
            magazines = json.load(f).get('magazines', {})

    return deals, codes, magazines


def save_deals(deals):
    """Save deals back to JSON."""
    path = DATA_DIR / 'deals.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)


def save_codes(codes):
    """Save codes back to JSON."""
    path = DATA_DIR / 'codes.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(codes, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════
# REPAIR 1: Fix direct Profitshare links
# ═══════════════════════════════════════════════════

def repair_profitshare_links(deals, codes, dry_run=True):
    """Fix self-referencing /out/ links back to l.profitshare.ro.

    deals.json should contain the FINAL Profitshare URL (l.profitshare.ro/l/NNNNN).
    The frontend handles the /out/[deal-id] redirect separately.
    This repair catches any deals where link_afiliat accidentally points to /out/.
    """
    repairs = []
    import re

    for items, item_type in [(deals, 'deal'), (codes, 'code')]:
        for item in items:
            link = item.get('link_afiliat', '')
            # Fix self-referencing /out/NNNNN links back to Profitshare
            m = re.match(r'https?://ghidulreducerilor\.ro/out/(\d+)', link)
            if m:
                fixed = f'https://l.profitshare.ro/l/{m.group(1)}'
                repairs.append({
                    'type': item_type,
                    'id': item.get('id', '?'),
                    'action': 'fix_self_reference',
                    'before': link,
                    'after': fixed
                })
                if not dry_run:
                    item['link_afiliat'] = fixed
                    item['affiliate_url'] = fixed

    return repairs


# ═══════════════════════════════════════════════════
# REPAIR 2: Deactivate deals with broken links
# ═══════════════════════════════════════════════════

def repair_broken_links(deals, dry_run=True):
    """Deactivate deals that have been marked with broken link status."""
    repairs = []

    for deal in deals:
        link_status = deal.get('link_status', '')
        is_active = deal.get('activ', True) or deal.get('is_active', True)

        if is_active and link_status in ('not_found', 'server_error', 'connection_error'):
            repairs.append({
                'type': 'deal',
                'id': deal.get('id', '?'),
                'action': 'deactivate_broken_link',
                'reason': f'link_status={link_status}',
                'link': (deal.get('link_afiliat') or '')[:80]
            })
            if not dry_run:
                deal['activ'] = False
                deal['is_active'] = False
                deal['deactivated_reason'] = f'auto_repair: {link_status}'
                deal['deactivated_at'] = datetime.now(timezone.utc).isoformat()

    return repairs


# ═══════════════════════════════════════════════════
# REPAIR 3: Set fallback for pending stores
# ═══════════════════════════════════════════════════

def repair_pending_stores(deals, magazines, dry_run=True):
    """For stores still pending approval, ensure deals use fallback URL."""
    repairs = []

    pending_stores = {
        slug for slug, config in magazines.items()
        if config.get('status') == 'pending_approval'
    }

    for deal in deals:
        store = deal.get('magazin', '')
        if store not in pending_stores:
            continue

        link = deal.get('link_afiliat', '')
        # If the link contains placeholder affiliate IDs, replace with fallback
        if 'COMPLETEAZĂ' in link or 'PENDING' in link.upper() or not link or link == '#':
            fallback = magazines.get(store, {}).get('fallback_url', '')
            if fallback and link != fallback:
                repairs.append({
                    'type': 'deal',
                    'id': deal.get('id', '?'),
                    'action': 'set_fallback_url',
                    'store': store,
                    'before': link[:80],
                    'after': fallback
                })
                if not dry_run:
                    deal['link_afiliat'] = fallback
                    deal['affiliate_url'] = fallback

    return repairs


# ═══════════════════════════════════════════════════
# REPAIR 4: Remove expired deals
# ═══════════════════════════════════════════════════

def repair_expired_deals(deals, dry_run=True):
    """Deactivate deals past their expiry date."""
    repairs = []
    now = datetime.now(timezone.utc)

    for deal in deals:
        is_active = deal.get('activ', True) or deal.get('is_active', True)
        if not is_active:
            continue

        expiry = deal.get('data_expirare') or deal.get('expiry_date')
        if not expiry:
            continue

        try:
            exp_date = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
            if exp_date < now:
                repairs.append({
                    'type': 'deal',
                    'id': deal.get('id', '?'),
                    'action': 'deactivate_expired',
                    'expired': expiry
                })
                if not dry_run:
                    deal['activ'] = False
                    deal['is_active'] = False
                    deal['deactivated_reason'] = 'auto_repair: expired'
                    deal['deactivated_at'] = now.isoformat()
        except (ValueError, TypeError):
            pass

    return repairs


# ═══════════════════════════════════════════════════
# REPAIR 5: Report placeholder images (info only)
# ═══════════════════════════════════════════════════

def report_placeholder_images(deals):
    """Report deals with placeholder images (don't auto-fix)."""
    reports = []
    placeholder_patterns = ['unsplash.com', 'placeholder.com', 'placehold.co']

    for deal in deals:
        img = deal.get('imagine_url') or deal.get('image', '')
        if any(p in img.lower() for p in placeholder_patterns):
            reports.append({
                'type': 'deal',
                'id': deal.get('id', '?'),
                'action': 'info_placeholder_image',
                'store': deal.get('magazin', ''),
                'image_url': img[:80]
            })

    return reports


# ═══════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════

def run_repairs(dry_run=True) -> dict:
    """Run all repairs and return report."""
    logger.info("=" * 60)
    logger.info(f"AUTO-REPAIR — {'DRY RUN' if dry_run else 'APPLYING CHANGES'}")
    logger.info("=" * 60)

    deals, codes, magazines = load_data()
    all_repairs = []

    # 1. Fix direct Profitshare links
    repairs = repair_profitshare_links(deals, codes, dry_run)
    all_repairs.extend(repairs)
    logger.info(f"[1] Fix Profitshare direct links: {len(repairs)} repairs")

    # 2. Deactivate broken links
    repairs = repair_broken_links(deals, dry_run)
    all_repairs.extend(repairs)
    logger.info(f"[2] Deactivate broken links: {len(repairs)} repairs")

    # 3. Fallback for pending stores
    repairs = repair_pending_stores(deals, magazines, dry_run)
    all_repairs.extend(repairs)
    logger.info(f"[3] Set fallback URLs: {len(repairs)} repairs")

    # 4. Deactivate expired
    repairs = repair_expired_deals(deals, dry_run)
    all_repairs.extend(repairs)
    logger.info(f"[4] Deactivate expired: {len(repairs)} repairs")

    # 5. Report placeholders (always info-only)
    info = report_placeholder_images(deals)
    all_repairs.extend(info)
    logger.info(f"[5] Placeholder images reported: {len(info)}")

    # Save if not dry run
    if not dry_run:
        save_deals(deals)
        save_codes(codes)
        logger.info("Changes saved to deals.json and codes.json")

    # Build report
    actual_repairs = [r for r in all_repairs if r['action'] != 'info_placeholder_image']
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'dry_run': dry_run,
        'total_repairs': len(actual_repairs),
        'total_info': len(info),
        'repairs': all_repairs,
        'summary': {
            'profitshare_fixed': sum(1 for r in all_repairs if r['action'] == 'fix_profitshare_direct'),
            'broken_deactivated': sum(1 for r in all_repairs if r['action'] == 'deactivate_broken_link'),
            'fallback_set': sum(1 for r in all_repairs if r['action'] == 'set_fallback_url'),
            'expired_deactivated': sum(1 for r in all_repairs if r['action'] == 'deactivate_expired'),
            'placeholder_images': len(info)
        }
    }

    # Save repair log
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    log_path = LOGS_DIR / f'repairs_{timestamp}.json'
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"Repair log saved: {log_path}")

    # Print summary
    print(f"\n{'=' * 50}")
    print(f"  AUTO-REPAIR {'(DRY RUN)' if dry_run else '(APPLIED)'}")
    print(f"{'=' * 50}")
    for key, count in report['summary'].items():
        print(f"  {key}: {count}")
    print(f"  TOTAL REPAIRS: {report['total_repairs']}")
    if dry_run:
        print(f"\n  Run with --apply to execute these repairs.")
    print(f"{'=' * 50}")

    return report


def main():
    parser = argparse.ArgumentParser(description='GhidulReducerilor Auto-Repair')
    parser.add_argument('--apply', action='store_true',
                        help='Actually apply repairs (default is dry-run)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Show what would be repaired without changing files')
    args = parser.parse_args()

    dry_run = not args.apply
    report = run_repairs(dry_run=dry_run)

    if report['total_repairs'] > 0 and dry_run:
        sys.exit(1)  # Signal there are things to fix
    sys.exit(0)


if __name__ == '__main__':
    main()
