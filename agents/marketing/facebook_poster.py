"""
facebook_poster.py — Postează automat în grupuri Facebook folosind Playwright.

Rulează LOCAL (pe calculatorul tău), nu în GitHub Actions.
Citește posturile generate de facebook_agent.py și le publică în grupurile configurate.

Setup prima dată:
  python agents/marketing/facebook_poster.py --setup

Rulare zilnică (via Task Scheduler):
  python agents/marketing/facebook_poster.py --run

Config: agents/marketing/fb_config_local.json (NU se commitează pe GitHub)
"""

import json
import time
import random
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

BASE        = Path(__file__).parent.parent.parent
POSTS_DIR   = BASE / "data" / "marketing"
LOG_DIR     = BASE / "logs" / "fb_poster"
CONFIG      = Path(__file__).parent / "fb_config_local.json"
SESSION     = Path(__file__).parent / "fb_session.json"       # cookie session (legacy)
PROFILE_DIR = Path(__file__).parent / "fb_browser_profile"    # profil persistent Playwright

# ─── Grupuri Facebook țintă (URL-uri) ────────────────────────────────────────
DEFAULT_GROUPS = [
    {
        "name": "Oferte Romania",
        "url": "https://www.facebook.com/groups/oferteromania",
        "post_types": ["deal_simplu", "lista_top"],
    },
    {
        "name": "Reduceri Romania",
        "url": "https://www.facebook.com/groups/reduceriromania",
        "post_types": ["comparatie_pret", "lista_top"],
    },
    {
        "name": "Vânătoare de chilipiruri",
        "url": "https://www.facebook.com/groups/vanatoaredechilipiruri",
        "post_types": ["urgenta", "story_personal"],
    },
    {
        "name": "Oferte și Reduceri Online Romania",
        "url": "https://www.facebook.com/groups/ofertesireducerionlineromania",
        "post_types": ["deal_simplu", "comparatie_pret"],
    },
    {
        "name": "Economisim impreuna",
        "url": "https://www.facebook.com/groups/economisimipreuna",
        "post_types": ["lista_top", "urgenta"],
    },
]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG.exists():
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(cfg: dict):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def load_today_posts() -> dict | None:
    today = datetime.now().strftime("%Y-%m-%d")
    path = POSTS_DIR / f"fb_posts_{today}.json"
    if not path.exists():
        # Încearcă cele mai recente 3 zile
        for i in range(1, 4):
            from datetime import timedelta
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            path = POSTS_DIR / f"fb_posts_{d}.json"
            if path.exists():
                print(f"[poster] Folosesc posturi din {d} (cele din azi lipsesc)")
                break
        else:
            return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def human_delay(min_s: float = 1.5, max_s: float = 4.0):
    """Pauză aleatorie pentru a imita comportament uman."""
    time.sleep(random.uniform(min_s, max_s))


def human_type(page, selector: str, text: str):
    """Tastare umană — caracter cu caracter, cu mici pauze."""
    el = page.locator(selector).first
    el.click()
    for char in text:
        el.type(char)
        time.sleep(random.uniform(0.03, 0.12))


def take_screenshot(page, name: str) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name}.png"
    page.screenshot(path=str(path))
    return path


# ─── Login / Session ─────────────────────────────────────────────────────────

def login_facebook(page, email: str, password: str) -> bool:
    """Login Facebook și salvează sesiunea."""
    print("[poster] Login Facebook...")
    page.goto("https://www.facebook.com/", wait_until="networkidle")
    human_delay(2, 4)

    # Acceptă cookies dacă apare (multiple variante de dialog)
    cookie_texts = [
        "Permite toate modulele cookie",   # varianta noua 2024+
        "Permite toate cookie-urile",
        "Allow all cookies",
        "Accept all",
        "Acceptă tot",
    ]
    cookie_accepted = False
    try:
        page.locator('[data-testid="cookie-policy-manage-dialog-accept-button"]').click(timeout=3000)
        cookie_accepted = True
        human_delay()
    except Exception:
        pass
    if not cookie_accepted:
        for txt in cookie_texts:
            try:
                page.get_by_text(txt, exact=True).first.click(timeout=2000)
                cookie_accepted = True
                human_delay()
                break
            except Exception:
                continue
    if not cookie_accepted:
        # Fallback: primul buton din dialog (de obicei "Permite toate")
        try:
            page.locator('div[role="dialog"] button').first.click(timeout=2000)
            human_delay()
            cookie_accepted = True
        except Exception:
            pass

    # Dacă am aterizat pe pagina de management cookie (click greșit), ieșim
    human_delay(1, 2)
    if "cookie" in page.url.lower() or page.locator('text="Module cookie de la alte companii"').count() > 0:
        print("[poster] ⚠️  Am nimerit pe pagina de setări cookie — navighez înapoi")
        page.goto("https://www.facebook.com/", wait_until="networkidle")
        human_delay(2, 3)
        # Încearcă din nou cu data-testid direct
        for txt in ["Permite toate modulele cookie", "Permite toate cookie-urile", "Allow all cookies"]:
            try:
                page.get_by_text(txt, exact=True).first.click(timeout=3000)
                human_delay()
                break
            except Exception:
                continue

    try:
        page.fill("#email", email)
        human_delay(0.5, 1.5)
        page.fill("#pass", password)
        human_delay(0.5, 1.5)
        page.click('[name="login"]')
        page.wait_for_url("**/facebook.com/**", timeout=15000)
        human_delay(2, 4)

        # Verifică dacă suntem logați
        if "login" in page.url or "checkpoint" in page.url:
            print("[poster] ⚠️  Login eșuat sau checkpoint de securitate!")
            take_screenshot(page, "login_failed")
            return False

        print("[poster] ✅ Login reușit")
        # Salvare sesiune (cookies)
        cookies = page.context.cookies()
        SESSION.write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        print(f"[poster] Login error: {e}")
        take_screenshot(page, "login_error")
        return False


def restore_session(context) -> bool:
    """Restaurează sesiunea salvată."""
    if not SESSION.exists():
        return False
    try:
        cookies = json.loads(SESSION.read_text(encoding="utf-8"))
        context.add_cookies(cookies)
        return True
    except Exception:
        return False


# ─── Postare în grup ─────────────────────────────────────────────────────────

def post_to_group(page, group: dict, post_text: str) -> bool:
    """Navighează la grup și postează textul."""
    group_url = group["url"]
    group_name = group["name"]
    print(f"\n[poster] → Postare în: {group_name}")

    try:
        page.goto(group_url, wait_until="domcontentloaded", timeout=20000)
        human_delay(3, 6)

        # Verifică dacă suntem în grup
        if "login" in page.url:
            print(f"[poster] ⚠️  Redirect la login — sesiunea a expirat")
            return False

        # Click pe câmpul de postare
        post_box_selectors = [
            '[aria-label="Scrie ceva..."]',
            '[aria-label="Write something..."]',
            '[data-testid="status-attachment-mentions-input"]',
            'div[role="button"][tabindex="0"]',
        ]
        clicked = False
        for sel in post_box_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.click()
                    clicked = True
                    break
            except Exception:
                continue

        if not clicked:
            # Încearcă click direct pe zona de creare post
            try:
                page.get_by_placeholder("Scrie ceva").first.click(timeout=5000)
                clicked = True
            except Exception:
                pass

        if not clicked:
            print(f"[poster] ⚠️  Nu am găsit câmpul de postare în {group_name}")
            take_screenshot(page, f"no_postbox_{group_name.replace(' ', '_')[:20]}")
            return False

        human_delay(1, 2)

        # Tastează textul
        page.keyboard.type(post_text, delay=random.randint(30, 80))
        human_delay(2, 4)

        # Captează screenshot înainte de post
        take_screenshot(page, f"before_post_{group_name.replace(' ', '_')[:20]}")

        # Click pe butonul de postare
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
                page.get_by_role("button", name="Postează").click(timeout=5000)
                posted = True
            except Exception:
                pass

        if not posted:
            print(f"[poster] ⚠️  Nu am găsit butonul Postează în {group_name}")
            take_screenshot(page, f"no_postbtn_{group_name.replace(' ', '_')[:20]}")
            return False

        human_delay(3, 6)
        take_screenshot(page, f"posted_{group_name.replace(' ', '_')[:20]}")
        print(f"[poster] ✅ Postat în {group_name}")
        return True

    except Exception as e:
        print(f"[poster] Eroare la {group_name}: {e}")
        try:
            take_screenshot(page, f"error_{group_name.replace(' ', '_')[:20]}")
        except Exception:
            pass
        return False


# ─── Setup interactiv ─────────────────────────────────────────────────────────

def setup():
    """Prima configurare — salvează credentials și grupuri."""
    print("\n=== SETUP Facebook Auto-Poster ===\n")
    print("Credentialele se salvează LOCAL pe calculatorul tău (nu pe GitHub).\n")

    email    = input("Email Facebook: ").strip()
    password = input("Parolă Facebook: ").strip()
    posts_per_day = input("Câte posturi/zi (1-3, recomandat 2): ").strip() or "2"

    print("\nGrupuri disponibile:")
    for i, g in enumerate(DEFAULT_GROUPS, 1):
        print(f"  {i}. {g['name']}")
    selected = input("\nAlege grupuri (ex: 1,2,3 sau Enter pentru toate): ").strip()
    if selected:
        indices = [int(x.strip()) - 1 for x in selected.split(",") if x.strip().isdigit()]
        groups = [DEFAULT_GROUPS[i] for i in indices if 0 <= i < len(DEFAULT_GROUPS)]
    else:
        groups = DEFAULT_GROUPS

    cfg = {
        "email":          email,
        "password":       password,
        "posts_per_day":  int(posts_per_day),
        "groups":         groups,
        "max_groups_per_run": 3,
        "post_hour_start": 8,   # Nu postăm înainte de ora 8
        "post_hour_end":   21,  # Nu postăm după ora 21
    }
    save_config(cfg)
    print(f"\n✅ Config salvat: {CONFIG}")

    # Test login
    test = input("\nTestezi login-ul acum? (y/N): ").strip().lower()
    if test == "y":
        run_poster(dry_run=True, test_login_only=True)


# ─── Login interactiv (prima dată) ───────────────────────────────────────────

def _auto_accept_cookies(page):
    """Acceptă automat dialogul de cookies Facebook.
    Scrollează dialogul la capăt (unde sunt butoanele) și dă click pe Accept."""

    # Încearcă de mai multe ori — dialogul se poate încărca lent
    for attempt in range(6):
        time.sleep(1.5)
        try:
            # Varianta 1: Playwright locator direct pe text
            for txt in ["Permite toate modulele cookie", "Permite toate cookie-urile", "Allow all cookies"]:
                try:
                    btn = page.get_by_text(txt, exact=True).first
                    if btn.count() > 0:
                        btn.scroll_into_view_if_needed(timeout=2000)
                        btn.click(timeout=2000)
                        print(f"[poster] ✅ Cookie acceptat: '{txt}'")
                        return
                except Exception:
                    pass

            # Varianta 2: scroll dialog la capăt + JS click
            result = page.evaluate("""
                (function() {
                    // Scroll toate containerele scrollabile la capăt
                    document.querySelectorAll('[role="dialog"]').forEach(d => {
                        d.scrollTop = d.scrollHeight;
                        d.querySelectorAll('*').forEach(el => {
                            if (el.scrollHeight > el.clientHeight) el.scrollTop = el.scrollHeight;
                        });
                    });

                    const keywords = ['Permite toate modulele cookie', 'Permite toate cookie', 'Allow all', 'Accept all'];
                    const allEls = Array.from(document.querySelectorAll('button, [role="button"], a'));
                    for (const kw of keywords) {
                        const el = allEls.find(e => e.innerText && e.innerText.trim().includes(kw));
                        if (el) {
                            el.scrollIntoView({block:'center'});
                            el.click();
                            return 'js_clicked:' + kw;
                        }
                    }
                    return 'not_found_attempt_' + arguments[0];
                })(""" + str(attempt) + """)
            """)

            if result and "js_clicked" in str(result):
                print(f"[poster] ✅ Cookie acceptat via JS: {result}")
                return
        except Exception:
            pass

    print("[poster] ⚠️  Cookie dialog nerezolvat după 6 încercări — continuăm oricum")


def login_interactive():
    """Deschide browserul cu login automat Facebook.
    Acceptă cookies automat via JS, completează email/parolă din config,
    salvează profilul pe disc — rulările ulterioare nu mai cer nimic."""
    from playwright.sync_api import sync_playwright

    cfg = load_config()
    email    = cfg.get("email", "") if cfg else ""
    password = cfg.get("password", "") if cfg else ""

    if not email or not password:
        print("[poster] ⚠️  Email/parolă lipsă. Rulează mai întâi: --setup")
        sys.exit(1)

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    print("\n=== LOGIN AUTOMAT ===")
    print(f"Email: {email}")
    print("Browserul se deschide și se loghează automat...\n")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ro-RO",
        )
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
        """)

        # Navighează direct la login
        page.goto("https://www.facebook.com/login", wait_until="domcontentloaded")
        human_delay(2, 3)

        # Acceptă cookies automat
        _auto_accept_cookies(page)
        human_delay(1, 2)

        # Completează login
        try:
            page.fill("#email", email)
            human_delay(0.5, 1)
            page.fill("#pass", password)
            human_delay(0.5, 1)
            page.click('[name="login"]')
            page.wait_for_url("**/facebook.com/**", timeout=20000)
            human_delay(2, 3)

            if "login" in page.url or "checkpoint" in page.url:
                print("[poster] ⚠️  Login eșuat sau checkpoint de securitate!")
                print("         Verifică manual browserul și apasă ENTER când ești logat.")
                take_screenshot(page, "login_failed")
                input(">>> Apasă ENTER după ce te-ai logat manual: ")
            else:
                print("[poster] ✅ Login reușit automat!")
                take_screenshot(page, "login_interactive_ok")
        except Exception as e:
            print(f"[poster] Eroare login: {e}")
            print("         Loghează-te manual în browser și apasă ENTER.")
            input(">>> Apasă ENTER după ce te-ai logat: ")

        # Verifică final
        if "facebook.com" in page.url and "login" not in page.url:
            print(f"[poster] ✅ Profil salvat în: {PROFILE_DIR}")
        else:
            print("[poster] ⚠️  Nu s-a detectat login. Verifică credențialele.")

        context.close()


# ─── Runner principal ─────────────────────────────────────────────────────────

def run_poster(dry_run: bool = False, test_login_only: bool = False):
    """Rulare principală cu profil browser persistent (fără re-login / cookie dialogs)."""
    from playwright.sync_api import sync_playwright

    cfg = load_config()
    if not cfg:
        print("[poster] Config lipsă. Rulează: python facebook_poster.py --setup")
        sys.exit(1)

    groups     = cfg.get("groups", DEFAULT_GROUPS[:2])
    max_groups = cfg.get("max_groups_per_run", 3)

    # Verifică că există profilul browser (login interactiv făcut)
    if not PROFILE_DIR.exists() or not any(PROFILE_DIR.iterdir()):
        print("[poster] ⚠️  Profilul browser lipsă. Rulează mai întâi:")
        print("         python facebook_poster.py --login")
        sys.exit(1)

    # Verifică ora (nu postăm noaptea)
    hour = datetime.now().hour
    start_h = cfg.get("post_hour_start", 8)
    end_h   = cfg.get("post_hour_end", 21)
    if not (start_h <= hour <= end_h) and not dry_run:
        print(f"[poster] Ora {hour} e în afara ferestrei de postare ({start_h}-{end_h}). Skip.")
        return

    if not dry_run and not test_login_only:
        posts_data = load_today_posts()
        if not posts_data or not posts_data.get("posts"):
            print("[poster] Nu există posturi generate pentru azi. Rulează orchestrator.py mai întâi.")
            return
        all_posts = {p["tip"]: p for p in posts_data["posts"]}
    else:
        all_posts = {}

    with sync_playwright() as p:
        # Profil persistent — nu mai apar cookie dialogs sau login
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ro-RO",
        )
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
        """)

        # Verifică că suntem logați
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        human_delay(2, 3)

        if "login" in page.url:
            print("[poster] ⚠️  Sesiunea a expirat. Rulează: python facebook_poster.py --login")
            take_screenshot(page, "session_expired")
            context.close()
            return

        print("[poster] ✅ Logat pe Facebook (profil persistent)")

        if test_login_only:
            take_screenshot(page, "login_test_ok")
            print("[poster] Test login OK!")
            context.close()
            return

        if dry_run:
            print("[poster] DRY-RUN — nu se postează")
            context.close()
            return

        # Postare în grupuri
        results = []
        groups_to_post = groups[:max_groups]

        for group in groups_to_post:
            # Alege tipul de post potrivit pentru grupul acesta
            post_types = group.get("post_types", ["deal_simplu"])
            post = None
            for pt in post_types:
                if pt in all_posts:
                    post = all_posts[pt]
                    del all_posts[pt]  # nu refolosi același post
                    break
            if not post:
                # Fallback: primul disponibil
                if all_posts:
                    post = next(iter(all_posts.values()))

            if not post:
                print(f"[poster] Nu mai sunt posturi disponibile pentru {group['name']}")
                break

            success = post_to_group(page, group, post["text"])
            results.append({
                "group":    group["name"],
                "post_tip": post["tip"],
                "success":  success,
                "time":     datetime.now().isoformat(),
            })

            # Pauză lungă între grupuri (comportament uman)
            if group != groups_to_post[-1]:
                delay = random.uniform(120, 300)  # 2-5 minute între posturi
                print(f"[poster] Aștept {delay:.0f}s până la următorul grup...")
                time.sleep(delay)

        context.close()

        # Salvare log
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        success_count = sum(1 for r in results if r["success"])
        print(f"\n[poster] Finalizat: {success_count}/{len(results)} posturi publicate")
        print(f"[poster] Log: {log_path}")
        return results


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Facebook Auto-Poster pentru ghidulreducerilor.ro")
    parser.add_argument("--setup",    action="store_true", help="Configurare inițială (email/parolă/grupuri)")
    parser.add_argument("--login",    action="store_true", help="Login interactiv — loghează-te manual în browser (prima dată)")
    parser.add_argument("--run",      action="store_true", help="Rulare postare")
    parser.add_argument("--dry-run",  action="store_true", help="Test fără postare (verifică login)")
    args = parser.parse_args()

    if args.setup:
        setup()
    elif args.login:
        login_interactive()
    elif args.run:
        run_poster(dry_run=False)
    elif args.dry_run:
        run_poster(dry_run=True)
    else:
        parser.print_help()
