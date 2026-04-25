"""
pinterest_agent.py — Postare automată pe Pinterest.

Strategie:
  - Board per categorie (casa-gradina, beauty, electronice, ceasuri, etc.)
  - 3-5 pin-uri/zi, ore de vârf (12:00-14:00 și 20:00-22:00 RO)
  - Titlu + descriere SEO optimizate în română
  - Link direct la /out/{id} (tracker afiliat)
  - Profilul browser persistent — login o singură dată manual

Setup prima dată:
  python agents/marketing/pinterest_agent.py --setup
  python agents/marketing/pinterest_agent.py --login

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
    "casa-gradina":      "Casa și Grădină — Reduceri",
    "beauty":            "Beauty & Cosmetice — Reduceri",
    "farmacie-sanatate": "Sănătate & Farmacie — Oferte",
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
    """Deschide Pinterest, completează login automat, salvează profilul."""
    from playwright.sync_api import sync_playwright

    cfg = load_config()
    email    = cfg.get("email", "")
    password = cfg.get("password", "")

    if not email or not password:
        print("[pinterest] Email/parolă lipsă. Rulează mai întâi: --setup")
        sys.exit(1)

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    print("\n=== LOGIN PINTEREST ===")
    print(f"Email: {email}")

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

        print("[pinterest] Navighez la login...")
        page.goto("https://www.pinterest.com/login/", wait_until="domcontentloaded")
        human_delay(3, 5)

        try:
            page.fill('input[name="id"]', email, timeout=10000)
            human_delay(0.5, 1)
            page.fill('input[name="password"]', password, timeout=10000)
            human_delay(0.5, 1)
            page.locator('button[type="submit"]').click(timeout=5000)
            human_delay(4, 6)

            if "login" in page.url:
                print("[pinterest] Login eșuat sau 2FA — completează manual în browser.")
                take_screenshot(page, "login_failed")
            else:
                print(f"[pinterest] ✅ Login OK! URL: {page.url}")
                take_screenshot(page, "login_ok")
        except Exception as e:
            print(f"[pinterest] Eroare: {e}")
            print("         Loghează-te manual și apasă ENTER.")

        input(">>> Apasă ENTER după ce ești logat pe Pinterest: ")
        print(f"[pinterest] ✅ Profil salvat: {PROFILE_DIR}")
        ctx.close()


# ─── Postare pin ──────────────────────────────────────────────────────────────

def post_pin(page, deal: dict, dry_run: bool = False) -> bool:
    """Postează un pin pe Pinterest."""
    board = board_for_deal(deal)
    title = pin_title(deal)
    desc  = pin_description(deal)
    link  = deal_link(deal)
    image = deal.get("imagine_url") or deal.get("image") or ""
    titlu_short = (deal.get("titlu") or deal.get("title") or "")[:30]

    print(f"\n[pinterest] → Pin: {titlu_short}...")
    print(f"              Board: {board}")
    print(f"              Link:  {link}")

    if dry_run:
        print(f"[pinterest] DRY-RUN — skip postare")
        return True

    try:
        # Navighează la creator
        page.goto("https://www.pinterest.com/pin-creation-tool/", wait_until="domcontentloaded")
        human_delay(3, 5)

        if "login" in page.url:
            print("[pinterest] ⚠️  Sesiunea a expirat. Rulează --login")
            return False

        # ── Upload imagine (via URL) sau din imagine_url ──────────────────────
        # Pinterest permite upload via URL din interfață
        # Așteptăm să apară câmpul de upload
        try:
            # Încearcă să găsească câmpul "URL imagine" sau "pin from website"
            page.wait_for_selector('[data-test-id="pin-draft-image-upload"]', timeout=8000)
        except Exception:
            pass

        # Fallback: "Salvează de pe site" — introduce URL-ul direct
        save_btn_selectors = [
            'button:has-text("Salvează dintr-un site")',
            'button:has-text("Save from site")',
            '[data-test-id="storybook-pin-creation-save-from-url"]',
        ]
        for sel in save_btn_selectors:
            try:
                if page.locator(sel).is_visible(timeout=2000):
                    page.locator(sel).click()
                    human_delay(1, 2)
                    break
            except Exception:
                continue

        # Introduce URL-ul de imagine în câmpul de URL
        url_input_selectors = [
            'input[placeholder*="imagine"]',
            'input[placeholder*="image"]',
            'input[placeholder*="URL"]',
            '[data-test-id="pin-draft-image-url-input"] input',
        ]
        image_url_entered = False
        if image:
            for sel in url_input_selectors:
                try:
                    inp = page.locator(sel).first
                    if inp.is_visible(timeout=2000):
                        inp.fill(image, timeout=3000)
                        human_delay(0.5, 1)
                        image_url_entered = True
                        break
                except Exception:
                    continue

        # ── Titlu ──────────────────────────────────────────────────────────────
        title_selectors = [
            '[placeholder="Adaugă titlu"]',
            '[placeholder="Add a title"]',
            '[data-test-id="pin-draft-title"] input',
            'input[name="title"]',
        ]
        for sel in title_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.click()
                    el.fill(title[:100])
                    break
            except Exception:
                continue
        human_delay(0.5, 1)

        # ── Descriere ──────────────────────────────────────────────────────────
        desc_selectors = [
            '[placeholder="Spune mai multe despre Pin-ul tău"]',
            '[placeholder="Tell everyone what your Pin is about"]',
            '[data-test-id="pin-draft-description"] textarea',
            'textarea[name="description"]',
        ]
        for sel in desc_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.click()
                    el.fill(desc[:500])
                    break
            except Exception:
                continue
        human_delay(0.5, 1)

        # ── Link destinație ────────────────────────────────────────────────────
        link_selectors = [
            '[placeholder="Adaugă un link"]',
            '[placeholder="Add a link"]',
            '[data-test-id="pin-draft-link"] input',
            'input[name="link"]',
        ]
        for sel in link_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.click()
                    el.fill(link)
                    break
            except Exception:
                continue
        human_delay(0.5, 1)

        # ── Selectare board ────────────────────────────────────────────────────
        board_selectors = [
            '[data-test-id="board-dropdown-select-button"]',
            'button:has-text("Alege un board")',
            'button:has-text("Choose a board")',
        ]
        board_opened = False
        for sel in board_selectors:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=3000):
                    el.click()
                    human_delay(1, 2)
                    board_opened = True
                    break
            except Exception:
                continue

        if board_opened:
            # Caută board-ul după nume
            try:
                page.get_by_text(board, exact=False).first.click(timeout=5000)
                human_delay(1, 2)
            except Exception:
                # Fallback: primul board disponibil
                try:
                    page.locator('[data-test-id="board-row"]').first.click(timeout=3000)
                    human_delay(1, 2)
                except Exception:
                    pass

        # Screenshot înainte de publicare
        take_screenshot(page, f"before_pin_{titlu_short.replace(' ', '_')[:20]}")

        # ── Publică ────────────────────────────────────────────────────────────
        publish_selectors = [
            'button:has-text("Publică")',
            'button:has-text("Publish")',
            '[data-test-id="board-dropdown-save-button"]',
        ]
        published = False
        for sel in publish_selectors:
            try:
                btn = page.locator(sel).last
                if btn.is_visible(timeout=3000):
                    btn.click()
                    published = True
                    break
            except Exception:
                continue

        if not published:
            print(f"[pinterest] ⚠️  Butonul Publică negăsit")
            take_screenshot(page, f"no_publish_btn_{titlu_short[:15]}")
            return False

        human_delay(3, 5)
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


# ─── Setup ────────────────────────────────────────────────────────────────────

def setup():
    print("\n=== SETUP Pinterest Auto-Poster ===\n")
    email    = input("Email Pinterest: ").strip()
    password = input("Parolă Pinterest: ").strip()
    pins_per_day = input("Câte pin-uri/zi (3-5, recomandat 3): ").strip() or "3"

    print("\nBoard-uri care vor fi create pe Pinterest:")
    for cat, board in BOARD_MAP.items():
        print(f"  → {board}")

    cfg = {
        "email":          email,
        "password":       password,
        "pins_per_day":   int(pins_per_day),
        "post_hour_start": 12,
        "post_hour_end":   22,
    }
    save_config(cfg)
    print(f"\n✅ Config salvat: {CONFIG}")
    print("\nPasul următor:")
    print("  python agents/marketing/pinterest_agent.py --login")
    print("\nDupă login, creează manual board-urile pe pinterest.com:")
    for board in set(BOARD_MAP.values()):
        print(f"  → '{board}'")


# ─── Runner principal ─────────────────────────────────────────────────────────

def run(dry_run: bool = False):
    cfg = load_config()
    if not cfg:
        print("[pinterest] Config lipsă. Rulează: --setup")
        sys.exit(1)

    # Verifică ora
    hour = datetime.now().hour
    start = cfg.get("post_hour_start", 12)
    end   = cfg.get("post_hour_end", 22)
    if not (start <= hour <= end) and not dry_run:
        print(f"[pinterest] Ora {hour} în afara ferestrei ({start}-{end}). Skip.")
        return

    pins_per_day = cfg.get("pins_per_day", 3)

    # Verifică profil browser
    if not PROFILE_DIR.exists() or not any(PROFILE_DIR.iterdir()):
        print("[pinterest] Profil browser lipsă. Rulează: --login")
        sys.exit(1)

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

    from playwright.sync_api import sync_playwright

    results = []
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

        # Verifică sesiunea
        page.goto("https://www.pinterest.com/", wait_until="domcontentloaded")
        human_delay(2, 3)
        if "login" in page.url:
            print("[pinterest] ⚠️  Sesiunea Pinterest a expirat. Rulează: --login")
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
    parser.add_argument("--setup",   action="store_true", help="Configurare inițială")
    parser.add_argument("--login",   action="store_true", help="Login interactiv (prima dată)")
    parser.add_argument("--run",     action="store_true", help="Postare pin-uri")
    parser.add_argument("--dry-run", action="store_true", help="Test fără postare (arată deals selectate)")
    args = parser.parse_args()

    if args.setup:
        setup()
    elif args.login:
        login_interactive()
    elif args.run:
        run(dry_run=False)
    elif args.dry_run:
        run(dry_run=True)
    else:
        parser.print_help()
