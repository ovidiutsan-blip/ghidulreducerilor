"""
performance_agent.py — Monitorizează performanța marketing-ului.

Urmărește:
- Click-uri pe /out/[id] (din click_log.json dacă există)
- Top deals după click-uri
- Surse de trafic (via UTM params în log)
- Comparație față de ziua anterioară

Output: data/marketing/performance_YYYY-MM-DD.json
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict

BASE        = Path(__file__).parent.parent.parent
CLICK_LOG   = BASE / "data" / "click_log.json"
DEALS_PATH  = BASE / "data" / "deals.json"
PERF_DIR    = BASE / "data" / "marketing"


def load_click_log() -> list[dict]:
    """Încarcă log-ul de click-uri (generat de /out/[id] route)."""
    if not CLICK_LOG.exists():
        return []
    with open(CLICK_LOG, encoding="utf-8") as f:
        return json.load(f)


def load_deals_map() -> dict:
    """Dict id -> deal."""
    with open(DEALS_PATH, encoding="utf-8") as f:
        deals = json.load(f)
    return {d.get("id", ""): d for d in deals}


def analyze(days_back: int = 7) -> dict:
    """Analiză completă a performanței pe ultimele N zile."""
    clicks = load_click_log()
    deals_map = load_deals_map()
    cutoff = (datetime.now() - timedelta(days=days_back)).isoformat()

    recent = [c for c in clicks if c.get("timestamp", "") >= cutoff]
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_clicks = [c for c in clicks if c.get("timestamp", "").startswith(today_str)]
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_clicks = [c for c in clicks if c.get("timestamp", "").startswith(yesterday_str)]

    # Top deals după click-uri (ultimele 7 zile)
    deal_counts = Counter(c.get("deal_id") for c in recent if c.get("deal_id"))
    top_deals = []
    for did, cnt in deal_counts.most_common(10):
        d = deals_map.get(did, {})
        top_deals.append({
            "deal_id":  did,
            "clicks":   cnt,
            "titlu":    d.get("titlu") or d.get("title", did),
            "magazin":  d.get("magazin") or d.get("store", ""),
            "pret":     d.get("pret_redus") or d.get("price"),
            "discount": d.get("procent_reducere") or d.get("discount_percent"),
        })

    # Surse de trafic
    sources = Counter(c.get("source", "direct") for c in recent)

    # Click-uri pe magazin
    by_store: dict[str, int] = defaultdict(int)
    for c in recent:
        did = c.get("deal_id", "")
        d = deals_map.get(did, {})
        store = d.get("magazin") or d.get("store", "unknown")
        by_store[store] += 1

    result = {
        "generated_at":       datetime.now().isoformat(),
        "period_days":        days_back,
        "total_clicks":       len(recent),
        "clicks_today":       len(today_clicks),
        "clicks_yesterday":   len(yesterday_clicks),
        "delta_vs_yesterday": len(today_clicks) - len(yesterday_clicks),
        "top_deals":          top_deals[:10],
        "clicks_by_source":   dict(sources.most_common(10)),
        "clicks_by_store":    dict(sorted(by_store.items(), key=lambda x: -x[1])[:10]),
        "insight":            _generate_insight(top_deals, sources, len(today_clicks), len(yesterday_clicks)),
    }
    return result


def _generate_insight(top_deals, sources, today, yesterday) -> str:
    """Generează un insight text scurt despre ce funcționează."""
    insights = []
    if top_deals:
        best = top_deals[0]
        insights.append(f"Deal-ul cu cele mai multe click-uri: '{best['titlu'][:40]}' ({best['clicks']} clicks)")
    if sources:
        top_src = max(sources.items(), key=lambda x: x[1])
        insights.append(f"Sursa principală de trafic: {top_src[0]} ({top_src[1]} clicks)")
    if today > yesterday:
        insights.append(f"Traficul a crescut față de ieri (+{today-yesterday} clicks)")
    elif today < yesterday:
        insights.append(f"Traficul a scăzut față de ieri ({today-yesterday} clicks)")
    return " | ".join(insights) if insights else "Date insuficiente pentru insight."


def save_report(data: dict) -> Path:
    PERF_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    out = PERF_DIR / f"performance_{today}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return out


def print_report(data: dict):
    print(f"\n📊 PERFORMANȚĂ MARKETING — {datetime.now().strftime('%Y-%m-%d')}")
    print(f"   Click-uri azi:     {data['clicks_today']}")
    print(f"   Click-uri ieri:    {data['clicks_yesterday']}")
    delta = data['delta_vs_yesterday']
    sign = "+" if delta >= 0 else ""
    print(f"   Variație:          {sign}{delta}")
    print(f"   Total {data['period_days']}z:       {data['total_clicks']}")
    if data['top_deals']:
        print(f"\n   Top deal:          {data['top_deals'][0]['titlu'][:45]} ({data['top_deals'][0]['clicks']} clicks)")
    print(f"\n   💡 {data['insight']}")


if __name__ == "__main__":
    report = analyze(days_back=7)
    path = save_report(report)
    print_report(report)
    print(f"\n   Salvat: {path}")
