# -*- coding: utf-8 -*-
"""
Test regresie scraper evoMAG — bug #46 (ghost deals 99 lei / -100%).

Context:
  evoMAG foloseste <sup>XX</sup> pentru zecimale (ex: 432<sup>99</sup> lei).
  Bug-ul vechi: [class*='price'] selector prindea orfani <sup>99</sup> din
  badge-uri promo, rezultand min(prices)=99, max(prices)=pret_real,
  deci deal-uri fantoma cu -99%/-100%.

Fix (in agents/agent_altemagazine.py::scrape_evomag):
  1) Preprocesare <sup> cu isdigit: `sup.string = "," + sup_text` inainte
     de get_text() — pentru ca zecimalele sa se lipeasca corect.
  2) Selectori stricti: .product_pret, .npi_pret, .price, .pret,
     [class*='product_pret'] — evita div-uri promo cu "price" in clasa.
  3) Sanity check: `if price_new * 5 < price_old: continue` — ratia
     noua/veche sub 20% e semnal de zgomot, nu oferta reala.

Ruleaza:
  Standalone:  py -3 tests/test_scrape_evomag_regression.py
  Sau pytest:  pytest tests/test_scrape_evomag_regression.py -v
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents import agent_altemagazine as agm  # noqa: E402


# Fixture HTML care reproduce pattern-ul real de pe evomag.ro
FIXTURE_HTML = """
<html><body>

<!-- Card NORMAL: pret + pret_vechi folosind <sup> pt zecimale -->
<div class="product_grid--item">
  <a class="npi_name" href="/product/tv-normal" title="TV normal 100cm">TV normal 100cm</a>
  <img src="https://cdn.evomag.ro/img/tv.jpg">
  <div class="product_pret">349<sup>99</sup> lei</div>
  <div class="product_pret_vechi">500<sup>00</sup> lei</div>
</div>

<!-- Card TRAP: are un <sup>99</sup> orfan intr-un badge promo.
     Sub SELECTORII VECHI ([class*='price']) ar fi prins, producand
     prices=[99, 2411.17, 3863.86] -> ghost deal -97%.
     Sub SELECTORII NOI, doar .product_pret si .product_pret_vechi prind. -->
<div class="product_grid--item">
  <a class="npi_name" href="/product/phone" title="Telefon flagship">Telefon flagship</a>
  <img src="https://cdn.evomag.ro/img/phone.jpg">
  <div class="price_promo_badge"><sup>99</sup></div>
  <div class="product_pret">2411<sup>17</sup> lei</div>
  <div class="product_pret_vechi">3863<sup>86</sup> lei</div>
</div>

<!-- Card TRAP 2: doar un singur pret plus un <sup> orfan.
     Vechiul bug l-ar fi interpretat ca -99% deal. Noul cod nu produce
     nimic pt el (prices cu < 2 elemente). -->
<div class="product_grid--item">
  <a class="npi_name" href="/product/small" title="Produs accesoriu mic">Produs accesoriu mic</a>
  <img src="https://cdn.evomag.ro/img/small.jpg">
  <div class="price_ribbon"><sup>99</sup></div>
  <div class="product_pret">50<sup>00</sup> lei</div>
</div>

</body></html>
"""


class _FakeResponse:
    """Minimal requests.Response double pt session.get mock."""
    def __init__(self, text, status=200):
        self.text = text
        self.status_code = status


def _run_scraper_with_fixture(html):
    """Ruleaza scrape_evomag cu fixture HTML in loc de request real."""
    config = {
        "categories": [{"name": "test", "url": "https://www.evomag.ro/cat"}],
        "max_pages": 1,
        "min_discount": 15,
        "rate_limit_seconds": 0,
    }
    calls = []

    def fake_get(url, timeout=None, **kwargs):
        calls.append(url)
        return _FakeResponse(html, status=200)

    original_get = agm.session.get
    agm.session.get = fake_get
    try:
        deals = agm.scrape_evomag(config)
    finally:
        agm.session.get = original_get

    return deals, calls


# ─── Tests ─────────────────────────────────────────────────────────

def test_no_ghost_deal_from_orphan_sup_99():
    """Regresie #46: orfani <sup>99</sup> NU trebuie sa produca deal -99%/-100%."""
    deals, _ = _run_scraper_with_fixture(FIXTURE_HTML)
    for d in deals:
        assert not (d["pret_redus"] <= 100 and d["procent_reducere"] >= 95), (
            f"Ghost deal detectat: titlu={d['titlu']!r} "
            f"pret_redus={d['pret_redus']} procent={d['procent_reducere']}%"
        )


def test_normal_evomag_card_parsed_correctly():
    """Card normal (349,99 vs 500,00) trebuie sa produca deal valid ~30%."""
    deals, _ = _run_scraper_with_fixture(FIXTURE_HTML)
    normal = [d for d in deals if "tv normal" in d["titlu"].lower()]
    assert len(normal) == 1, (
        f"Astept exact 1 deal 'TV normal', am gasit {len(normal)}. "
        f"Toate deal-urile: {[d['titlu'] for d in deals]}"
    )
    d = normal[0]
    assert abs(d["pret_redus"] - 349.99) < 0.02, f"pret_redus={d['pret_redus']}"
    assert abs(d["pret_original"] - 500.00) < 0.02, f"pret_original={d['pret_original']}"
    assert d["procent_reducere"] == 30, f"procent={d['procent_reducere']}"


def test_trap_card_with_orphan_sup_still_parses_real_prices():
    """Card cu <sup>99</sup> orfan + preturi reale -> deal valid (38% off), nu ghost."""
    deals, _ = _run_scraper_with_fixture(FIXTURE_HTML)
    phones = [d for d in deals if "flagship" in d["titlu"].lower()]
    assert len(phones) == 1, (
        f"Astept exact 1 deal 'Telefon flagship', am gasit {len(phones)}. "
        f"Toate: {[d['titlu'] for d in deals]}"
    )
    d = phones[0]
    # Preturile reale: 2411.17 si 3863.86 -> -38%
    assert abs(d["pret_redus"] - 2411.17) < 0.02, f"pret_redus={d['pret_redus']}"
    assert abs(d["pret_original"] - 3863.86) < 0.02, f"pret_original={d['pret_original']}"
    assert 35 <= d["procent_reducere"] <= 40, f"procent={d['procent_reducere']}"


def test_single_price_trap_card_dropped():
    """Card cu un singur pret real + <sup>99</sup> orfan -> DROPPED (len(prices)<2)."""
    deals, _ = _run_scraper_with_fixture(FIXTURE_HTML)
    small = [d for d in deals if "accesoriu" in d["titlu"].lower()]
    assert len(small) == 0, (
        f"Astept 0 deal-uri pt card cu un singur pret, am gasit {len(small)}: {small}"
    )


def test_extract_price_comma_decimal():
    """Sanity pe extract_price: virgula e separator zecimal (format RO)."""
    assert agm.extract_price("432,99 lei") == 432.99
    assert agm.extract_price("1.432,99 lei") == 1432.99  # . = mii, , = zecimale
    assert agm.extract_price("99") == 99.0
    assert agm.extract_price("") == 0


def test_discount_pct_helper():
    """Sanity pe discount_pct: returneaza 0 la input invalid, altfel rotunjit."""
    assert agm.discount_pct(500, 349.99) == 30
    assert agm.discount_pct(100, 50) == 50
    assert agm.discount_pct(3863.86, 2411.17) == 38
    assert agm.discount_pct(100, 150) == 0   # pret nou mai mare decat vechi
    assert agm.discount_pct(0, 10) == 0      # pret vechi invalid
    assert agm.discount_pct(100, 100) == 0   # fara reducere


def test_sup_preprocessing_normal_use():
    """Sanity pe preprocesare <sup>XX</sup> -> ','XX (prin parsing direct BS)."""
    from bs4 import BeautifulSoup
    html = '<div class="product_pret">432<sup>99</sup> lei</div>'
    soup = BeautifulSoup(html, "html.parser")
    card = soup
    # Reproducere pas preprocesare din fix
    for sup in card.find_all("sup"):
        sup_text = sup.get_text(strip=True)
        if sup_text.isdigit() and len(sup_text) <= 2:
            sup.string = "," + sup_text
    price_el = card.select_one(".product_pret")
    assert agm.extract_price(price_el.get_text(strip=True)) == 432.99


# ─── Standalone runner ─────────────────────────────────────────────

def _main():
    tests = [
        ("test_no_ghost_deal_from_orphan_sup_99", test_no_ghost_deal_from_orphan_sup_99),
        ("test_normal_evomag_card_parsed_correctly", test_normal_evomag_card_parsed_correctly),
        ("test_trap_card_with_orphan_sup_still_parses_real_prices",
         test_trap_card_with_orphan_sup_still_parses_real_prices),
        ("test_single_price_trap_card_dropped", test_single_price_trap_card_dropped),
        ("test_extract_price_comma_decimal", test_extract_price_comma_decimal),
        ("test_discount_pct_helper", test_discount_pct_helper),
        ("test_sup_preprocessing_normal_use", test_sup_preprocessing_normal_use),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  [OK]   {name}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERR]  {name}: {type(e).__name__}: {e}")
            failed += 1
    print()
    print(f"Rezultat: {passed} passed, {failed} failed (total {len(tests)})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_main())
