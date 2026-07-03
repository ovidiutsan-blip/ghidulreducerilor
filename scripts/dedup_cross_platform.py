#!/usr/bin/env python3
"""
Cross-Platform Dedup — GhidulReducerilor.ro
============================================
Detecteaza si elimina dealuri duplicate cu acelasi product_url importate
din surse diferite (profitshare + 2performant).

Regula: pentru fiecare product_url cu mai multe dealuri ACTIVE, pastreaza
cel cu procent_reducere maxim; celelalte primesc activ=false + expired_reason=dedup.

Utilizare:
  python scripts/dedup_cross_platform.py           # aplica dedup
  python scripts/dedup_cross_platform.py --dry-run # raporteaza fara sa scrie
"""
from __future__ import annotations
import json, sys, argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict

BASE       = Path(__file__).resolve().parent.parent
DEALS_PATH = BASE / "data" / "deals.json"


def run_dedup(dry_run: bool = False) -> dict:
    with open(DEALS_PATH, encoding="utf-8") as f:
        deals = json.load(f)

    # Grupeaza dealuri ACTIVE dupa product_url
    active_by_url: dict[str, list[int]] = defaultdict(list)
    for idx, d in enumerate(deals):
        if d.get("activ", True) and d.get("product_url"):
            active_by_url[d["product_url"]].append(idx)

    # Gaseste URL-uri cu mai mult de un deal activ
    duplicates = {url: idxs for url, idxs in active_by_url.items() if len(idxs) > 1}

    removed = 0
    log_lines = []

    for url, idxs in duplicates.items():
        group = [(idx, deals[idx]) for idx in idxs]
        # Sorteaza descrescator dupa procent_reducere; la egalitate prefer 2performant (mai fiabil)
        group.sort(key=lambda x: (
            -(x[1].get("procent_reducere") or 0),
            0 if (x[1].get("sursa") or "") == "2performant" else 1
        ))
        keeper_idx, keeper = group[0]
        losers = group[1:]

        sources = [d.get("sursa", "?") for _, d in group]
        log_lines.append(
            f"  DUP url={url[:70]} | surse={sources} | "
            f"pastrez id={keeper.get('id')} ({keeper.get('sursa')}, {keeper.get('procent_reducere')}%)"
        )

        for lose_idx, loser in losers:
            log_lines.append(
                f"    -> dezactiveaza id={loser.get('id')} ({loser.get('sursa')}, {loser.get('procent_reducere')}%)"
            )
            if not dry_run:
                deals[lose_idx]["activ"]          = False
                deals[lose_idx]["is_active"]       = False
                deals[lose_idx]["expired_at"]      = datetime.utcnow().strftime("%Y-%m-%d")
                deals[lose_idx]["expired_reason"]  = "dedup_cross_platform"
            removed += 1

    # Afiseaza raport
    tag = "[DRY-RUN] " if dry_run else ""
    print(f"{tag}Cross-platform dedup: {len(duplicates)} URL-uri duplicate, {removed} dealuri dezactivate")
    for line in log_lines:
        print(line)

    if not dry_run and removed > 0:
        deals.sort(key=lambda x: (not x.get("activ", True), -(x.get("procent_reducere") or 0)))
        with open(DEALS_PATH, "w", encoding="utf-8") as f:
            json.dump(deals, f, indent=2, ensure_ascii=False)
        print(f"Scris {DEALS_PATH} ({len(deals)} dealuri total)")

    return {"duplicates": len(duplicates), "removed": removed, "dry_run": dry_run}


def run_dedup_intra_store(dry_run: bool = False) -> dict:
    """Dedup intra-store: acelasi magazin + titlu identic (normalizat) + acelasi
    pret_redus = duplicat (ex: watch24 cu 3 carduri identice, novodoors cu
    part_number diferit dar acelasi produs). Pastreaza cel mai recent adaugat.
    """
    with open(DEALS_PATH, encoding="utf-8") as f:
        deals = json.load(f)

    groups: dict[tuple, list[int]] = defaultdict(list)
    for idx, d in enumerate(deals):
        if not d.get("activ", True):
            continue
        titlu = (d.get("titlu") or "").strip().lower()
        if not titlu:
            continue
        key = (d.get("magazin"), titlu, d.get("pret_redus"))
        groups[key].append(idx)

    duplicates = {k: idxs for k, idxs in groups.items() if len(idxs) > 1}
    removed = 0
    log_lines = []

    for key, idxs in duplicates.items():
        group = [(idx, deals[idx]) for idx in idxs]
        # Pastreaza cel mai recent (data_adaugare desc), tiebreak procent_reducere desc
        group.sort(key=lambda x: (
            str(x[1].get("data_adaugare") or ""),
            x[1].get("procent_reducere") or 0,
        ), reverse=True)
        keeper_idx, keeper = group[0]
        log_lines.append(f"  DUP-STORE {key[0]} | {key[1][:60]} | pastrez id={keeper.get('id')}")
        for lose_idx, loser in group[1:]:
            log_lines.append(f"    -> dezactiveaza id={loser.get('id')}")
            if not dry_run:
                deals[lose_idx]["activ"]          = False
                deals[lose_idx]["is_active"]       = False
                deals[lose_idx]["expired_at"]      = datetime.utcnow().strftime("%Y-%m-%d")
                deals[lose_idx]["expired_reason"]  = "dedup_intra_store"
            removed += 1

    tag = "[DRY-RUN] " if dry_run else ""
    print(f"{tag}Intra-store dedup: {len(duplicates)} grupuri duplicate, {removed} dealuri dezactivate")
    for line in log_lines:
        print(line)

    if not dry_run and removed > 0:
        deals.sort(key=lambda x: (not x.get("activ", True), -(x.get("procent_reducere") or 0)))
        with open(DEALS_PATH, "w", encoding="utf-8") as f:
            json.dump(deals, f, indent=2, ensure_ascii=False)
        print(f"Scris {DEALS_PATH} ({len(deals)} dealuri total)")

    return {"duplicates": len(duplicates), "removed": removed, "dry_run": dry_run}


def main():
    parser = argparse.ArgumentParser(description="Dedup cross-platform (PS+2P) + intra-store")
    parser.add_argument("--dry-run", action="store_true", help="Raporteaza fara a scrie")
    args = parser.parse_args()
    run_dedup(dry_run=args.dry_run)
    run_dedup_intra_store(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
