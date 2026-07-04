"""
pinterest_agent.py — Postare automată pe Pinterest.

Strategie:
  - Board per categorie (casa-gradina, beauty, electronice, ceasuri, etc.)
  - 3-5 pin-uri/zi, ore de vârf (12:00-14:00 și 20:00-22:00 RO)
  - Titlu + descriere SEO optimizate în română
  - Link direct la /out/{id} (tracker afiliat)
  - Profilul browser persistent — login o singură dată manual

Setup prima dată (login MANUAL, fără parolă stocată pe disc):
  python agents/marketing/pinterest_agent.py --login
  (se deschide un browser; te loghezi tu — email/parolă sau Google — sesiunea se salvează)
  Opțional: --setup salvează doar preferințe (email pt. pre-completare, pin-uri/zi).

Rulare zilnică (Task Scheduler):
  python agents/marketing/pinterest_agent.py --run

Debug/test:
  python agents/marketing/pinterest_agent.py --dry-run
"""

import json
import time
import random
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, date
from typing import Optional
import requests
import pyperclip

BASE         = Path(__file__).parent.parent.parent
DEALS_PATH   = BASE / "data" / "deals.json"
LOG_DIR      = BASE / "logs" / "pinterest"
PROFILE_DIR  = Path(__file__).parent / "pinterest_browser_profile"
CONFIG       = Path(__file__).parent / "pinterest_config.json"
PROMO_LOG    = BASE / "data" / "marketing" / "pinterest_promo_log.json"

SITE_BASE    = "https://ghidulreducerilor.ro"

# ─── Mapping categorie → board Pinterest ─────────────────────────────────────
# Cheile = valori din câmpul 'categorie' din deals.json
# Valorile = numele board-ului pe Pinterest (creat manual o dată)

BOARD_MAP = {
    "casa-gradina":      "Casă și Grădină — Reduceri",
    "beauty":            "Beauty & Cosmetice — Reduceri",
    "farmacie-sanatate": "Sănătate & Farmacie — Oferte",
    "suplimente-bio":    "Sănătate & Farmacie — Oferte",
    "electronice":       "Electronice — Reduceri România",
    "smartwatch":        "Smartwatch & Gadgeturi",
    "ceasuri":           "Ceasuri — Reduceri",
    "casti":             "Căști & Audio — Oferte",
    "tablete":           "Tablete & Laptopuri",
    "laptopuri":         "Tablete & Laptopuri",
    "televizoare":       "TV & Electronice",
    "promotii":          "Oferte Zilei — România",
    "carti":             "Cărți — Reduceri",
    "fashion":           "Modă — Reduceri Online",
    "default":           "Reduceri România — GhidulReducerilor",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

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


def human_delay(min_s: float = 1.5, max_s: float = 4.0):
    time.sleep(random.uniform(min_s, max_s))


def clipboard_fill(page, el, text: str):
    """
    Completează un câmp folosind clipboard — rezolvă caracterele românești (ț, ș, ă).
    keyboard.type() pe Windows nu trimite corect Unicode non-ASCII.
    """
    pyperclip.copy(text)
    el.click()
    time.sleep(0.2)
    page.keyboard.press("Control+a")
    page.keyboard.press("Control+v")


def take_screenshot(page, name: str) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name}.png"
    page.screenshot(path=str(path))
    return path


def deal_link(d: dict) -> str:
    deal_id = d.get("id", "")
    return f"{SITE_BASE}/out/{deal_id}" if deal_id else SITE_BASE


def board_for_deal(d: dict) -> str:
    cat = (d.get("categorie") or "").lower().strip()
    return BOARD_MAP.get(cat, BOARD_MAP["default"])


# ─── Generare text pin ────────────────────────────────────────────────────────

def pin_title(d: dict) -> str:
    titlu = (d.get("titlu") or d.get("title") or "Ofertă").strip()
    pct   = d.get("procent_reducere") or d.get("discount_percent") or 0
    store = (d.get("magazin") or d.get("store") or "").capitalize()
    # Truncat la 100 caractere (limita Pinterest)
    title = f"-{pct}% | {titlu}"
    if store:
        title += f" | {store}"
    return title[:100]


def pin_description(d: dict) -> str:
    titlu  = (d.get("titlu") or d.get("title") or "Produs").strip()
    pct    = d.get("procent_reducere") or d.get("discount_percent") or 0
    pret   = d.get("pret_redus") or d.get("price") or 0
    orig   = d.get("pret_original") or d.get("originalPrice") or 0
    store  = (d.get("magazin") or d.get("store") or "").capitalize()
    link   = deal_link(d)
    economie = orig - pret if orig > pret else 0

    lines = [
        f"🔥 -{pct}% reducere la {titlu}",
        "",
        f"💰 Preț: {pret:.0f} lei (față de {orig:.0f} lei)",
    ]
    if economie > 0:
        lines.append(f"💡 Economisești {economie:.0f} lei!")
    lines += [
        "",
        f"✅ Cumpără acum pe {store}: {link}",
        "",
        "📌 Urmărește board-ul pentru reduceri zilnice!",
        "",
        "#reduceri #oferte #chilipiruri #" + store.lower().replace(" ", "") +
        " #ghidulreducerilor #shopping #romania",
    ]
    # Maxim 500 caractere (limita Pinterest)
    desc = "\n".join(lines)
    return desc[:500]


# ─── Selecție deals pentru Pinterest ─────────────────────────────────────────

def select_deals_for_pinterest(n: int = 5) -> list[dict]:
    """Selectează N deals de postat azi pe Pinterest (diversitate categorii)."""
    with open(DEALS_PATH, encoding="utf-8") as f:
        deals = json.load(f)

    promo_log = load_promo_log()
    from datetime import timedelta
    cooldown = datetime.now() - timedelta(days=2)  # cooldown 2 zile (mai scurt ca FB)

    eligible = []
    for d in deals:
        if d.get("expired") or not d.get("activ", True):
            continue
        pct = d.get("procent_reducere") or d.get("discount_percent") or 0
        if pct < 30:
            continue
        # Trebuie imagine
        if not (d.get("imagine_url") or d.get("image")):
            continue
        # Cooldown
        last = promo_log.get(d.get("id", ""))
        if last:
            try:
                if datetime.fromisoformat(last) > cooldown:
                    continue
            except Exception:
                pass
        eligible.append(d)

    # Sortează: discount desc, cu bonus imagine și omnibus
    def score(d):
        s = (d.get("procent_reducere") or d.get("discount_percent") or 0) * 1.2
        if d.get("omnibus_validated"):
            s += 15
        if d.get("pret_redus", 9999) < 300 or d.get("price", 9999) < 300:
            s += 10
        return s

    eligible.sort(key=score, reverse=True)

    # Diversitate: max 1 per categorie
    selected = []
    seen_cats = set()
    for d in eligible:
        cat = d.get("categorie") or "default"
        if cat in seen_cats:
            continue
        selected.append(d)
        seen_cats.add(cat)
        if len(selected) >= n:
            break

    # Dacă n-avem suficiente cu diversitate, completăm fără restricție
    if len(selected) < n:
        for d in eligible:
            if d not in selected:
                selected.append(d)
            if len(selected) >= n:
                break

    return selected


# ─── Login interactiv ─────────────────────────────────────────────────────────

def login_interactive():
    """
    Deschide Pinterest într-un browser persistent și așteaptă login MANUAL.

    Nicio parolă nu e stocată sau completată de agent: te loghezi tu în fereastra
    care se deschide (email/parolă sau Google — cum vrei), apoi apeși ENTER aici.
    Sesiunea rămâne salvată în PROFILE_DIR și e refolosită de --run. Dacă în config
    există un email, doar câmpul de email e pre-completat, ca simplă comoditate.
    """
    from playwright.sync_api import sync_playwright

    cfg   = load_config()
    email = cfg.get("email", "")

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    print("\n=== LOGIN PINTEREST (manual, fără parolă stocată) ===")
    if email:
        print(f"Email pre-completat: {email}")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ro-RO",
        )
        page = ctx.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        print("[pinterest] Se deschide login-ul — loghează-te MANUAL în fereastră.")
        page.goto("https://www.pinterest.com/login/", wait_until="domcontentloaded")
        human_delay(3, 5)

        # Comoditate: pre-completează doar emailul, dacă e cunoscut. Parola o introduci tu.
        if email:
            try:
                page.fill('input[name="id"]', email, timeout=8000)
            except Exception:
                pass

        input(">>> Loghează-te în fereastră, apoi apasă ENTER aici: ")
        if "login" in page.url:
            print("[pinterest] ⚠️  Încă pari nelogat (URL conține 'login'). Verifică fereastra.")
            take_screenshot(page, "login_check")
        else:
            print(f"[pinterest] ✅ Login OK! URL: {page.url}")
            take_screenshot(page, "login_ok")
        print(f"[pinterest] ✅ Profil salvat: {PROFILE_DIR}")
        ctx.close()


# ─── Postare pin ──────────────────────────────────────────────────────────────

def download_image_temp(url: str) -> Optional[str]:
    """Descarcă imaginea în temp, o redimensionează la min 800x1200px și returnează calea."""
    import tempfile, urllib.request, os
    try:
        suffix = ".jpg"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r, open(tmp.name, "wb") as f:
            f.write(r.read())

        # Redimensionează la min 800x1200 (format Pinterest 2:3)
        try:
            from PIL import Image
            img = Image.open(tmp.name).convert("RGB")
            w, h = img.size
            MIN_W, MIN_H = 800, 1200
            if w < MIN_W or h < MIN_H:
                # Upscale la dimensiunea minimă Pinterest
                scale = max(MIN_W / w, MIN_H / h)
                new_w = max(int(w * scale), MIN_W)
                new_h = max(int(h * scale), MIN_H)
                img = img.resize((new_w, new_h), Image.LANCZOS)
                print(f"[pinterest] Imagine redimensionată: {w}x{h} → {new_w}x{new_h}")
            img.save(tmp.name, "JPEG", quality=90)
        except ImportError:
            print("[pinterest] Pillow nu e instalat — imagine fără resize")
        except Exception as re:
            print(f"[pinterest] Resize: {re}")

        return tmp.name
    except Exception as e:
        print(f"[pinterest] Download imagine eșuat: {e}")
        return None


def post_pin(page, deal: dict, dry_run: bool = False) -> bool:
    """Postează un pin pe Pinterest — UI românesc, upload fișier."""
    board = board_for_deal(deal)
    title = pin_title(deal)
    desc  = pin_description(deal)
    link  = deal_link(deal)
    image_url = deal.get("imagine_url") or deal.get("image") or ""
    titlu_short = (deal.get("titlu") or deal.get("title") or "")[:30]

    print(f"\n[pinterest] → Pin: {titlu_short}...")
    print(f"              Board: {board}")
    print(f"              Link:  {link}")

    if dry_run:
        print(f"[pinterest] DRY-RUN — skip postare")
        return True

    import tempfile, os
    tmp_image = None

    try:
        # Navighează la creator
        page.goto("https://www.pinterest.com/pin-creation-tool/", wait_until="domcontentloaded")
        human_delay(3, 5)

        if "login" in page.url:
            print("[pinterest] ⚠️  Sesiunea a expirat. Rulează --login-auto")
            return False

        # ── Upload imagine ─────────────────────────────────────────────────────
        if image_url:
            tmp_image = download_image_temp(image_url)

        if tmp_image and os.path.exists(tmp_image):
            # Caută input[type="file"] (poate fi ascuns)
            try:
                file_input = page.locator('input[type="file"]').first
                file_input.set_input_files(tmp_image)
                print(f"[pinterest] ✅ Imagine uploadată: {os.path.basename(tmp_image)}")
                human_delay(3, 5)  # așteptare procesare imagine
            except Exception as e:
                print(f"[pinterest] Upload imagine: {e}")
        else:
            print(f"[pinterest] ⚠️  Nicio imagine disponibilă pentru upload")

        # ── Titlu ──────────────────────────────────────────────────────────────
        title_filled = False
        title_selectors = [
            '[placeholder="Adaugă un titlu"]',
            '[placeholder="Adaugă titlu"]',
            '[placeholder="Add a title"]',
            '[data-test-id="pin-draft-title"] input',
            '[data-test-id="pin-draft-title"] [contenteditable]',
            'input[name="title"]',
        ]
        for sel in title_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    clipboard_fill(page, el, title[:100])
                    title_filled = True
                    print(f"[pinterest] ✅ Titlu setat")
                    break
            except Exception:
                continue
        if not title_filled:
            print(f"[pinterest] ⚠️  Titlu negăsit")
        human_delay(0.5, 1)

        # ── Descriere ──────────────────────────────────────────────────────────
        desc_filled = False
        desc_selectors = [
            '[placeholder="Adaugă o descriere detaliată"]',
            '[placeholder="Spune mai multe despre Pin-ul tău"]',
            '[placeholder="Tell everyone what your Pin is about"]',
            '[data-test-id="pin-draft-description"] textarea',
            '[data-test-id="pin-draft-description"] [contenteditable]',
            'textarea[name="description"]',
            'div[data-test-id="pin-draft-description"] [contenteditable]',
        ]
        for sel in desc_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    clipboard_fill(page, el, desc[:500])
                    desc_filled = True
                    print(f"[pinterest] ✅ Descriere setată")
                    break
            except Exception:
                continue
        if not desc_filled:
            print(f"[pinterest] ⚠️  Descriere negăsită")
        human_delay(0.5, 1)

        # ── Link destinație ────────────────────────────────────────────────────
        link_filled = False
        link_selectors = [
            '[placeholder="Adaugă un link"]',
            '[placeholder="Add a link"]',
            '[data-test-id="pin-draft-link"] input',
            'input[name="link"]',
            'input[placeholder*="link" i]',
        ]
        for sel in link_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    clipboard_fill(page, el, link)
                    link_filled = True
                    print(f"[pinterest] ✅ Link setat")
                    break
            except Exception:
                continue
        if not link_filled:
            print(f"[pinterest] ⚠️  Link negăsit")
        human_delay(0.5, 1)

        # ── Selectare / Creare board ───────────────────────────────────────────
        board_selectors = [
            'div[data-test-id="board-dropdown-select-button"]',
            '[data-test-id="board-dropdown-select-button"]',
            'button:has-text("Alege un panou")',
            'button:has-text("Alege un board")',
            'button:has-text("Choose a board")',
        ]
        board_opened = False
        for sel in board_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.click()
                    human_delay(2, 3)
                    board_opened = True
                    print(f"[pinterest] Board dropdown deschis")
                    break
            except Exception:
                continue

        if board_opened:
            board_found = False

            # Caută board-ul specific
            for board_name in [board, "Reduceri România — GhidulReducerilor", "Reduceri"]:
                try:
                    board_el = page.get_by_text(board_name, exact=False).first
                    if board_el.is_visible(timeout=2000):
                        board_el.click()
                        board_found = True
                        human_delay(1, 2)
                        print(f"[pinterest] ✅ Board selectat: {board_name}")
                        break
                except Exception:
                    continue

            if not board_found:
                # Încearcă primul board disponibil
                try:
                    first_board = page.locator(
                        '[data-test-id="board-row"], [data-test-id="boardWithoutSection"], '
                        '[data-test-id="board-list-item"]'
                    ).first
                    if first_board.is_visible(timeout=3000):
                        first_board.click()
                        board_found = True
                        human_delay(1, 2)
                        print(f"[pinterest] ✅ Primul board selectat")
                except Exception:
                    pass

            if not board_found:
                # Creează un board nou: "Reduceri România"
                print(f"[pinterest] Niciun board găsit — creez 'Reduceri România'...")
                try:
                    create_btn = page.locator('button:has-text("Creează panou"), button:has-text("Create board")').first
                    if create_btn.is_visible(timeout=3000):
                        create_btn.click()
                        human_delay(2, 3)
                        # Completează numele board-ului
                        name_input = page.locator('input[placeholder*="panou" i], input[placeholder*="board" i], input[name="boardName"]').first
                        if name_input.is_visible(timeout=3000):
                            name_input.fill("Reduceri România — GhidulReducerilor")
                            human_delay(1, 2)
                            # Click Create / Crează
                            confirm_btn = page.locator('button:has-text("Creează"), button:has-text("Create"), button[type="submit"]').last
                            confirm_btn.click()
                            human_delay(2, 3)
                            print(f"[pinterest] ✅ Board 'Reduceri România' creat")
                except Exception as be:
                    print(f"[pinterest] Create board: {be}")
        else:
            print(f"[pinterest] ⚠️  Board dropdown negăsit — continuăm fără board")

        human_delay(1, 2)
        # Screenshot înainte de publicare
        take_screenshot(page, f"before_pin_{titlu_short.replace(' ', '_')[:20]}")

        # ── Publică ────────────────────────────────────────────────────────────
        publish_selectors = [
            '[data-test-id="board-dropdown-save-button"]',
            '[data-test-id="pin-draft-save-button"]',
            'button:has-text("Publică")',
            'button:has-text("Salvează")',
            'button:has-text("Publish")',
            'button:has-text("Save")',
        ]
        published = False
        for sel in publish_selectors:
            try:
                btn = page.locator(sel).last
                if btn.is_visible(timeout=3000):
                    # Verifică dacă e disabled
                    disabled = btn.get_attribute("disabled")
                    aria_disabled = btn.get_attribute("aria-disabled")
                    if disabled is not None or aria_disabled == "true":
                        print(f"[pinterest] Buton '{sel}' e disabled — skip")
                        continue
                    btn.click()
                    published = True
                    print(f"[pinterest] ✅ Buton Publică apăsat")
                    break
            except Exception:
                continue

        if not published:
            print(f"[pinterest] ⚠️  Butonul Publică negăsit sau disabled")
            take_screenshot(page, f"no_publish_btn_{titlu_short[:15]}")
            return False

        human_delay(4, 6)
        take_screenshot(page, f"pin_posted_{titlu_short.replace(' ', '_')[:20]}")
        print(f"[pinterest] ✅ Pin publicat în board '{board}'")
        return True

    except Exception as e:
        print(f"[pinterest] Eroare la pin: {e}")
        try:
            take_screenshot(page, f"pin_error_{titlu_short[:15]}")
        except Exception:
            pass
        return False
    finally:
        if tmp_image:
            try:
                os.unlink(tmp_image)
            except Exception:
                pass


# ─── Login automat (fără Enter manual) ───────────────────────────────────────

def login_auto():
    """
    Deschide Pinterest în Chrome real și DETECTEAZĂ automat login-ul manual.
    Te loghezi tu în fereastră (email/parolă sau Google — cum vrei); agentul
    verifică la fiecare 2s dacă ai ajuns pe o pagină Pinterest logată și salvează
    sesiunea singur, fără ENTER. Nicio parolă nu e stocată sau completată de agent.
    """
    from playwright.sync_api import sync_playwright

    cfg   = load_config()
    email = cfg.get("email", "")

    # Șterge profilul vechi (sesiune invalidă)
    import shutil
    if PROFILE_DIR.exists():
        shutil.rmtree(PROFILE_DIR, ignore_errors=True)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    print("\n=== LOGIN PINTEREST (AUTO, Chrome real — login manual detectat automat) ===")
    if email:
        print(f"Email pre-completat: {email}")

    with sync_playwright() as p:
        # Folosim Chrome-ul real instalat — Google nu îl blochează ca bot
        try:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                channel="chrome",          # Chrome real, nu Chromium
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
                viewport={"width": 1280, "height": 900},
                locale="ro-RO",
            )
        except Exception:
            # Fallback la Chromium dacă Chrome nu e găsit
            print("[pinterest] Chrome real negăsit, folosesc Chromium...")
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                locale="ro-RO",
            )

        page = ctx.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)

        # 1. Navighează la login
        print("[pinterest] Se deschide login-ul — loghează-te MANUAL în fereastră.")
        page.goto("https://www.pinterest.com/login/", wait_until="domcontentloaded")
        human_delay(3, 5)

        # 2. Comoditate: pre-completează doar emailul, dacă e cunoscut. Parola o introduci tu.
        if email:
            try:
                page.wait_for_selector('input[name="id"]', timeout=8000)
                page.fill('input[name="id"]', email)
            except Exception:
                pass

        # 3. Așteptare confirmare login (max 2 minute)
        # Verifică TOATE paginile/tab-urile din context (Google OAuth deschide tab nou)
        print("[pinterest] Verific sesiunea pe toate tab-urile...")
        logged_in = False
        for i in range(60):
            time.sleep(2)
            try:
                all_pages = ctx.pages
                for pg in all_pages:
                    url = pg.url
                    if not url or url in ("about:blank", "chrome://newtab/"):
                        continue
                    if "login" in url or "/login" in url:
                        continue
                    if "google.com" in url or "accounts.google" in url:
                        continue
                    # E o pagină Pinterest, nu login
                    if "pinterest.com" in url:
                        logged_in = True
                        print(f"\n[pinterest] ✅ LOGIN REUȘIT! URL: {url}")
                        break
                if logged_in:
                    break
                if i % 10 == 0 and i > 0:
                    urls = [pg.url for pg in ctx.pages]
                    print(f"[pinterest] Aștept... ({i*2}s) tab-uri: {urls}")
            except Exception:
                pass

        if logged_in:
            human_delay(3, 4)
            take_screenshot(page, "login_auto_ok")
            print(f"[pinterest] ✅ Sesiune salvată în: {PROFILE_DIR}")
        else:
            take_screenshot(page, "login_auto_failed")
            print(f"[pinterest] ⚠️  Login nereușit. Screenshot salvat în logs/pinterest/")

        ctx.close()


# ─── Setup ────────────────────────────────────────────────────────────────────

def setup():
    """Pas OPȚIONAL: salvează doar preferințe (email pt. pre-completare, pin-uri/zi).
    Parola NU se cere și NU se stochează — login-ul e manual (vezi --login)."""
    print("\n=== SETUP Pinterest Auto-Poster (opțional, fără parolă) ===\n")
    print("Login-ul e manual în browser — aici salvezi doar preferințe.\n")
    email        = input("Email Pinterest (opțional, doar pre-completare): ").strip()
    pins_per_day = input("Câte pin-uri/zi (3-5, recomandat 3): ").strip() or "3"

    cfg = {
        "email":           email,
        "pins_per_day":    int(pins_per_day),
        "post_hour_start": 12,
        "post_hour_end":   22,
    }
    save_config(cfg)
    print(f"\n✅ Config salvat: {CONFIG}")
    print("\nPasul următor (login manual, fără parolă stocată):")
    print("  python agents/marketing/pinterest_agent.py --login")


# ─── Runner principal ─────────────────────────────────────────────────────────

def run(dry_run: bool = False):
    # Config-ul e OPȚIONAL — merge și fără el (setup nu mai e obligatoriu).
    cfg = load_config()

    # Verifică ora
    hour = datetime.now().hour
    start = cfg.get("post_hour_start", 12)
    end   = cfg.get("post_hour_end", 22)
    if not (start <= hour <= end) and not dry_run:
        print(f"[pinterest] Ora {hour} în afara ferestrei ({start}-{end}). Skip.")
        return

    pins_per_day = cfg.get("pins_per_day", 3)

    deals = select_deals_for_pinterest(pins_per_day)
    if not deals:
        print("[pinterest] Niciun deal eligibil pentru Pinterest azi.")
        return

    print(f"\n[pinterest] {len(deals)} deals selectate pentru Pinterest:")
    for d in deals:
        pct = d.get("procent_reducere") or d.get("discount_percent") or 0
        titlu = (d.get("titlu") or d.get("title") or "")[:50]
        print(f"  {pct}% | {d.get('magazin','')} | {titlu}")

    if dry_run:
        print("\n[pinterest] DRY-RUN — nu se deschide browserul")
        return

    # Verifică profil browser (doar pentru postarea reală — dry-run nu are nevoie de login)
    if not PROFILE_DIR.exists() or not any(PROFILE_DIR.iterdir()):
        print("[pinterest] Profil browser lipsă. Rulează: --login")
        sys.exit(1)

    from playwright.sync_api import sync_playwright

    results = []
    with sync_playwright() as p:
        # Folosim Chrome real (același cu login_auto) pentru compatibilitate profil
        try:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                channel="chrome",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
                viewport={"width": 1280, "height": 900},
                locale="ro-RO",
            )
        except Exception:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIR),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                viewport={"width": 1280, "height": 900},
                locale="ro-RO",
            )
        page = ctx.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        # Verifică sesiunea
        page.goto("https://www.pinterest.com/", wait_until="domcontentloaded")
        human_delay(2, 3)
        content = page.content()
        # Detectează pagina de landing (nelogat) după elemente specifice
        not_logged_in = any(kw in content for kw in [
            "Conectează-te", "Log in", "Sign up", "Înregistrează-te",
            "Găsește-ți", "Find your next", "create-account",
        ])
        if not_logged_in or "login" in page.url or "/login" in page.url:
            print("[pinterest] ⚠️  Sesiunea Pinterest a expirat sau nu ești logat.")
            print("[pinterest]    Rulează: python agents/marketing/pinterest_agent.py --login")
            ctx.close()
            return

        print("[pinterest] ✅ Sesiune Pinterest validă")

        promo_log = load_promo_log()
        now_iso = datetime.now().isoformat()

        for i, deal in enumerate(deals):
            success = post_pin(page, deal, dry_run=dry_run)
            results.append({
                "deal_id":  deal.get("id"),
                "titlu":    (deal.get("titlu") or deal.get("title") or "")[:60],
                "board":    board_for_deal(deal),
                "success":  success,
                "time":     now_iso,
            })
            if success:
                promo_log[deal.get("id", "")] = now_iso

            # Pauza între pin-uri (comportament uman)
            if i < len(deals) - 1:
                delay = random.uniform(45, 120)
                print(f"[pinterest] Aștept {delay:.0f}s...")
                time.sleep(delay)

        ctx.close()
        save_promo_log(promo_log)

    # Log
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    ok = sum(1 for r in results if r["success"])
    print(f"\n[pinterest] Finalizat: {ok}/{len(results)} pin-uri publicate")
    print(f"[pinterest] Log: {log_path}")
    return results


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pinterest Auto-Poster — ghidulreducerilor.ro")
    parser.add_argument("--setup",      action="store_true", help="Opțional: salvează preferințe (fără parolă)")
    parser.add_argument("--login",      action="store_true", help="Login MANUAL în browser + ENTER (fără parolă stocată)")
    parser.add_argument("--login-auto", action="store_true", help="Login manual detectat automat (fără ENTER, fără parolă)")
    parser.add_argument("--run",        action="store_true", help="Postare pin-uri")
    parser.add_argument("--dry-run",    action="store_true", help="Test fără postare (arată deals selectate)")
    args = parser.parse_args()

    if args.setup:
        setup()
    elif args.login:
        login_interactive()
    elif args.login_auto:
        login_auto()
    elif args.run:
        run(dry_run=False)
    elif args.dry_run:
        run(dry_run=True)
    else:
        parser.print_help()
