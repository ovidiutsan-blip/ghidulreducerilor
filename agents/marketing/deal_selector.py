"""
deal_selector.py — Selectează top deals de promovat zilnic.

Criterii de selecție:
- link_status == 'ok' (verificat live)
- activ == True
- procent_reducere >= 40%
- are imagine validă
- diversitate de magazine și categorii
- nu a fost promovat recent (cooldown 3 zile)
"""

import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

BASE = Path(__file__).parent.parent.parent
DEALS_PATH   = BASE / "data" / "deals.json"
PROMO_LOG    = BASE / "data" / "marketing" / "promo_log.json"

# ─── Config ───────────────────────────────────────────────────────────────────
MIN_DISCOUNT    = 40       # % minim reducere
TOP_N           = 8        # câte deals selectăm
COOLDOWN_DAYS   = 3        # zile până când același deal poate fi repromotat
MAX_PER_STORE   = 2        # max deals din același magazin în selecție


def load_deals() -> list[dict]:
    with open(DEALS_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_promo_log() -> dict:
    """Încarcă log-ul de deals deja promovate (id -> data_ultima_promovare)."""
    if PROMO_LOG.exists():
        with open(PROMO_LOG, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_promo_log(log: dict):
    PROMO_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(PROMO_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def score_deal(d: dict) -> float:
    """Scor de promovabilitate (mai mare = mai bun de promovat)."""
    score = 0.0
    pct = d.get("procent_reducere") or d.get("discount_percent") or 0
    score += pct * 1.5                              # reducere mare = prioritate
    if d.get("pret_redus", 9999) < 200:
        score += 20                                 # produse ieftine → conversii mai ușoare
    if d.get("imagine_url") or d.get("image"):
        score += 10                                 # imagine = post mai atrăgător
    if d.get("omnibus_validated"):
        score += 15                                 # reducere verificată Omnibus
    if pct >= 70:
        score += 25                                 # bonus pentru reduceri wow (70%+)
    return score


def select_top_deals(n: int = TOP_N) -> list[dict]:
    """Returnează top N deals de promovat azi, cu cooldown și diversitate."""
    deals = load_deals()
    promo_log = load_promo_log()
    cutoff = datetime.now() - timedelta(days=COOLDOWN_DAYS)

    eligible = []
    for d in deals:
        if not d.get("activ", True):
            continue
        if d.get("link_status") not in ("ok", None, ""):
            # permite și deals fără link_status (neverificate încă)
            if d.get("link_status") and d["link_status"] not in ("ok",):
                continue
        pct = d.get("procent_reducere") or d.get("discount_percent") or 0
        if pct < MIN_DISCOUNT:
            continue
        # Cooldown check
        last = promo_log.get(d.get("id", ""))
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                if last_dt > cutoff:
                    continue  # promovat prea recent
            except Exception:
                pass
        eligible.append(d)

    # Sortează după scor
    eligible.sort(key=score_deal, reverse=True)

    # Aplică limita per magazin (diversitate)
    selected = []
    store_count: dict[str, int] = defaultdict(int)
    for d in eligible:
        store = d.get("magazin") or d.get("store", "")
        if store_count[store] >= MAX_PER_STORE:
            continue
        selected.append(d)
        store_count[store] += 1
        if len(selected) >= n:
            break

    return selected


def mark_as_promoted(deal_ids: list[str]):
    """Marchează deals ca promovate azi."""
    log = load_promo_log()
    now = datetime.now().isoformat()
    for did in deal_ids:
        log[did] = now
    save_promo_log(log)


def format_deal_summary(d: dict) -> str:
    """Rezumat scurt pentru logging."""
    titlu = d.get("titlu") or d.get("title", "")
    store = d.get("magazin") or d.get("store", "")
    pct   = d.get("procent_reducere") or d.get("discount_percent") or 0
    pret  = d.get("pret_redus") or d.get("price") or 0
    return f"[{store}] {titlu[:50]} — -{pct}% → {pret} lei"


if __name__ == "__main__":
    deals = select_top_deals()
    print(f"Top {len(deals)} deals de promovat azi:\n")
    for d in deals:
        print(f"  {score_deal(d):.0f}p  {format_deal_summary(d)}")
