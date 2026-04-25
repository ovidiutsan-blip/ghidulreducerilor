"""
telegram_agent.py — Poster automat top 5 deals pe canalul Telegram al ghidulreducerilor.ro.

Setup necesar (o singură dată):
1. Deschide Telegram → caută @BotFather → /newbot → urmează pașii
2. Copiază token-ul primit (ex: 123456:ABCdef...)
3. Adaugă în .env: TELEGRAM_BOT_TOKEN=<token>
4. Adaugă în .env: TELEGRAM_CHANNEL_ID=@ghidulreducerilor (după ce creezi canalul)
5. Adaugă botul ca admin pe canal
6. Rulează: python telegram_agent.py

Rulare zilnică automată: Task Scheduler → 09:00.
"""

import os, json, sys
from pathlib import Path
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

BASE = Path(__file__).resolve().parent.parent.parent
DEALS_PATH = BASE / "data" / "deals.json"

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@ghidulreducerilor")
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

UTM = "?utm_source=telegram&utm_medium=social&utm_campaign=daily_deals"


# ─── Helpers ────────────────────────────────────────────────────────────────

def send_message(chat_id: str, text: str, parse_mode: str = "HTML",
                 disable_web_page_preview: bool = False) -> dict:
    """Trimite un mesaj text pe canal."""
    r = requests.post(f"{API_BASE}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
    }, timeout=15)
    return r.json()


def send_photo(chat_id: str, photo_url: str, caption: str, parse_mode: str = "HTML") -> dict:
    """Trimite o poză cu caption pe canal."""
    r = requests.post(f"{API_BASE}/sendPhoto", json={
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": parse_mode,
    }, timeout=15)
    return r.json()


def send_media_group(chat_id: str, media: list) -> dict:
    """Trimite un album de poze (max 10)."""
    r = requests.post(f"{API_BASE}/sendMediaGroup", json={
        "chat_id": chat_id,
        "media": media,
    }, timeout=15)
    return r.json()


# ─── Selecție deals ─────────────────────────────────────────────────────────

def load_top_deals(n: int = 5) -> list:
    """Returnează top N deals active, sortate după reducere %."""
    with open(DEALS_PATH, encoding="utf-8") as f:
        deals = json.load(f)

    activi = [d for d in deals if d.get("activ") and d.get("imagine_url")]
    # Sortare: reducere % descrescătoare
    activi.sort(key=lambda d: -(d.get("procent_reducere") or 0))
    return activi[:n]


# ─── Formatare mesaje ────────────────────────────────────────────────────────

def format_deal_caption(deal: dict, index: int, total: int) -> str:
    """Generează caption HTML pentru un deal individual."""
    titlu = deal.get("titlu", "")[:100]
    magazin = deal.get("magazin", "").replace("-", " ").title()
    pret_original = deal.get("pret_original", 0)
    pret_redus = deal.get("pret_redus", 0)
    pct = deal.get("procent_reducere", 0)
    categorie = deal.get("categorie", "").replace("-", " ").title()

    # Link afiliat cu UTM tracking
    link = deal.get("link_afiliat", deal.get("product_url", ""))
    if "?" in link:
        link_utm = link + "&utm_source=telegram&utm_medium=social&utm_campaign=daily_deals"
    else:
        link_utm = link + UTM

    # URL deal pe site-ul nostru
    site_url = f"https://ghidulreducerilor.ro"

    lines = [
        f"🔥 <b>-{pct}% REDUCERE</b> | Deal #{index}/{total}",
        f"",
        f"📦 <b>{titlu}</b>",
        f"",
        f"💰 <s>{pret_original:.0f} RON</s>  →  <b>{pret_redus:.0f} RON</b>",
        f"🏪 {magazin}  |  📂 {categorie}",
        f"",
        f"👉 <a href=\"{link_utm}\">VEZI OFERTA →</a>",
        f"",
        f"📲 Mai multe reduceri: {site_url}",
    ]
    return "\n".join(lines)


def format_intro_message(deals: list) -> str:
    """Mesaj introductiv zilnic cu sumarul top deals."""
    zi = datetime.now().strftime("%d %B %Y")
    lines = [
        f"🛍️ <b>TOP {len(deals)} REDUCERI ALE ZILEI</b>",
        f"📅 {zi}",
        f"",
        f"Am selectat cele mai bune oferte active acum:",
        f"",
    ]
    for i, d in enumerate(deals, 1):
        titlu = d.get("titlu", "")[:60]
        pct = d.get("procent_reducere", 0)
        pret = d.get("pret_redus", 0)
        lines.append(f"  {i}. -{pct}% | {titlu}... ({pret:.0f} RON)")

    lines += [
        f"",
        f"👇 Detalii cu link-uri de cumpărare mai jos:",
        f"",
        f"🔔 Activează notificările pentru a nu rata ofertele!",
        f"🌐 ghidulreducerilor.ro — reduceri verificate zilnic",
    ]
    return "\n".join(lines)


# ─── Postare ─────────────────────────────────────────────────────────────────

def post_daily_deals():
    """Funcția principală: postează top 5 deals pe canalul Telegram."""
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN lipsește din .env!")
        print("   1. Deschide Telegram → @BotFather → /newbot")
        print("   2. Adaugă în .env: TELEGRAM_BOT_TOKEN=<token>")
        sys.exit(1)

    print(f"[telegram] Canal: {CHANNEL_ID}")
    print(f"[telegram] Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 1. Încarcă top 5 deals
    deals = load_top_deals(5)
    if not deals:
        print("[telegram] ❌ Niciun deal activ cu imagine găsit!")
        return

    print(f"[telegram] {len(deals)} deals selectate")

    # 2. Trimite mesaj introductiv
    intro = format_intro_message(deals)
    r = send_message(CHANNEL_ID, intro)
    if not r.get("ok"):
        print(f"[telegram] ❌ Eroare intro: {r}")
        return
    print("[telegram] ✅ Mesaj intro trimis")

    # 3. Postează fiecare deal cu imagine
    for i, deal in enumerate(deals, 1):
        caption = format_deal_caption(deal, i, len(deals))
        img = deal.get("imagine_url", "")

        try:
            if img and img.startswith("http"):
                r = send_photo(CHANNEL_ID, img, caption)
                if r.get("ok"):
                    print(f"[telegram] ✅ Deal {i}/{len(deals)}: {deal.get('titlu','')[:50]}")
                else:
                    # Fallback la mesaj text dacă imaginea eșuează
                    print(f"[telegram] ⚠️  Imagine eșuată, trimit text: {r.get('description','')}")
                    send_message(CHANNEL_ID, caption)
            else:
                send_message(CHANNEL_ID, caption)
                print(f"[telegram] ✅ Deal {i}/{len(deals)} (text)")
        except Exception as e:
            print(f"[telegram] ⚠️  Deal {i} eroare: {e}")

        # Pauză între mesaje (evită rate limit Telegram)
        import time
        time.sleep(1.5)

    print(f"\n[telegram] ✅ DONE — {len(deals)} deals postate pe {CHANNEL_ID}")
    print(f"[telegram] Tracking: ?utm_source=telegram activ pe toate link-urile")


# ─── Setup helper ────────────────────────────────────────────────────────────

def test_connection():
    """Verifică dacă bot-ul e conectat și are acces la canal."""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN lipsește!")
        return False

    # Test getMe
    r = requests.get(f"{API_BASE}/getMe", timeout=10).json()
    if not r.get("ok"):
        print(f"❌ Token invalid: {r}")
        return False

    bot_name = r["result"]["username"]
    print(f"✅ Bot conectat: @{bot_name}")

    # Test sendMessage
    r2 = send_message(CHANNEL_ID, "🔧 Test conexiune bot ghidulreducerilor.ro — OK!")
    if r2.get("ok"):
        print(f"✅ Mesaj test trimis pe {CHANNEL_ID}")
        return True
    else:
        print(f"❌ Eroare canal: {r2.get('description','')}")
        print(f"   Asigură-te că botul @{bot_name} e admin pe {CHANNEL_ID}")
        return False


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_connection()
    else:
        post_daily_deals()
