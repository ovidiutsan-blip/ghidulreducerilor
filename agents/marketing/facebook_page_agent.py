"""
facebook_page_agent.py — Postează automat pe Pagina Facebook a ghidulreducerilor.ro.

Diferit de facebook_poster.py (care postează în GRUPURI), acesta postează pe
PAGINA proprie a site-ului — construiește audiență pe termen lung.

Refolosește același fb_browser_profile/ (nu e nevoie de re-login dacă ești deja
logat din facebook_poster.py).

Setup:
  python agents/marketing/facebook_page_agent.py --setup
    → salvează URL-ul paginii în fb_page_config.json

Rulare zilnică (3 postări via Task Scheduler):
  python agents/marketing/facebook_page_agent.py --run --slot morning   # 08:30
  python agents/marketing/facebook_page_agent.py --run --slot midday    # 13:00
  python agents/marketing/facebook_page_agent.py --run --slot evening   # 20:00

Slot-urile sunt independente — fiecare postează alt deal cu alt format.

Config: agents/marketing/fb_page_config.json (NU se commitează pe GitHub)
"""

import json
import time
import random
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

BASE        = Path(__file__).parent.parent.parent
POSTS_DIR   = BASE / "data" / "marketing"
LOG_DIR     = BASE / "logs" / "fb_page"
CONFIG      = Path(__file__).parent / "fb_page_config.json"
PROMO_LOG   = BASE / "data" / "marketing" / "page_promo_log.json"
PROFILE_DIR = Path(__file__).parent / "fb_browser_profile"   # același profil ca poster

SITE_BASE   = "https://ghidulreducerilor.ro"

# ─── Formate posturi pagina ───────────────────────────────────────────────────
# Pagina FB e mai "brand", mai puțin urgent față de grupuri.
# Tonul: util, informativ, cu call-to-action clar.

def _deal_link(d: dict) -> str:
    deal_id = d.get("id", "")
    if deal_id:
        return f"{SITE_BASE}/out/{deal_id}"
    return d.get("link_afiliat") or d.get("affiliate_url") or SITE_BASE


def format_morning(d: dict) -> str:
    """Post de dimineață — 'Buna dimineata + deal zilei'."""
    titlu = d.get("titlu") or d.get("title", "Produs")
    pct   = d.get("procent_reducere") or d.get("discount_percent") or 0
    pret  = d.get("pret_redus") or d.get("price") or 0
    orig  = d.get("pret_original") or d.get("originalPrice") or 0
    store = (d.get("magazin") or d.get("store", "")).capitalize()
    link  = _deal_link(d)
    today_name = datetime.now().strftime("%A").lower()
    zile_ro = {
        "monday": "luni", "tuesday": "marți", "wednesday": "miercuri",
        "thursday": "joi", "friday": "vineri", "saturday": "sâmbătă", "sunday": "duminică"
    }
    zi = zile_ro.get(today_name, "azi")
    return (
        f"☀️ Bună dimineața! Vă aducem oferta zilei de {zi}:\n\n"
        f"🏷️ {titlu}\n"
        f"💰 {pret} lei (în loc de {orig} lei)\n"
        f"📉 Reducere: -{pct}%\n"
        f"🏪 Magazin: {store}\n\n"
        f"👉 {link}\n\n"
        f"Urmărește pagina pentru cele mai bune oferte zilnic! 🔔\n\n"
        f"#reduceri #oferte#{store.lower()} #ghidulreducerilor"
    )


def format_midday(d: dict) -> str:
    """Post de prânz — focus pe economie/valoare."""
    titlu = d.get("titlu") or d.get("title", "Produs")
    pct   = d.get("procent_reducere") or d.get("discount_percent") or 0
    pret  = d.get("pret_redus") or d.get("price") or 0
    orig  = d.get("pret_original") or d.get("originalPrice") or 0
    economie = orig - pret if orig > pret else 0
    store = (d.get("magazin") or d.get("store", "")).capitalize()
    link  = _deal_link(d)
    return (
        f"💡 Ofertă de la prânz — economisești {economie:.0f} lei!\n\n"
        f"📦 {titlu}\n\n"
        f"✅ Preț redus: {pret} lei\n"
        f"❌ Preț normal: {orig} lei\n"
        f"🔥 -{pct}% reducere pe {store}\n\n"
        f"🛒 {link}\n\n"
        f"#chilipiruri #dealzilei #{store.lower()}"
    )


def format_evening(d: dict) -> str:
    """Post de seară — 'ultima șansă' / mai relaxat."""
    titlu = d.get("titlu") or d.get("title", "Produs")
    pct   = d.get("procent_reducere") or d.get("discount_percent") or 0
    pret  = d.get("pret_redus") or d.get("price") or 0
    store = (d.get("magazin") or d.get("store", "")).capitalize()
    link  = _deal_link(d)
    return (
        f"🌙 Oferta serii — mai e timp!\n\n"
        f"➡️ {titlu}\n"
        f"💥 -{pct}% → {pret} lei pe {store}\n\n"
        f"Toate ofertele zilei: {SITE_BASE}\n\n"
        f"👉 {link}\n\n"
        f"#ofertaserii #reduceri #{store.lower()} #ghidulreducerilor"
    )


# ─── Slot → format ───────────────────────────────────────────────────────────

SLOT_FORMATS = {
    "morning": format_morning,
    "midday":  format_midday,
    "evening": format_evening,
}

SLOT_HOURS = {
    "morning": 8,
    "midday":  13,
    "evening": 20,
}


# ─── Config ───────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG.exists():
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(cfg: dict):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def load_promo_log() -> dict:
    if PROMO_LOG.exists():
        with open(PROMO_LOG, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_promo_log(log: dict):
    PROMO_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(PROMO_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


# ─── Selecție deal pentru slot ────────────────────────────────────────────────

def select_deal_for_slot(slot: str) -> dict | None:
    """
    Selectează un deal potrivit pentru slot-ul dat.
    Cooldown 2 zile, min 30% reducere, imaginea obligatorie.
    """
    sys.path.insert(0, str(Path(__file__).parent))
    from deal_selector import load_deals

    deals = load_deals()
    promo_log = load_promo_log()
    cutoff = datetime.now() - timedelta(days=2)

    # Cheie unică per slot ca să nu repete același deal în zile consecutive
    slot_key = f"{slot}:{datetime.now().strftime('%Y-%m-%d')}"

    eligible = []
    for d in deals:
        if not d.get("activ", True):
            continue
        pct = d.get("procent_reducere") or d.get("discount_percent") or 0
        if pct < 30:
            continue
        # Imagine obligatorie pentru postări pe pagina FB
        if not (d.get("imagine_url") or d.get("image")):
            continue
        # Cooldown — nu posta același deal în ultimele 2 zile
        last = promo_log.get(d.get("id", ""))
        if last:
            try:
                if datetime.fromisoformat(last) > cutoff:
                    continue
            except Exception:
                pass
        eligible.append(d)

    if not eligible:
        return None

    # Sortează după procent_reducere descrescător
    eligible.sort(key=lambda x: (x.get("procent_reducere") or x.get("discount_percent") or 0), reverse=True)

    # Diversitate: morning=index 0, midday=1, evening=2
    slot_idx = {"morning": 0, "midday": 1, "evening": 2}.get(slot, 0)
    return eligible[min(slot_idx, len(eligible) - 1)]


def mark_page_posted(deal_id: str):
    log = load_promo_log()
    log[deal_id] = datetime.now().isoformat()
    save_promo_log(log)


# ─── Helpers Playwright ───────────────────────────────────────────────────────

def human_delay(min_s: float = 1.5, max_s: float = 4.0):
    time.sleep(random.uniform(min_s, max_s))


def take_screenshot(page, name: str) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = LOG_DIR / f"{ts}_{name}.png"
    page.screenshot(path=str(path))
    return path


# ─── Postare pe pagina FB ─────────────────────────────────────────────────────

def post_to_page(page, page_url: str, post_text: str, deal_image_url: str | None = None) -> bool:
    """
    Navighează la pagina FB și publică textul.
    Strategia: click pe "Scrie ceva pe pagina ta..." → tastează → Postează.
    """
    print(f"[fb_page] → Navighez la pagina: {page_url}")
    try:
        page.goto(page_url, wait_until="domcontentloaded", timeout=25000)
        human_delay(3, 5)

        if "login" in page.url:
            print("[fb_page] ⚠️  Redirect la login — sesiunea expirat!")
            return False

        # Click pe câmpul de creare post pe pagina
        create_post_selectors = [
            '[aria-label="Scrie ceva pe pagina ta..."]',
            '[aria-label="Write something on your page..."]',
            '[aria-label="Crează o postare"]',
            '[aria-label="Create a post"]',
            'div[data-pagelet="ProfileComposer"] [role="button"]',
        ]

        clicked = False
        for sel in create_post_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.click()
                    clicked = True
                    human_delay(1, 2)
                    break
            except Exception:
                continue

        if not clicked:
            # Fallback: caută orice placeholder care conține "Scrie ceva" sau "What's on your mind"
            for placeholder in ["Scrie ceva", "What's on your mind", "Crează o postare"]:
                try:
                    page.get_by_placeholder(placeholder).first.click(timeout=4000)
                    clicked = True
                    human_delay(1, 2)
                    break
                except Exception:
                    continue

        if not clicked:
            print("[fb_page] ⚠️  Nu am găsit câmpul de creare post!")
            take_screenshot(page, "no_create_post_box")
            return False

        # Tastează textul (clipboard — rezolvă caracterele românești ț/ș/ă pe Windows)
        import pyperclip
        pyperclip.copy(post_text)
        page.keyboard.press("Control+v")
        human_delay(2, 3)

        # Screenshot înainte de publicare
        take_screenshot(page, "before_page_post")

        # Butonul Postează
        post_btn_selectors = [
            '[aria-label="Postează"]',
            '[aria-label="Post"]',
            'div[aria-label="Postează"]',
        ]
        posted = False
        for sel in post_btn_selectors:
            try:
                btn = page.locator(sel).last
                if btn.is_visible(timeout=3000):
                    btn.click()
                    posted = True
                    break
            except Exception:
                continue

        if not posted:
            try:
                page.get_by_role("button", name="Postează").last.click(timeout=5000)
                posted = True
            except Exception:
                pass

        if not posted:
            # Ultimul fallback: buton cu text "Post" (en)
            try:
                page.get_by_role("button", name="Post").last.click(timeout=5000)
                posted = True
            except Exception:
                pass

        if not posted:
            print("[fb_page] ⚠️  Nu am găsit butonul Postează!")
            take_screenshot(page, "no_post_button")
            return False

        human_delay(3, 5)
        take_screenshot(page, "page_posted_ok")
        print("[fb_page] ✅ Postat pe pagina Facebook!")
        return True

    except Exception as e:
        print(f"[fb_page] Eroare: {e}")
        try:
            take_screenshot(page, "page_post_error")
        except Exception:
            pass
        return False


# ─── Setup ────────────────────────────────────────────────────────────────────

def setup():
    print("\n=== SETUP Facebook Page Auto-Poster ===\n")
    print("Ai nevoie de URL-ul paginii tale Facebook.")
    print("Exemplu: https://www.facebook.com/ghidulreducerilor\n")
    print("Dacă nu ai creat pagina încă, urmează instrucțiunile de mai jos,")
    print("apoi revino și rulează din nou --setup.\n")
    print("──────────────────────────────────────────────")
    print("CUM CREEZI PAGINA FACEBOOK:")
    print("1. Mergi la: https://www.facebook.com/pages/create")
    print("2. Alege: Business or brand")
    print("3. Nume pagină:  GhidulReducerilor.ro")
    print("4. Categorie:    Shopping & retail")
    print("5. Click Next → adaugă descriere + poze (opțional)")
    print("6. Copiază URL-ul paginii create (ex: facebook.com/ghidulreducerilor)")
    print("──────────────────────────────────────────────\n")

    page_url = input("URL pagina Facebook (Enter pentru a seta mai târziu): ").strip()
    if not page_url:
        page_url = "https://www.facebook.com/ghidulreducerilor"
        print(f"[setup] URL implicit setat: {page_url}")

    cfg = {
        "page_url":        page_url,
        "posts_per_day":   3,
        "slots":           ["morning", "midday", "evening"],
        "post_hour_start": 8,
        "post_hour_end":   21,
        "min_discount":    30,
    }
    save_config(cfg)
    print(f"\n✅ Config salvat: {CONFIG}")
    print("\nPasul următor:")
    print("  python agents/marketing/facebook_page_agent.py --run --slot morning")


# ─── Runner principal ─────────────────────────────────────────────────────────

def run_slot(slot: str, dry_run: bool = False) -> dict:
    """Postează un singur slot (morning / midday / evening)."""
    if slot not in SLOT_FORMATS:
        print(f"[fb_page] Slot invalid: {slot}. Opțiuni: morning, midday, evening")
        sys.exit(1)

    print(f"\n{'='*55}")
    print(f"📘 Facebook Page — slot: {slot} — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}\n")

    cfg = load_config()
    if not cfg:
        print("[fb_page] Config lipsă. Rulează: --setup")
        sys.exit(1)

    page_url = cfg.get("page_url", "https://www.facebook.com/ghidulreducerilor")

    # Verifică ora
    hour = datetime.now().hour
    expected_hour = SLOT_HOURS[slot]
    if abs(hour - expected_hour) > 2 and not dry_run:
        print(f"[fb_page] Slot {slot} e configurat pt ora {expected_hour}, acum e ora {hour}. Skip.")
        return {"status": "wrong_hour", "slot": slot}

    # Verifică profil browser
    if not PROFILE_DIR.exists() or not any(PROFILE_DIR.iterdir()):
        print("[fb_page] ⚠️  Profilul browser lipsă. Rulează mai întâi:")
        print("         python facebook_poster.py --login")
        sys.exit(1)

    # Selectează deal
    deal = select_deal_for_slot(slot)
    if not deal:
        print(f"[fb_page] Niciun deal eligibil pentru slot {slot} — skip")
        return {"status": "no_deals", "slot": slot}

    # Generează text
    formatter = SLOT_FORMATS[slot]
    post_text = formatter(deal)
    deal_id   = deal.get("id", "")

    print(f"[fb_page] Deal selectat: {deal.get('titlu') or deal.get('title', '')[:60]}")
    print(f"[fb_page] Reducere: -{deal.get('procent_reducere') or deal.get('discount_percent')}%")
    print(f"[fb_page] Pagina: {page_url}")
    print(f"\n--- Preview post ---\n{post_text}\n---\n")

    if dry_run:
        print("[fb_page] DRY-RUN — nu se postează")
        return {"status": "dry_run", "slot": slot, "deal_id": deal_id}

    # Postare Playwright
    from playwright.sync_api import sync_playwright

    result = {"slot": slot, "deal_id": deal_id, "success": False, "time": datetime.now().isoformat()}

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ro-RO",
        )
        page_pw = context.new_page()
        page_pw.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins',   { get: () => [1, 2, 3] });
        """)

        # Verifică login
        page_pw.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        human_delay(2, 3)

        if "login" in page_pw.url:
            print("[fb_page] ⚠️  Sesiunea expirat. Rulează: python facebook_poster.py --login")
            context.close()
            sys.exit(1)

        print("[fb_page] ✅ Logat pe Facebook (profil persistent)")

        deal_image = deal.get("imagine_url") or deal.get("image")
        ok = post_to_page(page_pw, page_url, post_text, deal_image_url=deal_image)
        result["success"] = ok
        context.close()

    if result["success"]:
        mark_page_posted(deal_id)

    # Log
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{slot}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n{'✅' if result['success'] else '❌'} Slot {slot}: {'publicat' if result['success'] else 'eroare'}")
    print(f"[fb_page] Log: {log_path}")
    return result


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Facebook Page Auto-Poster pentru ghidulreducerilor.ro")
    parser.add_argument("--setup",    action="store_true", help="Configurare inițială (URL pagina)")
    parser.add_argument("--run",      action="store_true", help="Postează pe pagina FB")
    parser.add_argument("--dry-run",  action="store_true", help="Test fără postare efectivă")
    parser.add_argument("--slot",     default="morning",
                        choices=["morning", "midday", "evening"],
                        help="Slot de postare (morning=08:30, midday=13:00, evening=20:00)")
    args = parser.parse_args()

    if args.setup:
        setup()
    elif args.run or args.dry_run:
        run_slot(args.slot, dry_run=args.dry_run)
    else:
        parser.print_help()
