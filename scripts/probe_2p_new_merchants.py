# -*- coding: utf-8 -*-
"""Probă old_price pentru merchants 2P nou-aprobați, ÎNAINTE de activare.

Regula (memorie 2026-07-08): feed-urile 2P de tip catalog (fashion/mobilier/
farmacie) tind să NU aibă old_price => 0 deal-uri structural + fetch-uri
risipite zilnic. Lecția otter (2026-07-14): pagina 1 (bestsellers) poate fi
FĂRĂ old_price deși mijlocul feed-ului e 20/20 CU old_price — de aceea probăm
pagina 1, mijlocul și finalul feed-ului, prin exact calea de producție
(product_to_deal), nu printr-o reimplementare.

Utilizare (necesită TWO_PERFORMANT_EMAIL/PASSWORD — rulează în CI):
  python scripts/probe_2p_new_merchants.py gsmnet bonami ginissima lumaro petmart
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agents"))

from two_performant_session import api_get, TwoPerformantRateLimited  # noqa: E402
from two_performant_to_deals import (  # noqa: E402
    get_all_feeds, get_feed_products_page, product_to_deal,
)

PER_PAGE = 50
MIN_PCT = 10


def fetch_accepted_programs() -> list[dict]:
    programs: list[dict] = []
    for page in range(1, 6):
        data = api_get("affiliate/programs", params={"per_page": 100, "page": page})
        batch = data.get("programs") or (data if isinstance(data, list) else [])
        if not batch:
            break
        programs.extend(batch)
        if len(batch) < 100:
            break
    return programs


def match_program(programs: list[dict], slug: str) -> dict | None:
    slug_l = slug.lower()
    for p in programs:
        haystack = f"{p.get('name', '')} {p.get('main_url', '')} {p.get('base_url', '')}".lower()
        if slug_l in haystack:
            return p
    return None


def probe_feed(feed: dict, slug: str) -> dict:
    """Probează pagina 1 + mijloc + final; returnează statistici agregate."""
    fid = feed["id"]
    count = int(feed.get("products_count") or 0)
    total_pages = max(1, (count + PER_PAGE - 1) // PER_PAGE)
    pages = sorted({1, max(1, total_pages // 2), total_pages})

    stats = {"raw": 0, "eligibile": 0, "rejects": {}}
    for page in pages:
        try:
            data = get_feed_products_page(fid, page=page, per_page=PER_PAGE)
        except TwoPerformantRateLimited:
            raise
        except Exception as e:
            print(f"    pagina {page}: EROARE {e}")
            continue
        products = (data.get("products") or data.get("items") or
                    data.get("data") or (data if isinstance(data, list) else []))
        rejects: dict[str, int] = {}
        hits = 0
        for p in products:
            deal = product_to_deal(p, slug, "PROBE", "probe", None, reject_stats=rejects)
            if deal and deal["procent_reducere"] >= MIN_PCT:
                hits += 1
        stats["raw"] += len(products)
        stats["eligibile"] += hits
        for k, v in rejects.items():
            stats["rejects"][k] = stats["rejects"].get(k, 0) + v
        detail = ", ".join(f"{k}={v}" for k, v in sorted(rejects.items())) or "—"
        print(f"    pagina {page}/{total_pages}: {len(products)} produse, "
              f"{hits} eligibile (>= {MIN_PCT}%), respinse: {detail}")
    return stats


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    slugs = [s.strip().lower() for s in sys.argv[1:] if s.strip()]
    if not slugs:
        print("Utilizare: probe_2p_new_merchants.py <slug> [slug...]")
        sys.exit(1)

    print("=== Probă old_price merchants 2P noi ===")
    programs = fetch_accepted_programs()
    print(f"Programe vizibile: {len(programs)}\n")

    verdicts: list[str] = []
    for slug in slugs:
        prog = match_program(programs, slug)
        if not prog:
            print(f"[{slug}] NU am găsit programul în listă — sari peste.\n")
            verdicts.append(f"{slug}: NEGĂSIT în programe")
            continue
        uc = prog.get("unique_code", "?")
        aff = (prog.get("affrequest") or {}).get("status") or "?"
        print(f"[{slug}] {prog.get('name')} | unique_code={uc} | aff={aff}")

        feeds = [f for f in get_all_feeds()
                 if (f.get("program") or {}).get("unique_code") == uc]
        if not feeds:
            print(f"[{slug}] 0 feed-uri de produse => INUTILIZABIL ca sursă de deal-uri.\n")
            verdicts.append(f"{slug}: unique_code={uc}, FĂRĂ FEED")
            continue

        total = {"raw": 0, "eligibile": 0}
        for feed in feeds[:2]:
            print(f"  Feed '{feed.get('name')}' (id={feed['id']}, "
                  f"products_count={feed.get('products_count')})")
            s = probe_feed(feed, slug)
            total["raw"] += s["raw"]
            total["eligibile"] += s["eligibile"]

        if total["eligibile"] > 0:
            verdict = (f"{slug}: unique_code={uc}, ACTIVABIL — "
                       f"{total['eligibile']}/{total['raw']} eligibile în probă")
        else:
            verdict = (f"{slug}: unique_code={uc}, NEACTIVABIL — "
                       f"0/{total['raw']} eligibile (probabil fără old_price)")
        print(f"  => {verdict}\n")
        verdicts.append(verdict)

    print("=== VERDICTE ===")
    for v in verdicts:
        print(" -", v)


if __name__ == "__main__":
    main()
