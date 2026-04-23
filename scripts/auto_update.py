#!/usr/bin/env python3
"""
GhidulReducerilor.ro — Auto-Update Engine (Weekly)
===================================================
Orchestrates all maintenance tasks in sequence:
  1. Run full audit
  2. Run auto-repair (apply fixes)
  3. Refresh Profitshare links
  4. Run link checker (verify post-repair)
  5. Generate summary report

Designed to run via GitHub Actions weekly (Sunday 02:00 UTC).
NOT a persistent scheduler — it runs once and exits.

Utilizare:
  python scripts/auto_update.py                # Full update
  python scripts/auto_update.py --audit-only   # Just audit, no repairs
  python scripts/auto_update.py --dry-run      # Audit + dry-run repairs
"""

import json
import sys
import os
import argparse
import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

LOGS_DIR = ROOT / 'logs'
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = ROOT / 'data'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'auto_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('auto_update')


def run_step(name, func, *args, **kwargs):
    """Run a step with error handling. Returns (success, result)."""
    logger.info(f">>> Step: {name}")
    try:
        result = func(*args, **kwargs)
        logger.info(f"[OK] {name}")
        return True, result
    except Exception as e:
        logger.error(f"[FAIL] {name}: {e}")
        traceback.print_exc()
        return False, {'error': str(e)}


def run_auto_update(audit_only=False, dry_run=False):
    """Main auto-update orchestration."""
    start_time = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info("AUTO-UPDATE ENGINE — GhidulReducerilor.ro")
    logger.info(f"Mode: {'audit-only' if audit_only else 'dry-run' if dry_run else 'full'}")
    logger.info("=" * 60)

    steps_results = {}

    # ═══ Step 1: Full Audit ═══
    from audit_full import run_audit
    success, audit_report = run_step("Full Audit", run_audit, skip_links=False)
    steps_results['audit'] = {
        'success': success,
        'score': audit_report.get('score', 0) if success else 0,
        'issues': audit_report.get('summary', {}).get('total_issues', 0) if success else -1
    }

    if audit_only:
        # Save audit report and exit
        from audit_full import save_report
        if success:
            save_report(audit_report)
        return _finalize(start_time, steps_results, audit_only=True)

    # ═══ Step 2: Auto-Repair ═══
    from auto_repair import run_repairs
    apply = not dry_run
    success, repair_report = run_step("Auto-Repair", run_repairs, dry_run=not apply)
    steps_results['repair'] = {
        'success': success,
        'repairs_count': repair_report.get('total_repairs', 0) if success else 0,
        'dry_run': not apply
    }

    # ═══ Step 3: Refresh Profitshare Links ═══
    if not dry_run and os.getenv('PROFITSHARE_API_USER') and os.getenv('PROFITSHARE_API_KEY'):
        try:
            from generate_profitshare_links import process_deals, process_codes
            success_deals, _ = run_step("Profitshare Links (deals)", process_deals)
            success_codes, _ = run_step("Profitshare Links (codes)", process_codes)
            steps_results['profitshare'] = {
                'success': success_deals and success_codes,
                'deals_processed': success_deals,
                'codes_processed': success_codes
            }
        except Exception as e:
            logger.warning(f"Profitshare link refresh skipped: {e}")
            steps_results['profitshare'] = {'success': False, 'skipped': True, 'reason': str(e)}
    else:
        reason = 'dry_run' if dry_run else 'missing API credentials'
        logger.info(f"Profitshare link refresh skipped: {reason}")
        steps_results['profitshare'] = {'success': True, 'skipped': True, 'reason': reason}


    # === Step 3b: 2Performant Import ===
    if not dry_run and os.getenv('TWO_PERFORMANT_USER_KEY'):
        try:
            import subprocess, sys as _sys
            script = str(ROOT / 'agents' / 'two_performant_to_deals.py')
            r2p = subprocess.run([_sys.executable, script], capture_output=True, text=True, timeout=120)
            logger.info(r2p.stdout[-2000:] if r2p.stdout else '(no output)')
            if r2p.returncode != 0:
                logger.warning(f"2Performant import exit {r2p.returncode}: {r2p.stderr[-500:]}")
            steps_results['two_performant'] = {'success': r2p.returncode == 0}
        except Exception as e:
            logger.warning(f"2Performant import skipped: {e}")
            steps_results['two_performant'] = {'success': False, 'skipped': True, 'reason': str(e)}
    else:
        reason = 'dry_run' if dry_run else 'TWO_PERFORMANT_USER_KEY not set'
        logger.info(f"2Performant import skipped: {reason}")
        steps_results['two_performant'] = {'success': True, 'skipped': True, 'reason': reason}

    # ═══ Step 4: Link Checker (verify) ═══
    if not dry_run:
        try:
            from link_checker import load_deals, run_checks, save_deals, save_report as save_link_report
            deals = load_deals()
            success, check_result = run_step("Link Checker (verify)", run_checks, deals, mode='quick')
            if success and isinstance(check_result, tuple):
                stats, updated_deals = check_result
                save_deals(updated_deals)
                save_link_report(stats)
                steps_results['link_check'] = {
                    'success': True,
                    'ok': stats.get('ok', 0),
                    'broken': stats.get('broken', 0)
                }
            else:
                steps_results['link_check'] = {'success': False}
        except Exception as e:
            logger.warning(f"Link checker skipped: {e}")
            steps_results['link_check'] = {'success': False, 'error': str(e)}
    else:
        steps_results['link_check'] = {'success': True, 'skipped': True, 'reason': 'dry_run'}

    # ═══ Step 5: Save audit report ═══
    if audit_report and isinstance(audit_report, dict):
        from audit_full import save_report
        save_report(audit_report)

    return _finalize(start_time, steps_results)


def _finalize(start_time, steps_results, audit_only=False):
    """Generate final summary and save status."""
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

    all_success = all(s.get('success', False) for s in steps_results.values())

    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'duration_seconds': round(elapsed, 1),
        'success': all_success,
        'audit_only': audit_only,
        'steps': steps_results
    }

    # Save update status (read by dashboard)
    status_path = DATA_DIR / 'update_status.json'
    status = {
        'ultima_actualizare': report['timestamp'],
        'success': all_success,
        'duration_s': report['duration_seconds'],
        'audit_score': steps_results.get('audit', {}).get('score', 0),
        'repairs_applied': steps_results.get('repair', {}).get('repairs_count', 0),
        'links_ok': steps_results.get('link_check', {}).get('ok', 0),
        'links_broken': steps_results.get('link_check', {}).get('broken', 0),
    }
    with open(status_path, 'w', encoding='utf-8') as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

    # Save full report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    report_path = LOGS_DIR / f'auto_update_{timestamp}.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Print summary
    logger.info("=" * 60)
    logger.info(f"AUTO-UPDATE {'COMPLETE' if all_success else 'FINISHED WITH ERRORS'}")
    logger.info(f"Duration: {elapsed:.1f}s")
    for step_name, step_result in steps_results.items():
        status = "[OK]" if step_result.get('success') else "[FAIL]"
        skipped = " (skipped)" if step_result.get('skipped') else ""
        logger.info(f"  {status} {step_name}{skipped}")
    logger.info(f"Report: {report_path}")
    logger.info("=" * 60)

    return report


def main():
    parser = argparse.ArgumentParser(description='GhidulReducerilor Auto-Update Engine')
    parser.add_argument('--audit-only', action='store_true',
                        help='Only run audit, no repairs')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run audit + dry-run repairs (no changes)')
    args = parser.parse_args()

    report = run_auto_update(
        audit_only=args.audit_only,
        dry_run=args.dry_run
    )

    sys.exit(0 if report.get('success', False) else 1)


if __name__ == '__main__':
    main()
