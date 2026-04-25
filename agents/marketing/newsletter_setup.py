"""
newsletter_setup.py — Setup și verificare Brevo pentru newsletter GhidulReducerilor.

Rulează O SINGURĂ DATĂ după ce ai configurat BREVO_API_KEY în .env.
Verifică API key, afișează senders disponibili, testează trimiterea unui email,
și configurează Task Scheduler pentru vineri la 08:00.

Utilizare:
    python newsletter_setup.py
"""

import os
import sys
import requests
import subprocess
from pathlib import Path
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

BREVO_API_KEY   = os.getenv("BREVO_API_KEY", "")
BREVO_LIST_ID   = int(os.getenv("BREVO_LIST_NEWSLETTER", os.getenv("BREVO_LIST_ID", "3")))
TEST_EMAIL      = os.getenv("BREVO_TEST_EMAIL", os.getenv("USER_EMAIL", "ovidiutsan@gmail.com"))
SENDER_EMAIL    = os.getenv("BREVO_SENDER_REDUCERI", "reduceri@ghidulreducerilor.ro")
SITE_BASE       = "https://ghidulreducerilor.ro"

HEADERS = {
    "api-key":      BREVO_API_KEY,
    "Content-Type": "application/json",
    "Accept":       "application/json",
}


def check_api_key() -> dict | None:
    """Verifică că API key-ul e valid și returnează info cont."""
    if not BREVO_API_KEY:
        print("❌ BREVO_API_KEY lipsă în .env!")
        print("   Mergi la https://app.brevo.com → Settings → API Keys → Create API key")
        return None

    r = requests.get("https://api.brevo.com/v3/account", headers=HEADERS, timeout=10)
    if r.status_code == 200:
        acct = r.json()
        plan = acct.get("plan", [{}])
        print(f"✅ Brevo API Key valid!")
        print(f"   Cont: {acct.get('email', '?')}")
        print(f"   Plan: {acct.get('companyName', 'N/A')}")
        return acct
    else:
        print(f"❌ API Key invalid: {r.status_code} — {r.text[:200]}")
        return None


def check_senders() -> bool:
    """Verifică senders configurați."""
    r = requests.get("https://api.brevo.com/v3/senders", headers=HEADERS, timeout=10)
    if r.status_code != 200:
        print(f"⚠️  Nu pot citi senders: {r.status_code}")
        return False

    senders = r.json().get("senders", [])
    print(f"\n📧 Senders disponibili ({len(senders)}):")
    found = False
    for s in senders:
        active = "✅" if s.get("active") else "⚠️"
        print(f"   {active} {s.get('email')} — {s.get('name', '')}")
        if s.get("email") == SENDER_EMAIL and s.get("active"):
            found = True

    if not found:
        print(f"\n⚠️  Sender-ul '{SENDER_EMAIL}' nu e activ sau verificat.")
        print(f"   Mergi la Brevo → Senders & IP → Add a New Sender")
        print(f"   Sau schimbă BREVO_SENDER_REDUCERI în .env")
    else:
        print(f"\n✅ Sender principal '{SENDER_EMAIL}' activ!")

    return found


def check_or_create_list() -> int | None:
    """Verifică sau creează lista de abonați."""
    # Verifică dacă lista există
    r = requests.get(f"https://api.brevo.com/v3/contacts/lists/{BREVO_LIST_ID}",
                     headers=HEADERS, timeout=10)
    if r.status_code == 200:
        lst = r.json()
        print(f"\n✅ Lista Brevo găsită: '{lst.get('name')}' (ID={BREVO_LIST_ID}) — {lst.get('totalSubscribers', 0)} abonați")
        return BREVO_LIST_ID
    elif r.status_code == 404:
        print(f"\n⚠️  Lista ID={BREVO_LIST_ID} nu există — creez una nouă...")
        payload = {"name": "Newsletter GhidulReducerilor", "folderId": 1}
        r2 = requests.post("https://api.brevo.com/v3/contacts/lists",
                           headers=HEADERS, json=payload, timeout=10)
        if r2.status_code in (200, 201):
            new_id = r2.json().get("id")
            print(f"✅ Listă creată: ID={new_id}")
            print(f"   Actualizează .env: BREVO_LIST_NEWSLETTER={new_id}")
            return new_id
        else:
            print(f"❌ Eroare creare listă: {r2.text[:200]}")
            return None
    else:
        print(f"⚠️  Eroare verificare listă: {r.status_code}")
        return None


def send_test_email(list_id: int) -> bool:
    """Trimite email de test la adresa configurată."""
    print(f"\n📤 Trimit email test la {TEST_EMAIL}...")

    html = f"""<!DOCTYPE html>
<html lang="ro">
<head><meta charset="UTF-8" /></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px;">
  <table width="600" style="background:#fff;border-radius:12px;overflow:hidden;margin:0 auto;">
    <tr><td style="background:#1D3557;padding:24px 32px;">
      <span style="color:#F4A261;font-size:22px;font-weight:bold;">GhidulReducerilor.ro</span>
    </td></tr>
    <tr><td style="padding:28px 32px;">
      <h2 style="color:#1D3557;">✅ Newsletter configurat cu succes!</h2>
      <p style="color:#555;line-height:1.6;">
        Dacă primești acest email, înseamnă că newsletter-ul funcționează corect.<br/><br/>
        În fiecare <strong>vineri la 08:00</strong> vei primi automat top reduceri din România.
      </p>
      <a href="{SITE_BASE}" style="display:inline-block;margin-top:16px;background:#F4A261;color:white;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">
        Vizitează GhidulReducerilor.ro →
      </a>
    </td></tr>
    <tr><td style="background:#f9f9f9;padding:14px 32px;border-top:1px solid #eee;">
      <p style="margin:0;font-size:12px;color:#aaa;text-align:center;">
        Email de test — <a href="{SITE_BASE}" style="color:#F4A261;">ghidulreducerilor.ro</a>
      </p>
    </td></tr>
  </table>
</body>
</html>"""

    payload = {
        "sender":      {"name": "GhidulReducerilor.ro", "email": SENDER_EMAIL},
        "to":          [{"email": TEST_EMAIL}],
        "replyTo":     {"email": "contact@ghidulreducerilor.ro"},
        "subject":     "✅ [TEST] Newsletter GhidulReducerilor — funcționează!",
        "htmlContent": html,
    }
    r = requests.post("https://api.brevo.com/v3/smtp/email",
                      headers=HEADERS, json=payload, timeout=15)
    if r.status_code in (200, 201):
        msg_id = r.json().get("messageId", "?")
        print(f"✅ Email test trimis! (messageId: {msg_id})")
        print(f"   Verifică inbox-ul: {TEST_EMAIL}")
        return True
    else:
        print(f"❌ Eroare trimitere test: {r.status_code} — {r.text[:300]}")
        if "sender" in r.text.lower() or "domain" in r.text.lower():
            print("\n   💡 Posibil sender neverificat. Mergi la:")
            print("      https://app.brevo.com/senders/list")
            print("      Adaugă și verifică sender-ul: " + SENDER_EMAIL)
        return False


def setup_task_scheduler() -> bool:
    """Configurează Task Scheduler: vineri la 08:00."""
    script_path = Path(__file__).parent / "newsletter_agent.py"
    python_path = sys.executable

    task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-05-01T08:00:00</StartBoundary>
      <ScheduleByWeek>
        <WeeksInterval>1</WeeksInterval>
        <DaysOfWeek>
          <Friday />
        </DaysOfWeek>
      </ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>{python_path}</Command>
      <Arguments>"{script_path}"</Arguments>
      <WorkingDirectory>{script_path.parent}</WorkingDirectory>
    </Exec>
  </Actions>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
  </Settings>
</Task>"""

    import tempfile
    xml_file = Path(tempfile.gettempdir()) / "newsletter_task.xml"
    xml_file.write_text(task_xml, encoding="utf-16")

    result = subprocess.run(
        ["schtasks", "/Create", "/TN", "GhidulReducerilor_Newsletter",
         "/XML", str(xml_file), "/F"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✅ Task Scheduler configurat: vineri la 08:00")
        print("   Task: GhidulReducerilor_Newsletter")
        return True
    else:
        print(f"⚠️  Task Scheduler eroare: {result.stderr.strip()}")
        print(f"   Adaugă manual: {python_path} \"{script_path}\" — vineri 08:00")
        return False


if __name__ == "__main__":
    print("=" * 55)
    print("  SETUP NEWSLETTER — ghidulreducerilor.ro")
    print("=" * 55)

    # 1. Verifică API Key
    acct = check_api_key()
    if not acct:
        sys.exit(1)

    # 2. Verifică senders
    check_senders()

    # 3. Verifică / creează lista
    list_id = check_or_create_list()
    if not list_id:
        print("\n⚠️  Continuăm fără verificarea listei...")

    # 4. Trimite email test
    print("\n--- Email test ---")
    email_ok = send_test_email(list_id or BREVO_LIST_ID)

    # 5. Task Scheduler
    print("\n--- Task Scheduler ---")
    task_ok = setup_task_scheduler()

    # Sumar
    print("\n" + "=" * 55)
    if email_ok:
        print("✅ SETUP COMPLET!")
    else:
        print("⚠️  SETUP PARȚIAL (email test nu a mers)")
    print(f"   API Key: ✅")
    print(f"   Email test: {'✅' if email_ok else '❌'} ({TEST_EMAIL})")
    print(f"   Task Scheduler: {'✅' if task_ok else '⚠️'} (vineri 08:00)")
    print(f"\n   Test manual: python newsletter_agent.py test")
    print(f"   Dry-run:     python newsletter_agent.py --dry")
    print(f"   Trimite:     python newsletter_agent.py")
    print("=" * 55)
