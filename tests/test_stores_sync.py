# -*- coding: utf-8 -*-
"""
Guardrail: fiecare magazin cu deal-uri active în data/deals.json trebuie să
aibă o intrare în data/stores.json.

Context (15 iul 2026): gsmnet a fost activat în 2p_merchants.json + allowlist,
pipeline-ul a importat 7 deal-uri, dar /reduceri/gsmnet nu se genera pentru că
slug-ul lipsea din stores.json (getStoreBySlug → undefined). Aceeași clasă de
bug ca suplimente-bio și fashion din CATEGORIES (tests/test_categories_sync.py).
Checklist activare merchant: 2p_merchants.json/config PS + remotePatterns +
stores.json (+ categoria în lib/categories.ts).

Rulează:
  Standalone:  py -3 tests/test_stores_sync.py
  Sau pytest:  pytest tests/test_stores_sync.py -v
"""
import json
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent


def _load(name: str):
    return json.loads((BASE / "data" / name).read_text(encoding="utf-8"))


def _active_merchant_slugs() -> set:
    deals = _load("deals.json")
    if isinstance(deals, dict):
        deals = deals.get("deals", deals)
    return {
        (d.get("magazin") or d.get("store") or "").strip()
        for d in deals
        if d.get("activ", True) and (d.get("magazin") or d.get("store"))
    }


def _store_slugs() -> set:
    stores = _load("stores.json")
    if isinstance(stores, dict):
        stores = stores.get("stores", stores)
    return {s.get("slug", "").strip() for s in stores}


def test_all_active_merchants_in_stores_json():
    missing = sorted(_active_merchant_slugs() - _store_slugs())
    assert not missing, (
        f"Magazine cu deal-uri active FĂRĂ intrare în data/stores.json: {missing}. "
        "Adaugă intrarea (id/nume/slug/descriere/logo_emoji/culoare/"
        "categorie_principala/url_site/comision_mediu/retea) — altfel "
        "/reduceri/<slug> nu se generează."
    )


if __name__ == "__main__":
    failed = False
    for fn in [test_all_active_merchants_in_stores_json]:
        try:
            fn()
            print(f"  [OK]   {fn.__name__}")
        except AssertionError as e:
            failed = True
            print(f"  [FAIL] {fn.__name__}: {e}")
    sys.exit(1 if failed else 0)
