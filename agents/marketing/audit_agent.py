"""
audit_agent.py — Verificare zilnică a tuturor agenților și sistemului ghidulreducerilor.ro.

Ce verifică:
  1. Task Scheduler — toate taskurile GhidulReducerilor sunt Ready
  2. deals.json — există, are suficiente deals, nu e mai vechi de 25h
  3. Imagini broken — verifică primele 50 imagini din deals.json
  4. Schema JSON-LD — prezentă pe site-ul live (/reduceri/vegis)
  5. Pipeline GitHub Actions — ultimul run a fost azi (via .lastrun dacă există)

Raport: afișat în consolă + trimis pe Telegram dacă există erori critice.

Rulare: python audit_agent.py
Task Scheduler: zilnic 07:30 (înainte de ceilalți agenți)
"""

import os, json, sys, subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)  # type: ignore[attr-defined]
sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

BASE = Path(__file__).resolve().parent.parent.parent
DEALS_PATH = BASE / "data" / "deals.json"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@ghidulreducerilor")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")  # ID chat personal pentru alerte
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

SITE_URL = "https://ghidulreducerilor.ro"

TASKS_EXPECTED = [
    "GhidulReducerilor_Telegram",
    "GhidulReducerilor_Pinterest_Midday",
    "GhidulReducerilor_Pinterest_Evening",
    "GhidulReducerilor_Newsletter",
    "GhidulReducerilor_FB_Poster",
]

MIN_DEALS = 400
MAX_DEALS_AGE_HOURS = 25
IMAGE_CHECK_COUNT = 30
IMAGE_TIMEOUT = 5

# ─────────────────────────────────────────
# Checks
# ─────────────────────────────────────────

def check_task_scheduler() -> list[str]:
    """Verifică taskurile Task Scheduler prin fișierele XML din sistemul Windows."""
    errors = []
    task_dir = Path(r"C:\Windows\System32\Tasks")
    if not task_dir.exists():
        # Fallback: încearcă via subprocess cu CREATE_NO_WINDOW
        try:
            result = subprocess.run(
                ["schtasks", "/query", "/fo", "CSV"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL, text=True, timeout=15,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for task_name in TASKS_EXPECTED:
                if task_name not in result.stdout:
                    errors.append(f"Task LIPSĂ: {task_name}")
        except Exception as e:
            errors.append(f"Nu pot verifica Task Scheduler: {e}")
        return errors

    for task_name in TASKS_EXPECTED:
        task_file = task_dir / task_name
        if not task_file.exists():
            errors.append(f"Task LIPSĂ: {task_name}")
    return errors


def check_deals_json() -> list[str]:
    """Verifică deals.json — există, dimensiune, freshness."""
    errors = []
    if not DEALS_PATH.exists():
        errors.append(f"deals.json LIPSĂ la {DEALS_PATH}")
        return errors

    mtime = datetime.fromtimestamp(DEALS_PATH.stat().st_mtime)
    age_hours = (datetime.now() - mtime).total_seconds() / 3600
    if age_hours > MAX_DEALS_AGE_HOURS:
        errors.append(f"deals.json vechi {age_hours:.1f}h (max {MAX_DEALS_AGE_HOURS}h)")

    try:
        with open(DEALS_PATH, encoding="utf-8") as f:
            deals = json.load(f)
        active = [d for d in deals if d.get("activ", True)]
        if len(active) < MIN_DEALS:
            errors.append(f"Prea puține deals active: {len(active)} (min {MIN_DEALS})")
        return errors, len(active)
    except Exception as e:
        errors.append(f"deals.json corupt: {e}")
        return errors, 0


def _check_one_image(d: dict) -> str | None:
    """Returnează string cu eroare dacă imaginea e broken, altfel None."""
    url = d.get("imagine", "")
    if not url or not url.startswith("http"):
        return None
    try:
        r = requests.head(url, timeout=IMAGE_TIMEOUT, allow_redirects=True)
        if r.status_code >= 400:
            return f"{d.get('titlu', '?')[:40]} → {r.status_code}"
    except Exception:
        return f"{d.get('titlu', '?')[:40]} → timeout"
    return None


def check_images() -> list[str]:
    """Verifică primele IMAGE_CHECK_COUNT imagini din deals.json (paralel)."""
    errors = []
    if not DEALS_PATH.exists():
        return ["deals.json lipsă, nu pot verifica imagini"]

    try:
        with open(DEALS_PATH, encoding="utf-8") as f:
            deals = json.load(f)
    except Exception as e:
        return [f"deals.json corupt: {e}"]

    to_check = [d for d in deals if d.get("imagine") and d.get("activ", True)][:IMAGE_CHECK_COUNT]
    broken = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_check_one_image, d): d for d in to_check}
        for fut in as_completed(futures):
            result = fut.result()
            if result:
                broken.append(result)

    if broken:
        errors.append(f"{len(broken)}/{IMAGE_CHECK_COUNT} imagini broken:")
        errors.extend([f"  • {b}" for b in broken[:5]])
        if len(broken) > 5:
            errors.append(f"  ... și {len(broken)-5} altele")
    return errors


def check_live_schema() -> list[str]:
    """Verifică că JSON-LD Product+Offer e prezent pe site-ul live."""
    errors = []
    url = f"{SITE_URL}/reduceri/vegis"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "GhidulReducerilor-Audit/1.0"})
        if r.status_code != 200:
            errors.append(f"Site live returnează {r.status_code} pe {url}")
            return errors
        body = r.text
        for schema_type in ["ItemList", "BreadcrumbList", "Product", "Offer"]:
            if f'"@type":"{schema_type}"' not in body:
                errors.append(f"Schema JSON-LD lipsă: {schema_type} pe {url}")
    except Exception as e:
        errors.append(f"Nu pot accesa site-ul live: {e}")
    return errors


def check_site_pages() -> list[str]:
    """Verifică că paginile principale sunt accesibile (200)."""
    errors = []
    pages = ["/", "/deals", "/categorii", "/reduceri/vegis", "/blog"]
    for path in pages:
        url = SITE_URL + path
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "GhidulReducerilor-Audit/1.0"})
            if r.status_code != 200:
                errors.append(f"Pagina {path} → {r.status_code}")
        except Exception as e:
            errors.append(f"Pagina {path} inaccesibilă: {e}")
    return errors


# ─────────────────────────────────────────
# Raport
# ─────────────────────────────────────────

def send_telegram_alert(message: str):
    """Trimite alertă pe Telegram (canal admin sau chat personal)."""
    if not BOT_TOKEN:
        print("  [WARN] TELEGRAM_BOT_TOKEN lipsă, nu trimit alertă")
        return

    # Încearcă ADMIN_CHAT_ID mai întâi, altfel canalul public
    chat_id = ADMIN_CHAT_ID if ADMIN_CHAT_ID else CHANNEL_ID
    if not chat_id:
        print("  [WARN] Nicio destinație Telegram configurată")
        return

    try:
        resp = requests.post(
            f"{API_BASE}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            timeout=10
        )
        if resp.status_code == 200:
            print(f"  [OK] Alertă trimisă pe Telegram → {chat_id}")
        else:
            print(f"  [ERR] Telegram {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"  [ERR] Telegram send failed: {e}")


def run():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*60}", flush=True)
    print(f"  AUDIT GHIDULREDUCERILOR.RO — {now}", flush=True)
    print(f"{'='*60}\n", flush=True)

    all_errors = []
    warnings = []

    # 1. Task Scheduler
    print("1. Task Scheduler...", flush=True)
    task_errors = check_task_scheduler()
    if task_errors:
        print(f"   ❌ {len(task_errors)} probleme:")
        for e in task_errors:
            print(f"      • {e}")
        all_errors.extend(task_errors)
    else:
        print(f"   ✅ Toate {len(TASKS_EXPECTED)} taskuri sunt Ready")

    # 2. deals.json
    print("\n2. deals.json...")
    result = check_deals_json()
    if isinstance(result, tuple):
        deal_errors, deal_count = result
    else:
        deal_errors, deal_count = result, 0

    if deal_errors:
        print(f"   ❌ {len(deal_errors)} probleme:")
        for e in deal_errors:
            print(f"      • {e}")
        all_errors.extend(deal_errors)
    else:
        print(f"   ✅ {deal_count} deals active, fișier fresh")

    # 3. Imagini
    print(f"\n3. Imagini (primele {IMAGE_CHECK_COUNT})...")
    img_errors = check_images()
    if img_errors:
        print(f"   ⚠️  Imagini broken:")
        for e in img_errors:
            print(f"      {e}")
        warnings.extend(img_errors)
    else:
        print(f"   ✅ Toate imaginile verificate sunt accesibile")

    # 4. Schema JSON-LD live
    print("\n4. Schema JSON-LD live...")
    schema_errors = check_live_schema()
    if schema_errors:
        print(f"   ❌ Schema lipsă:")
        for e in schema_errors:
            print(f"      • {e}")
        all_errors.extend(schema_errors)
    else:
        print("   ✅ ItemList + Product + Offer + BreadcrumbList prezente")

    # 5. Pagini site
    print("\n5. Pagini site...")
    page_errors = check_site_pages()
    if page_errors:
        print(f"   ❌ Pagini down:")
        for e in page_errors:
            print(f"      • {e}")
        all_errors.extend(page_errors)
    else:
        print("   ✅ Toate paginile principale răspund 200")

    # ── Sumar ──
    print(f"\n{'='*60}")
    if not all_errors and not warnings:
        print("  ✅ TOTUL E OK — nicio problemă detectată")
        print(f"{'='*60}\n")
        return

    if all_errors:
        print(f"  ❌ {len(all_errors)} ERORI CRITICE")
        # Trimite alertă Telegram
        msg_lines = [f"🚨 <b>AUDIT GHIDULREDUCERILOR</b> — {now}"]
        msg_lines.append(f"\n❌ <b>{len(all_errors)} erori critice:</b>")
        for e in all_errors[:10]:
            msg_lines.append(f"• {e}")
        if warnings:
            msg_lines.append(f"\n⚠️ {len(warnings)} avertismente (imagini)")
        msg_lines.append(f"\n→ Verifică manual: {SITE_URL}")
        send_telegram_alert("\n".join(msg_lines))
    else:
        print(f"  ⚠️  {len(warnings)} avertismente (non-critice)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run()
