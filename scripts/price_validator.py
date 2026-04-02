#!/usr/bin/env python3
"""
GhidulReducerilor.ro — Validator Prețuri (Directiva Omnibus UE)
Verifică dacă reducerile sunt reale conform Directivei Omnibus:
prețul afișat ca "original" trebuie să fie cel mai mic preț din ultimele 30 de zile.

Utilizare:
  python scripts/price_validator.py --mode check
  python scripts/price_validator.py --mode update
  python scripts/price_validator.py --deal-id emag-001
"""

import json
import os
import logging
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/price_validator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('price_validator')

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / 'data'
PRICE_HISTORY_DIR = DATA_DIR / 'price_history'
PRICE_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

import sys
sys.path.insert(0, str(Path(__file__).parent))
from utils import normalize_deal  # noqa: E402


def load_deals() -> list:
    with open(DATA_DIR / 'deals.json', 'r', encoding='utf-8') as f:
        return [normalize_deal(d) for d in json.load(f)]


def save_deals(deals: list):
    with open(DATA_DIR / 'deals.json', 'w', encoding='utf-8') as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)


def load_price_history(deal_id: str) -> list:
    """Încarcă istoricul de prețuri pentru un deal."""
    history_file = PRICE_HISTORY_DIR / f"{deal_id}.json"
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_price_history(deal_id: str, history: list):
    """Salvează istoricul de prețuri pentru un deal."""
    history_file = PRICE_HISTORY_DIR / f"{deal_id}.json"
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def record_price(deal: dict) -> dict:
    """
    Înregistrează prețul curent în istoricul prețurilor.
    Returnează înregistrarea adăugată.
    """
    deal_id = deal.get('id', '')
    if not deal_id:
        return {}

    # Normalizare câmpuri (schema veche RO sau nouă EN)
    price = deal.get('price') or deal.get('pret_redus') or deal.get('newPrice', 0)
    original_price = deal.get('originalPrice') or deal.get('pret_original') or deal.get('original_price', 0)

    record = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'price': float(price or 0),
        'original_price': float(original_price or 0),
        'discount_percent': deal.get('discount_percent') or deal.get('procent_reducere', 0)
    }

    history = load_price_history(deal_id)
    history.append(record)

    # Păstrează doar ultimele 90 de zile
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    history = [
        h for h in history
        if datetime.fromisoformat(h['timestamp'].replace('Z', '+00:00')) > cutoff
    ]

    save_price_history(deal_id, history)
    return record


def get_min_price_30d(deal_id: str) -> Optional[float]:
    """
    Returnează prețul minim din ultimele 30 de zile (Directiva Omnibus).
    Prețul "original" afișat ca bară tăiată trebuie să fie ≥ acest minim.
    """
    history = load_price_history(deal_id)
    if not history:
        return None

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    recent = [
        h for h in history
        if datetime.fromisoformat(h['timestamp'].replace('Z', '+00:00')) > cutoff
    ]

    if not recent:
        return None

    prices = [h['price'] for h in recent if h.get('price', 0) > 0]
    return min(prices) if prices else None


def validate_deal_omnibus(deal: dict) -> dict:
    """
    Validează un deal conform Directivei Omnibus.

    Regulă: Prețul "original" (barat) trebuie să fie cel mai mic preț
    din ultimele 30 de zile, nu un preț umflat artificial.

    Returnează deal-ul cu câmpuri de validare adăugate.
    """
    deal_id = deal.get('id', '')
    original_price = float(deal.get('originalPrice') or deal.get('pret_original') or 0)
    current_price = float(deal.get('price') or deal.get('pret_redus') or 0)

    min_30d = get_min_price_30d(deal_id)

    deal['omnibus_checked_at'] = datetime.now(timezone.utc).isoformat()
    deal['pret_minim_30z'] = min_30d

    if min_30d is None:
        # Fără istoric — nu putem valida
        deal['omnibus_validated'] = None  # Unknown
        deal['is_fake_discount'] = False
        logger.debug(f"[{deal_id}] Fără istoric — skip validare Omnibus")
        return deal

    # Verificare cheie Omnibus:
    # Dacă prețul "original" afișat este MAI MIC decât minimul din 30z,
    # înseamnă că prețul a crescut artificial înainte de reducere (fake discount)
    if original_price > 0 and original_price < min_30d * 0.95:
        # Marja de 5% pentru variații normale
        deal['is_fake_discount'] = True
        deal['omnibus_validated'] = False
        logger.warning(
            f"[{deal_id}] ⚠️ REDUCERE FALSĂ DETECTATĂ: "
            f"preț original {original_price} RON < minim 30z {min_30d} RON"
        )
    else:
        deal['is_fake_discount'] = False
        deal['omnibus_validated'] = True
        logger.debug(f"[{deal_id}] ✅ Omnibus OK: original {original_price} ≥ minim30z {min_30d}")

    return deal


def run_validation(deals: list, deal_id: Optional[str] = None) -> dict:
    """Rulează validarea Omnibus pe toate deal-urile sau unul specific."""
    if deal_id:
        deals_to_check = [d for d in deals if d.get('id') == deal_id]
    else:
        deals_to_check = [d for d in deals if d.get('is_active', True) and d.get('activ', True)]

    stats = {
        'total': len(deals_to_check),
        'validated_ok': 0,
        'fake_discounts': 0,
        'no_history': 0,
        'fake_deals': []
    }

    for i, deal in enumerate(deals):
        if deal.get('id') not in [d.get('id') for d in deals_to_check]:
            continue

        # Înregistrează prețul curent
        record_price(deal)

        # Validează
        deals[i] = validate_deal_omnibus(deal)

        if deals[i].get('omnibus_validated') is True:
            stats['validated_ok'] += 1
        elif deals[i].get('is_fake_discount'):
            stats['fake_discounts'] += 1
            stats['fake_deals'].append({
                'id': deal.get('id'),
                'title': deal.get('title') or deal.get('titlu', '')[:50],
                'original_price': deal.get('originalPrice') or deal.get('pret_original'),
                'min_30d': deals[i].get('pret_minim_30z')
            })
        else:
            stats['no_history'] += 1

    return stats, deals


def main():
    parser = argparse.ArgumentParser(description='GhidulReducerilor Price Validator (Omnibus)')
    parser.add_argument('--mode', choices=['check', 'update', 'record'], default='check')
    parser.add_argument('--deal-id', help='Validează doar un deal specific')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    logger.info(f"=== Price Validator — mod: {args.mode} ===")

    deals = load_deals()

    if args.mode == 'record':
        # Doar înregistrează prețurile curente fără validare
        count = 0
        for deal in deals:
            if deal.get('is_active', True) or deal.get('activ', True):
                record_price(deal)
                count += 1
        logger.info(f"Prețuri înregistrate: {count}")
        print(f"✅ Înregistrate {count} prețuri în istoric")
        return

    # Check sau Update
    stats, updated_deals = run_validation(deals, deal_id=args.deal_id)

    if args.mode == 'update' and not args.dry_run:
        save_deals(updated_deals)
        logger.info("Deals actualizate cu statusul Omnibus")

    print(f"\n=== RAPORT OMNIBUS VALIDATOR ===")
    print(f"Total verificate: {stats['total']}")
    print(f"✅ Reduceri valide: {stats['validated_ok']}")
    print(f"❌ Reduceri false: {stats['fake_discounts']}")
    print(f"ℹ️  Fără istoric: {stats['no_history']}")

    if stats['fake_deals']:
        print(f"\n⚠️ REDUCERI FALSE DETECTATE:")
        for fd in stats['fake_deals']:
            print(f"  - {fd['id']}: original {fd['original_price']} RON < minim30z {fd['min_30d']} RON")
            print(f"    {fd['title']}")

    return stats


if __name__ == '__main__':
    main()
