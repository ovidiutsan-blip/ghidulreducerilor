# -*- coding: utf-8 -*-
"""
Guardrail: fiecare categorie cu deal-uri active în data/deals.json trebuie
să existe în CATEGORIES (lib/categories.ts).

Context (14 iul 2026): slug prezent în deals dar absent din CATEGORIES =>
/categorie/<slug> dă 404 deși deal-urile există, iar categoria lipsește din
navigație. S-a întâmplat de două ori în aceeași zi: suplimente-bio (19 deal-uri
vegis invizibile) și fashion (47 deal-uri otter invizibile).

Ruleaza:
  Standalone:  py -3 tests/test_categories_sync.py
  Sau pytest:  pytest tests/test_categories_sync.py -v
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _active_categories() -> set[str]:
    data = json.loads((ROOT / "data" / "deals.json").read_text(encoding="utf-8"))
    deals = data.get("deals", data) if isinstance(data, dict) else data
    return {d.get("categorie") for d in deals
            if d.get("is_active") and d.get("categorie")}


def _known_slugs() -> set[str]:
    src = (ROOT / "lib" / "categories.ts").read_text(encoding="utf-8")
    return set(re.findall(r"slug: '([a-z0-9-]+)'", src))


def test_all_active_categories_in_categories_ts():
    missing = sorted(_active_categories() - _known_slugs())
    assert not missing, (
        f"Categorii cu deal-uri active dar absente din lib/categories.ts: {missing} "
        "— /categorie/<slug> va da 404 și categoria lipsește din navigație."
    )


def _main() -> int:
    failed = 0
    for fn in [test_all_active_categories_in_categories_ts]:
        try:
            fn()
            print(f"  [OK]   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  [FAIL] {fn.__name__}: {e}")
    return failed


if __name__ == "__main__":
    raise SystemExit(_main())
