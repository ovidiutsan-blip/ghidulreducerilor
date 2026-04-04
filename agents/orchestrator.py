"""
Orchestrator — Ruleaza toti agentii in ordine si gestioneaza erorile

Utilizare:
  python agents/orchestrator.py              # Ruleaza toti agentii (fetch+process+publish+monitor)
  python agents/orchestrator.py fetch        # Doar fetcher
  python agents/orchestrator.py process      # Doar processor
  python agents/orchestrator.py publish      # Doar publisher
  python agents/orchestrator.py monitor      # Doar monitor
  python agents/orchestrator.py newsletter   # Trimite newsletter saptamanal
  python agents/orchestrator.py digest       # Trimite digest zilnic
  python agents/orchestrator.py reengagement # Trimite email re-engagement

Cron (Windows Task Scheduler sau Unix cron):
  0 6 * * * cd /path/to/ghidulreducerilor.ro && PYTHONIOENCODING=utf-8 python agents/orchestrator.py >> logs/cron.log 2>&1
  0 10 * * 5 cd /path/to/ghidulreducerilor.ro && PYTHONIOENCODING=utf-8 python agents/orchestrator.py newsletter >> logs/cron.log 2>&1
  0 8 * * 1-5 cd /path/to/ghidulreducerilor.ro && PYTHONIOENCODING=utf-8 python agents/orchestrator.py digest >> logs/cron.log 2>&1
"""

import sys
import json
import traceback
from datetime import datetime
from pathlib import Path

# Adauga directoarele la sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(BASE_DIR / "email"))

from fetcher_agent import run as run_fetcher
from processor_agent import run as run_processor
from publisher_agent import run as run_publisher
from monitor_agent import run as run_monitor

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")


def run_agent(name, func):
    """Ruleaza un agent cu error handling."""
    log(f"> Start: {name}")
    try:
        result = func()
        log(f"[OK] {name} -- completat cu succes")
        return True, result
    except Exception as e:
        log(f"[FAIL] {name} -- EROARE: {e}")
        traceback.print_exc()
        return False, None


def _load_deals():
    """Incarca ofertele din deals.json."""
    deals_file = BASE_DIR / "data" / "deals.json"
    if deals_file.exists():
        with open(deals_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _load_codes():
    """Incarca codurile promo din codes.json."""
    codes_file = BASE_DIR / "data" / "codes.json"
    if codes_file.exists():
        with open(codes_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def run_newsletter():
    """Trimite newsletter-ul saptamanal cu top oferte."""
    from email_sender import send_weekly_newsletter
    offers = _load_deals()
    codes = _load_codes()
    # Sorteaza dupa reducere descrescator
    offers.sort(key=lambda x: x.get("procent_reducere", 0), reverse=True)
    return send_weekly_newsletter(offers[:6], coduri_promo=codes[:3])


def run_digest():
    """Trimite digest-ul zilnic."""
    from email_sender import send_daily_digest
    offers = _load_deals()
    offers.sort(key=lambda x: x.get("procent_reducere", 0), reverse=True)
    return send_daily_digest(offers[:3])


def run_reengagement():
    """Trimite email de re-engagement."""
    from email_sender import send_email
    from renderer import render_reengagement
    offers = _load_deals()
    offers.sort(key=lambda x: x.get("procent_reducere", 0), reverse=True)
    # In productie, se extrage segmentul de inactivi din Brevo
    # Aici doar renderizam template-ul si logam
    html = render_reengagement(offers[:5])
    log("[EMAIL] Re-engagement template renderat. In productie, se trimite la segmentul de inactivi din Brevo.")
    return True


def _run_auto_update():
    """Ruleaza auto-update saptamanal."""
    sys.path.insert(0, str(BASE_DIR / "scripts"))
    from auto_update import run_auto_update
    return run_auto_update()


def _run_audit():
    """Ruleaza audit complet."""
    sys.path.insert(0, str(BASE_DIR / "scripts"))
    from audit_full import run_audit, save_report
    report = run_audit()
    save_report(report)
    return report


def _run_repair():
    """Ruleaza auto-repair cu aplicare."""
    sys.path.insert(0, str(BASE_DIR / "scripts"))
    from auto_repair import run_repairs
    return run_repairs(dry_run=False)


def main():
    start_time = datetime.now()
    log("=" * 60)
    log("ORCHESTRATOR -- GhidulReducerilor.ro")
    log("=" * 60)

    task = sys.argv[1] if len(sys.argv) > 1 else "all"

    # Agentii de baza
    agents = {
        "fetch": ("Fetcher Agent", run_fetcher),
        "process": ("Processor Agent", run_processor),
        "publish": ("Publisher Agent", run_publisher),
        "monitor": ("Monitor Agent", run_monitor),
    }

    # Task-uri email
    email_tasks = {
        "newsletter": ("Newsletter Saptamanal", run_newsletter),
        "digest": ("Digest Zilnic", run_digest),
        "reengagement": ("Re-engagement Email", run_reengagement),
    }

    # Task-uri de mentenanta
    maintenance_tasks = {
        "auto_update": ("Auto-Update Saptamanal", _run_auto_update),
        "audit": ("Audit Complet", _run_audit),
        "repair": ("Auto-Repair", _run_repair),
    }

    if task == "all":
        run_order = ["fetch", "process", "publish", "monitor"]
        task_map = agents
    elif task in agents:
        run_order = [task]
        task_map = agents
    elif task in email_tasks:
        run_order = [task]
        task_map = email_tasks
    elif task in maintenance_tasks:
        run_order = [task]
        task_map = maintenance_tasks
    else:
        log(f"Task necunoscut: {task}")
        all_tasks = list(agents.keys()) + list(email_tasks.keys()) + list(maintenance_tasks.keys())
        log(f"Optiuni: all, {', '.join(all_tasks)}")
        sys.exit(1)

    results = {}
    all_success = True

    for key in run_order:
        name, func = task_map[key]
        success, result = run_agent(name, func)
        results[key] = {"success": success, "result": result}
        if not success:
            all_success = False
            if key == "fetch" and "process" in run_order:
                log("[WARN] Fetcher a esuat dar processor va folosi datele anterioare")

    elapsed = (datetime.now() - start_time).total_seconds()
    log("-" * 60)
    log(f"SUMAR -- Timp total: {elapsed:.1f}s")

    for key in run_order:
        name = task_map[key][0]
        status = "[OK]" if results[key]["success"] else "[FAIL]"
        log(f"  {status} {name}")

    if all_success:
        log("[SUCCESS] Toate task-urile au rulat cu succes!")
    else:
        log("[WARN] Unele task-uri au avut erori -- verifica logurile")

    # Trimite raport zilnic pe email daca am rulat toti agentii
    if task == "all":
        try:
            sys.path.insert(0, str(BASE_DIR))
            from email_system.sender import EmailSender
            sender = EmailSender()
            offers = _load_deals()
            errors = sum(1 for r in results.values() if not r["success"])
            sender.send_system_report({
                "Oferte in deals.json": len(offers),
                "Agenti rulati": len(run_order),
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
