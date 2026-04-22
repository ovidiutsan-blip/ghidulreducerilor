#!/usr/bin/env python3
"""
Purge deals evomag cu preț bug: pret_redus <= 100 (superscript parsing issue).
Rulează o singură dată pentru a curăța homepage-ul; apoi scraperul fix va
repopula cu date valide.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEALS_PATH = ROOT / "data" / "deals.json"


def main():
    deals = json.loads(DEALS_PATH.read_text(encoding="utf-8"))
    before = len(deals)

    kept = []
    removed = 0
    for d in deals:
        if d.get("magazin") == "evomag" and (
            d.get("pret_redus", 0) <= 100 or d.get("procent_reducere", 0) >= 95
        ):
            removed += 1
            continue
        kept.append(d)

    DEALS_PATH.write_text(
        json.dumps(kept, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Before: {before} | Removed evomag broken: {removed} | After: {len(kept)}")


if __name__ == "__main__":
    main()
