"""
telegram_setup.py — Setup automat canal Telegram + verificare bot.

Rulează O SINGURĂ DATĂ după ce ai token-ul de la @BotFather.
Verifică token, afișează link-ul canalului, testează postarea.

Utilizare:
    python telegram_setup.py
"""

import os, sys, requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@ghidulreducerilor")


def check_token():
    if not BOT_TOKEN:
        print("\n❌ TELEGRAM_BOT_TOKEN lipsește din .env\n")
        print("Pași pentru a crea bot-ul (durează 2 minute):")
        print("  1. Deschide Telegram (app telefon sau web.telegram.org)")
        print("  2. Caută @BotFather")
        print("  3. Scrie: /newbot")
        print("  4. Dă un nume: Ghidul Reducerilor")
        print("  5. Dă un username: ghidulreducerilorbot")
        print("  6. Copiază token-ul primit (format: 123456789:ABCdef...)")
        print("  7. Adaugă în fișierul .env din repo:")
        print("     TELEGRAM_BOT_TOKEN=<token_tău>")
        print("  8. Rulează din nou: python telegram_setup.py")
        return None

    r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=10).json()
    if not r.get("ok"):
        print(f"❌ Token invalid: {r.get('description', 'unknown error')}")
        return None

    bot = r["result"]
    print(f"✅ Bot: @{bot['username']} ({bot['first_name']})")
    return bot["username"]


def check_channel(bot_username):
    """Verifică dacă botul e admin pe canal."""
    r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getChat",
                     params={"chat_id": CHANNEL_ID}, timeout=10).json()
    if not r.get("ok"):
        print(f"\n⚠️  Canal '{CHANNEL_ID}' negăsit sau bot fără acces.")
        print("\nPași pentru a crea canalul și adăuga bot-ul:")
        print(f"  1. Deschide Telegram → Nou Canal")
        print(f"  2. Nume: Ghidul Reducerilor")
        print(f"  3. Username (public): ghidulreducerilor")
        print(f"     → URL va fi: t.me/ghidulreducerilor")
        print(f"  4. Setări canal → Administratori → Adaugă @{bot_username}")
        print(f"  5. Dă-i permisiunea: Post Messages ✅")
        print(f"  6. Actualizează .env:")
        print(f"     TELEGRAM_CHANNEL_ID=@ghidulreducerilor")
        print(f"  7. Rulează din nou: python telegram_setup.py")
        return False

    chat = r["result"]
    print(f"✅ Canal găsit: {chat.get('title', CHANNEL_ID)} ({chat.get('type','')})")

    # Verifica daca botul e admin
    r2 = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember",
                      params={"chat_id": CHANNEL_ID,
                              "user_id": requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe").json()["result"]["id"]},
                      timeout=10).json()
    if r2.get("ok"):
        status = r2["result"].get("status", "")
        if status in ("administrator", "creator"):
            print(f"✅ Bot este admin pe canal (status: {status})")
            return True
        else:
            print(f"⚠️  Bot nu e admin (status: {status})")
            print(f"   Adaugă @{bot_username} ca administrator pe {CHANNEL_ID}")
            return False
    return False


def send_test_message():
    """Trimite mesaj test pe canal."""
    text = (
        "🎉 <b>Canal activat!</b>\n\n"
        "👋 Bun venit pe canalul oficial <b>Ghidul Reducerilor</b>!\n\n"
        "🔥 Zilnic vei primi <b>Top 5 cele mai bune reduceri</b> din România.\n\n"
        "🛍️ Verifică și site-ul: <a href='https://ghidulreducerilor.ro'>ghidulreducerilor.ro</a>\n\n"
        "🔔 Activează notificările pentru a nu rata nicio ofertă!"
    )
    r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }, timeout=15).json()

    if r.get("ok"):
        print("✅ Mesaj de bun-venit trimis pe canal!")
        return True
    else:
        print(f"❌ Eroare trimitere mesaj: {r.get('description', '')}")
        return False


def setup_task_scheduler():
    """Configurează Task Scheduler pentru rulare zilnică la 09:00."""
    script_path = Path(__file__).parent / "telegram_agent.py"
    python_path = sys.executable

    task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-04-25T09:00:00</StartBoundary>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>
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
  </Settings>
</Task>"""

    xml_path = Path(os.environ["TEMP"]) / "telegram_task.xml"
    xml_path.write_text(task_xml, encoding="utf-16")

    import subprocess
    result = subprocess.run(
        ["schtasks", "/Create", "/TN", "GhidulReducerilor_Telegram",
         "/XML", str(xml_path), "/F"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✅ Task Scheduler configurat: zilnic la 09:00")
        print("   Task: GhidulReducerilor_Telegram")
    else:
        print(f"⚠️  Task Scheduler: {result.stderr.strip()}")
        print(f"   Adaugă manual task-ul pentru: {python_path} \"{script_path}\"")


if __name__ == "__main__":
    print("=" * 50)
    print("  SETUP TELEGRAM BOT — ghidulreducerilor.ro")
    print("=" * 50)

    bot_username = check_token()
    if not bot_username:
        sys.exit(1)

    channel_ok = check_channel(bot_username)
    if not channel_ok:
        sys.exit(1)

    print("\n--- Trimit mesaj test ---")
    if send_test_message():
        print("\n--- Configurez Task Scheduler ---")
        setup_task_scheduler()
        print("\n" + "=" * 50)
        print("✅ SETUP COMPLET!")
        print(f"   Bot: @{bot_username}")
        print(f"   Canal: {CHANNEL_ID}")
        print(f"   Postare zilnică: 09:00")
        print(f"\n   Test manual: python telegram_agent.py")
        print(f"   Test conexiune: python telegram_agent.py test")
        print("=" * 50)
