import sys, time
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
from pathlib import Path
import pyperclip

PROFILE_DIR = Path(r"C:\dev\ghidulreducerilor.ro\agents\marketing\pinterest_browser_profile")
LOG_DIR     = Path(r"C:\dev\ghidulreducerilor.ro\logs\pinterest")

def fill_field(page, selector, text, label):
    """Completează câmp via clipboard — rezolvă caractere românești ț/ș/ă pe Windows."""
    try:
        el = page.locator(selector).first
        if el.is_visible(timeout=4000):
            el.click()
            time.sleep(0.3)
            page.keyboard.press("Control+a")
            pyperclip.copy(text)
            page.keyboard.press("Control+v")
            print(f"[profile] ✅ {label} setat")
            return True
    except Exception as e:
        print(f"[profile] ⚠️  {label}: {e}")
    return False

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,
        channel="chrome",
        args=["--disable-blink-features=AutomationControlled","--no-first-run"],
        viewport={"width": 1280, "height": 900},
        locale="ro-RO",
    )
    page = ctx.new_page()
    page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")

    page.goto("https://www.pinterest.com/settings/edit-profile/", wait_until="domcontentloaded")
    time.sleep(4)

    if "login" in page.url:
        print("[profile] EROARE: sesiune expirată!")
        ctx.close()
        sys.exit(1)

    print(f"[profile] URL: {page.url}")
    page.screenshot(path=str(LOG_DIR / "profile_before.png"))

    # Nume afacere
    fill_field(page, 'input[name="business_name"]',
               "GhidulReducerilor.ro",
               "Nume")
    time.sleep(0.5)

    # Bio
    bio = "📌 Cele mai bune reduceri din România — zilnic! Cumpără mai mult cu mai puțin 💰 Oferte verificate de la 50+ magazine partenere. Urmărește pentru reduceri zilnice! 🛒"
    if not fill_field(page, 'textarea[name="about"]', bio, "Bio"):
        fill_field(page, 'input[name="about"]', bio, "Bio (input)")
    time.sleep(0.5)

    # Website
    fill_field(page, 'input[name="website_url"]',
               "https://ghidulreducerilor.ro",
               "Website")
    time.sleep(0.5)

    page.screenshot(path=str(LOG_DIR / "profile_filled.png"))

    # Salvează
    saved = False
    for sel in ['button:has-text("Salvează")', 'button:has-text("Save")', 'button[type="submit"]']:
        try:
            btn = page.locator(sel).last
            if btn.is_visible(timeout=3000):
                btn.click()
                saved = True
                print(f"[profile] ✅ Save apăsat")
                break
        except:
            continue

    time.sleep(4)
    page.screenshot(path=str(LOG_DIR / "profile_after.png"))
    print(f"[profile] {'✅ GATA!' if saved else '⚠️  Save negăsit'}")
    ctx.close()
