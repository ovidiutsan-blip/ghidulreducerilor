#!/usr/bin/env python3
"""
Merge data/raw/altemagazine_<today>.json into data/deals.json.

Runs after agent_altemagazine.py produces the raw file.
- Preserves existing Profitshare deals for watch24/forit/fornello/emag
  (these are scraped by scripts/scrape_and_merge.py / agent_emag)
- Replaces deals for magazines in stores_config.json (status=activ)
  with freshly scraped data from the raw file
- Normalizes via utils.normalize_deal so both RO and EN fields are present

Usage:
  python scripts/merge_altemagazine.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CONFIG_DIR = ROOT / "config"

sys.path.insert(0, str(Path(__file__).parent))
from utils import normalize_deal  # noqa: E402


def main() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    raw_file = RAW_DIR / f"altemagazine_{today}.json"
    deals_file = DATA_DIR / "deals.json"

    if not raw_file.exists():
        print(f"[merge_altemagazine] No raw file for today: {raw_file.name}")
        return 0

    raw = json.loads(raw_file.read_text(encoding="utf-8"))
    if not raw:
        print("[merge_altemagazine] Raw file is empty; nothing to merge.")
        return 0

    # Determine which magazine slugs were produced by agent_altemagazine
    alte_magazines = {d["magazin"] for d in raw if d.get("magazin")}
    print(f"[merge_altemagazine] Raw deals: {len(raw)} from magazines: {sorted(alte_magazines)}")

    # Load existing deals
    existing = []
    if deals_file.exists():
        existing = json.loads(deals_file.read_text(encoding="utf-8"))

    # Keep existing deals for magazines NOT in alte_magazines (e.g., emag, watch24, forit, fornello)
    kept = [d for d in existing if (d.get("magazin") or d.get("magazine_key") or "") not in alte_magazines]
    print(f"[merge_altemagazine] Kept {len(kept)} existing deals from other scrapers")

    # Normalize new deals
    new_deals = [normalize_deal(d) for d in raw]

    # Combine + sort by discount
    final = kept + new_deals
    final.sort(key=lambda d: d.get("procent_reducere") or d.get("discount_percent", 0), reverse=True)

    # Write back
    deals_file.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")

    # Summary
    stores = {}
    for d in final:
        s = d.get("magazin") or d.get("magazine_key") or "unknown"
        stores[s] = stores.get(s, 0) + 1
    print(f"[merge_altemagazine] Total deals.json after merge: {len(final)}")
    for s in sorted(stores):
        print(f"  {s}: {stores[s]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
