#!/usr/bin/env python3
"""
Merge data/raw/emag_<today>.json into data/deals.json.

Runs after agents/agent_emag.py produces the raw file.
- Replaces existing magazin=='emag' deals with freshly scraped data
- Normalizes via utils.normalize_deal so both RO and EN fields are present
- Mirrors scripts/merge_altemagazine.py (same safe replace-by-store pattern)

Usage:
  python scripts/merge_emag.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

sys.path.insert(0, str(Path(__file__).parent))
from utils import normalize_deal  # noqa: E402


def main() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    raw_file = RAW_DIR / f"emag_{today}.json"
    deals_file = DATA_DIR / "deals.json"

    if not raw_file.exists():
        print(f"[merge_emag] No raw file for today: {raw_file.name}")
        return 0

    raw = json.loads(raw_file.read_text(encoding="utf-8"))
    if not raw:
        print("[merge_emag] Raw file is empty; nothing to merge.")
        return 0

    print(f"[merge_emag] Raw deals: {len(raw)}")

    existing = []
    if deals_file.exists():
        existing = json.loads(deals_file.read_text(encoding="utf-8"))

    # Keep every existing deal that is NOT emag
    kept = [d for d in existing if (d.get("magazin") or d.get("magazine_key") or "") != "emag"]
    print(f"[merge_emag] Kept {len(kept)} existing deals from other scrapers")

    new_deals = [normalize_deal(d) for d in raw]

    final = kept + new_deals
    final.sort(key=lambda d: d.get("procent_reducere") or d.get("discount_percent", 0), reverse=True)

    deals_file.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[merge_emag] Total deals.json after merge: {len(final)} (emag: {len(new_deals)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
