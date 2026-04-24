"""
Orchestrator — Agent General care coordoneaza toti agentii

Flux principal (task "all" sau "scrape"):
  1. agent_emag.run()            → data/raw/emag_YYYY-MM-DD.json
  2. agent_altemagazine.run()    → data/raw/altemagazine_YYYY-MM-DD.json
  3. MERGE + VALIDARE            → data/raw/YYYY-MM-DD.json
  4. processor_agent.run()       → data/processed/YYYY-MM-DD.json
  5. publisher_agent.run()       → data/deals.json
  6. monitor_agent.run()         → health check

Utilizare:
  python agents/orchestrator.py              # Pipeline complet (scrape + process + publish + monitor)
  python agents/orchestrator.py scrape       # Doar scraping (agent_emag + agent_altemagazine + merge)
  python agents/orchestrator.py emag         # Doar agent eMAG
  python agents/orchestrator.py altemagazine # Doar agent alte magazine
  python agents/orchestrator.py process      # Doar processor
  python agents/orchestrator.py publish      # Doar publisher
  python agents/orchestrator.py monitor      # Doar monitor
  python agents/orchestrator.py newsletter   # Trimite newsletter saptamanal
  python agents/orchestrator.py digest       # Trimite digest zilnic

Cron:
  0 6 * * * cd /path/to/ghidulreducerilor.ro && python agents/orchestrator.py >> logs/cron.log 2>&1
"""

import sys
import json
import re
import traceback
from datetime import datetime
from pathlib import Path

# Adauga directoarele la sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(BASE_DIR / "email"))

LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")


def run_agent(name, func):
    """Ruleaza un agent cu error handling."""
    log(f"> Start: {name}")
    try:
        result = func()
        log(f"[OK] {name} — completat cu succes")
        return True, result
    except Exception as e:
        log(f"[FAIL] {name} — EROARE: {e}")
        traceback.print_exc()
        return False, None


# ─── Validare deals ──────────────────────────────────────────────────
def validate_deals(deals: list) -> list:
    """
    Valideaza si curata deals-urile inainte de procesare.
    Elimina deals cu probleme: fara link, fara imagine, self-referencing, etc.
    """
    valid = []
    issues = {"no_link": 0, "no_image": 0, "self_ref": 0, "no_title": 0, "duplicate": 0}
    seen_ids = set()

    for d in deals:
        deal_id = d.get("id", "")

        # Duplicate
        if deal_id in seen_ids:
            issues["duplicate"] += 1
            continue
        seen_ids.add(deal_id)

        # Titlu
        if not d.get("titlu") or len(d.get("titlu", "")) < 5:
            issues["no_title"] += 1
            continue

        # Link afiliat
        link = d.get("link_afiliat", "")
        if not link:
            issues["no_link"] += 1
            continue

        # Self-referencing links (ghidulreducerilor.ro/out/...)
        if re.search(r"ghidulreducerilor\.ro/out/", link):
            # Converteste inapoi la Profitshare daca posibil
            m = re.search(r"/out/(\d+)", link)
            if m:
                d["link_afiliat"] = f"https://l.profitshare.ro/l/{m.group(1)}"
            else:
                issues["self_ref"] += 1
                continue

        # Imagine
        if not d.get("imagine_url"):
            issues["no_image"] += 1
            continue

        valid.append(d)

    # Log issues
    total_issues = sum(issues.values())
    if total_issues > 0:
        log(f"  Validare: {total_issues} probleme gasite")
        for k, v in issues.items():
            if v > 0:
                log(f"    {k}: {v}")

    log(f"  Validare: {len(valid)}/{len(deals)} deals valide")
    return valid


# ─── Merge raw outputs ───────────────────────────────────────────────
def merge_and_save_raw(emag_deals: list, other_deals: list) -> list:
    """Combina, valideaza si salveaza outputul combinat."""
    today = datetime.now().strftime("%Y-%m-%d")

    all_deals = (emag_deals or []) + (other_deals or [])
    log(f"  Merge: {len(emag_deals or [])} eMAG + {len(other_deals or [])} alte magazine = {len(all_deals)} total")

    # Validare
    all_deals = validate_deals(all_deals)

    # Sorteaza dupa discount descrescator
    all_deals.sort(key=lambda d: d.get("procent_reducere", 0), reverse=True)

    # Salveaza raw combinat
    output_file = RAW_DIR / f"{today}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_deals, f, ensure_ascii=False, indent=2)
    log(f"  Salvat raw combinat: {output_file} ({len(all_deals)} deals)")

    return all_deals


# ─── Scraping complet ────────────────────────────────────────────────
def run_scrape():
    """Ruleaza ambii agenti de scraping + merge + validare."""
    from agent_emag import run as run_emag
    from agent_altemagazine import run as run_altemagazine

    # Agent eMAG
    emag_ok, emag_deals = run_agent("Agent eMAG", run_emag)

    # Agent Alte Magazine
    other_ok, other_deals = run_agent("Agent Alte Magazine", run_altemagazine)

    # Daca ambii au esuat, nu suprascriem nimic
    if not emag_ok and not other_ok:
        log("[WARN] Ambii agenti au esuat — se pastreaza datele existente")
        return False, []

    # Merge si validare
    merged = merge_and_save_raw(
        emag_deals if emag_ok else [],
        other_deals if other_ok else [],
    )

    return True, merged


# ─── Task-uri existente ──────────────────────────────────────────────
def _load_deals():
    deals_file = BASE_DIR / "data" / "deals.json"
    if deals_file.exists():
        with open(deals_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _load_codes():
    codes_file = BASE_DIR / "data" / "codes.json"
    if codes_file.exists():
        with open(codes_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def run_newsletter():
    from email_sender import send_weekly_newsletter
    offers = _load_deals()
    codes = _load_codes()
    offers.sort(key=lambda x: x.get("procent_reducere", 0), reverse=True)
    return send_weekly_newsletter(offers[:6], coduri_promo=codes[:3])


def run_digest():
    from email_sender import send_daily_digest
    offers = _load_deals()
    offers.sort(key=lambda x: x.get("procent_reducere", 0), reverse=True)
    return send_daily_digest(offers[:3])


def run_reengagement():
    from email_sender import send_email
    from renderer import render_reengagement
    offers = _load_deals()
    offers.sort(key=lambda x: x.get("procent_reducere", 0), reverse=True)
    html = render_reengagement(offers[:5])
    log("[EMAIL] Re-engagement template renderat.")
    return True


# ─── Main ─────────────────────────────────────────────────────────
def main():
    start_time = datetime.now()
    log("=" * 60)
    log("ORCHESTRATOR — GhidulReducerilor.ro")
    log("=" * 60)

    task = sys.argv[1] if len(sys.argv) > 1 else "all"

    # Import agents
    from processor_agent import run as run_processor
    from publisher_agent import run as run_publisher
    from monitor_agent import run as run_monitor

    results = {}
    all_success = True

    if task == "all":
        # Pipeline complet: scrape → process → publish → monitor
        scrape_ok, merged = run_scrape()
        results["scrape"] = {"success": scrape_ok}
        if not scrape_ok:
            all_success = False

        for key, name, func in [
            ("process", "Processor Agent", run_processor),
            ("publish", "Publisher Agent", run_publisher),
            ("monitor", "Monitor Agent", run_monitor),
        ]:
            success, result = run_agent(name, func)
            results[key] = {"success": success, "result": result}
            if not success:
                all_success = False

    elif task == "scrape":
        scrape_ok, merged = run_scrape()
        results["scrape"] = {"success": scrape_ok}
        if not scrape_ok:
            all_success = False

    elif task == "emag":
        from agent_emag import run as run_emag
        success, result = run_agent("Agent eMAG", run_emag)
        results["emag"] = {"success": success}
        if not success:
            all_success = False

    elif task == "altemagazine":
        from agent_altemagazine import run as run_altemagazine
        success, result = run_agent("Agent Alte Magazine", run_altemagazine)
        results["altemagazine"] = {"success": success}
        if not success:
            all_success = False

    elif task == "process":
        success, result = run_agent("Processor Agent", run_processor)
        results["process"] = {"success": success}
        if not success:
            all_success = False

    elif task == "publish":
        success, result = run_agent("Publisher Agent", run_publisher)
        results["publish"] = {"success": success}
        if not success:
            all_success = False

    elif task == "monitor":
        success, result = run_agent("Monitor Agent", run_monitor)
        results["monitor"] = {"success": success}
        if not success:
            all_success = False

    elif task == "newsletter":
        success, result = run_agent("Newsletter Saptamanal", run_newsletter)
        results["newsletter"] = {"success": success}
        if not success:
            all_success = False

    elif task == "digest":
        success, result = run_agent("Digest Zilnic", run_digest)
        results["digest"] = {"success": success}
        if not success:
            all_success = False

    elif task == "reengagement":
        success, result = run_agent("Re-engagement Email", run_reengagement)
        results["reengagement"] = {"success": success}
        if not success:
            all_success = False

    else:
        log(f"Task necunoscut: {task}")
        log("Optiuni: all, scrape, emag, altemagazine, process, publish, monitor, newsletter, digest, reengagement")
        sys.exit(1)

    elapsed = (datetime.now() - start_time).total_seconds()
    log("-" * 60)
    log(f"SUMAR — Timp total: {elapsed:.1f}s")

    for key, info in results.items():
        status = "[OK]" if info["success"] else "[FAIL]"
        log(f"  {status} {key}")

    if all_success:
        log("[SUCCESS] Toate task-urile au rulat cu succes!")
    else:
        log("[WARN] Unele task-uri au avut erori — verifica logurile")

    # Trimite raport pe email daca am rulat pipeline complet
    if task == "all":
        try:
            sys.path.insert(0, str(BASE_DIR))
            from email_system.sender import EmailSender
            sender = EmailSender()
            offers = _load_deals()
            errors = sum(1 for r in results.values() if not r["success"])

            # Rezumat pe magazine
            stores = {}
            for d in offers:
                s = d.get("magazin", "unknown")
                stores[s] = stores.get(s, 0) + 1
            store_summary = ", ".join(f"{s}: {c}" for s, c in sorted(stores.items()))

            sender.send_system_report({
                "Oferte in deals.json": len(offers),
                "Magazine": store_summary,
                "Agenti rulati": len(results),
                "Erori": errors,
                "Durata rulare": f"{elapsed:.1f} secunde",
                "Status": "[OK]" if all_success else f"[WARN] {errors} erori",
            })
        except Exception as e:
            log(f"[WARN] Nu am putut trimite raport email: {e}")

    log("=" * 60)
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
