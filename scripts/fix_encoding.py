"""
fix_encoding.py — Fix mojibake (cp1252 citit ca latin-1) în deals.json și în importeri.

Problema: text din Profitshare API encodat UTF-8, importat cu encoding greșit (cp1252/latin-1).
Rezultat: "Ã®n" în loc de "în", "plÄƒci" în loc de "plăci", etc.
"""
import json
import sys
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(__file__).parent.parent
DEALS_PATH = BASE / "data" / "deals.json"

# Pattern pentru detectare mojibake specific românesc
MOJI_CHARS = set('ÃÄÅÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞàáâãäåæçèéêëìíîïðñòóôõöøùúûüý')

def looks_like_mojibake(s: str) -> bool:
    """Detectează dacă stringul conține mojibake tipic pentru română."""
    if not s:
        return False
    # Caractere tipice mojibake RO: Ã® (î), Äƒ (ă), Ã¢ (â), È› (ț), È™ (ș), Ã® etc.
    moji_pattern = re.compile(r'Ã[®¢¯¬]|Ä[ƒ€]|È[›>™ˆ]|Å£|Å¸|Ã®|Â')
    return bool(moji_pattern.search(s))

def fix_mojibake(s: str) -> str:
    """Decodează mojibake cp1252→UTF-8."""
    if not s:
        return s
    try:
        fixed = s.encode('cp1252').decode('utf-8')
        return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s

TEXT_FIELDS = ['titlu', 'title', 'descriere', 'description', 'magazin', 'store']

def fix_deals():
    with open(DEALS_PATH, encoding='utf-8') as f:
        deals = json.load(f)

    fixed_deals = 0
    fixed_fields = 0

    for d in deals:
        deal_fixed = False
        for field in TEXT_FIELDS:
            val = d.get(field)
            if not val or not isinstance(val, str):
                continue
            if looks_like_mojibake(val):
                fixed = fix_mojibake(val)
                if fixed != val:
                    print(f"  Fix [{field}]: {val[:60]!r}")
                    print(f"       → {fixed[:60]!r}")
                    d[field] = fixed
                    fixed_fields += 1
                    deal_fixed = True
        if deal_fixed:
            fixed_deals += 1

    print(f"\n✅ Fixat {fixed_fields} câmpuri în {fixed_deals} deals")

    with open(DEALS_PATH, 'w', encoding='utf-8') as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)

    print(f"✅ deals.json salvat ({len(deals)} deals total)")
    return fixed_deals

if __name__ == '__main__':
    print("=== Fix encoding mojibake în deals.json ===\n")
    fixed = fix_deals()
    if fixed == 0:
        print("Nicio problemă de encoding detectată în deals.json")
