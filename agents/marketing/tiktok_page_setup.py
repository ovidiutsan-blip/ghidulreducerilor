"""
tiktok_page_setup.py — Creare și configurare cont TikTok pentru ghidulreducerilor.ro.

Flow:
  1. Deschide tiktok.com/signup — tu creezi contul manual (email + parolă)
  2. Scriptul asteapta ca tu sa finalizezi signup-ul
  3. Automat: seteaza username, bio, link profil, poza de profil
  4. Salveaza sesiunea in tiktok_browser_profile/ (refolositã de tiktok_agent.py)

Rulare:
  python agents/marketing/tiktok_page_setup.py

Dupa setup:
  python agents/marketing/tiktok_agent.py --dry-run   (test)
  python agents/marketing/tiktok_agent.py --run       (postare live)
"""
from __future__ import annotations
import sys, time, json
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)  # type: ignore

BASE         = Path(__file__).resolve().parent.parent.parent
LOG_DIR      = BASE / "logs" / "tiktok"
PROFILE_DIR  = Path(__file__).parent / "tiktok_browser_profile"
CARDS_DIR    = BASE / "data" / "marketing" / "tiktok_cards"

# ── Datele profilului ────────────────────────────────────────────────────────
PROFILE = {
    "username":    "ghidulreducerilor",       # @ghidulreducerilor
    "display_name": "Ghidul Reducerilor 🔥",
    "bio":         "Reduceri reale, verificate zilnic 🛒\nCele mai bune oferte din Romania 🇷🇴\n👇 Link oferte:",
    "website":     "https://ghidulreducerilor.ro",
    "category":    "Shopping & Retail",
}


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / "tiktok_setup.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def generate_profile_picture() -> Path:
    """Generează o poză de profil brandată cu Pillow (1:1, 400x400)."""
    out = CARDS_DIR / "profile_picture.png"
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (400, 400), (29, 53, 87))   # navy #1D3557
        draw = ImageDraw.Draw(img)

        # Cerc portocaliu ca accent
        draw.ellipse([20, 20, 380, 380], outline=(244, 162, 97), width=12)

        # Text "GR" mare in centru
        candidates = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/seguibl.ttf",
        ]
        font = None
        for path in candidates:
            if Path(path).exists():
                try:
                    font = ImageFont.truetype(path, 130)
                    break
                except Exception:
                    continue
        if font is None:
            font = ImageFont.load_default()

        text = "GR"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((400 - tw) // 2, (400 - th) // 2 - 20), text, font=font, fill=(244, 162, 97))

        # Subtext mic
        try:
            font_sm = ImageFont.truetype(candidates[0], 28)
        except Exception:
            font_sm = ImageFont.load_default()
        sub = "reduceri.ro"
        bbox2 = draw.textbbox((0, 0), sub, font=font_sm)
        sw = bbox2[2] - bbox2[0]
        draw.text(((400 - sw) // 2, 310), sub, font=font_sm, fill=(200, 210, 220))

        img.save(str(out), "PNG")
        log(f"Poza de profil generata: {out}")
        return out
    except ImportError:
        log("[WARN] Pillow nu e instalat — fara poza de profil automata")
        return None
    except Exception as e:
        log(f"[WARN] Eroare generare poza: {e}")
        return None


def setup_tiktok_profile():
    """Deschide TikTok signup, asteapta login manual, seteaza profilul automat."""

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        log("[ERR] Playwright lipseste — pip install playwright && python -m playwright install chromium")
        sys.exit(1)

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Genereaza poza de profil
    profile_pic = generate_profile_picture()

    p = sync_playwright().start()
    browser = p.chromium.launch_persistent_context(
        str(PROFILE_DIR),
        headless=False,
        channel="msedge",  # Edge — separat de Chrome (evită singleton conflict)
        viewport={"width": 1280, "height": 800},
        args=["--disable-blink-features=AutomationControlled"],
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    page = browser.new_page()

    try:
        # ── Pasul 1: Signup ───────────────────────────────────────────────────
        log("="*55)
        log("PASUL 1: Creare cont TikTok")
        log("="*55)
        log("Deschid pagina de signup TikTok...")
        page.goto("https://www.tiktok.com/signup", timeout=30_000)
        time.sleep(2)

        log("")
        log(">>> ACTIUNE MANUALA NECESARA <<<")
        log("Creeaza contul TikTok in browser:")
        log("  - Foloseste email: ovidiutsan085@gmail.com")
        log("    SAU creeaza un email nou dedicat (recomandat)")
        log("  - Seteaza o parola puternica")
        log("  - Completeaza verificarea de securitate")
        log("")
        log("Apasa ENTER cand ai creat contul si esti pe pagina principala TikTok...")
        input()

        # Verifica ca e logat
        page.goto("https://www.tiktok.com", timeout=20_000)
        time.sleep(2)
        if "login" in page.url.lower():
            log("[ERR] Nu pare sa fii logat. Incearca din nou.")
            input("Apasa ENTER dupa ce te-ai logat...")

        # ── Pasul 2: Setare username ──────────────────────────────────────────
        log("")
        log("="*55)
        log("PASUL 2: Setare username + profil")
        log("="*55)
        log(f"Navighez la setarile profilului...")
        page.goto("https://www.tiktok.com/setting", timeout=20_000)
        time.sleep(3)

        page.screenshot(path=str(LOG_DIR / "step2_settings.png"))
        log("Screenshot salvat in logs/tiktok/step2_settings.png")
        log("")
        log(">>> ACTIUNE MANUALA <<<")
        log("In setari, cauta 'Edit Profile' si seteaza:")
        log(f"  Username: {PROFILE['username']}")
        log(f"  Name:     {PROFILE['display_name']}")
        log(f"  Bio:      {PROFILE['bio']}")
        if profile_pic and profile_pic.exists():
            log(f"  Poza de profil: {profile_pic}")
            log("  (deschide fisierul de mai sus si incarca-l ca poza de profil)")
        log("")
        log("Apasa ENTER cand ai setat profilul...")
        input()

        # ── Pasul 3: Incercare automata setare profil ─────────────────────────
        log("Incerc sa setez profilul automat...")
        try:
            page.goto("https://www.tiktok.com/setting?activeTab=account", timeout=15_000)
            time.sleep(2)

            # Cauta Edit Profile button
            for sel in [
                'a[href*="edit-profile"]',
                'button:has-text("Edit profile")',
                '[data-e2e="nav-profile"]',
            ]:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=3_000):
                        el.click()
                        time.sleep(2)
                        break
                except Exception:
                    continue

            page.goto("https://www.tiktok.com/@me/edit", timeout=10_000)
            time.sleep(3)

            # Username
            try:
                username_input = page.locator('input[placeholder*="username" i], input[name*="unique" i]').first
                if username_input.is_visible(timeout=4_000):
                    username_input.triple_click()
                    time.sleep(0.3)
                    import pyperclip
                    pyperclip.copy(PROFILE["username"])
                    page.keyboard.press("Control+v")
                    log(f"  Username setat: @{PROFILE['username']}")
                    time.sleep(1)
            except Exception:
                log("  [SKIP] Username — selecteaza manual")

            # Bio
            try:
                bio_input = page.locator('textarea[placeholder*="bio" i], textarea[name*="bio" i], div[data-e2e="user-bio"] textarea').first
                if bio_input.is_visible(timeout=4_000):
                    bio_input.triple_click()
                    time.sleep(0.3)
                    import pyperclip
                    pyperclip.copy(PROFILE["bio"])
                    page.keyboard.press("Control+v")
                    log(f"  Bio setat")
                    time.sleep(1)
            except Exception:
                log("  [SKIP] Bio — seteaza manual")

            # Poza de profil
            if profile_pic and profile_pic.exists():
                try:
                    photo_input = page.locator('input[type="file"][accept*="image"]').first
                    if photo_input.count() > 0:
                        photo_input.set_input_files(str(profile_pic))
                        log(f"  Poza de profil incarcata: {profile_pic.name}")
                        time.sleep(3)
                except Exception:
                    log(f"  [SKIP] Poza — incarca manual din: {profile_pic}")

            # Save
            for save_sel in ['button:has-text("Save")', 'button:has-text("Salveaza")', '[data-e2e="save-btn"]']:
                try:
                    btn = page.locator(save_sel).first
                    if btn.is_visible(timeout=3_000):
                        btn.click()
                        log("  Profil salvat!")
                        time.sleep(2)
                        break
                except Exception:
                    continue

        except Exception as e:
            log(f"  [WARN] Setare automata partiala: {e}")
            log("  Seteaza manual restul campurilor.")

        page.screenshot(path=str(LOG_DIR / "profile_done.png"))

        # ── Pasul 4: Confirmare si ghid urmator ──────────────────────────────
        log("")
        log("="*55)
        log("SETUP COMPLET!")
        log("="*55)
        log(f"Profil TikTok: https://www.tiktok.com/@{PROFILE['username']}")
        log(f"Sesiune salvata in: {PROFILE_DIR}")
        log("")
        log("Pasi urmatori:")
        log("  1. Deschide TikTok app pe telefon si adauga website-ul in bio:")
        log(f"     {PROFILE['website']}")
        log("  2. Testeaza agentul de postare:")
        log("     python agents/marketing/tiktok_agent.py --dry-run")
        log("  3. Prima postare live:")
        log("     python agents/marketing/tiktok_agent.py --run")
        log("")
        log("Task Scheduler 'GhidulReducerilor_TikTok_Midday' ruleaza zilnic la 11:00.")
        log("="*55)

        # Salveaza config
        config_path = Path(__file__).parent / "tiktok_config.json"
        config = {
            "username": PROFILE["username"],
            "display_name": PROFILE["display_name"],
            "website": PROFILE["website"],
            "profile_dir": str(PROFILE_DIR),
            "setup_date": datetime.now().strftime("%Y-%m-%d"),
        }
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        log(f"Config salvat: {config_path}")

    finally:
        log("Inchid browser... (sesiunea e salvata)")
        browser.close()
        p.stop()


if __name__ == "__main__":
    setup_tiktok_profile()
