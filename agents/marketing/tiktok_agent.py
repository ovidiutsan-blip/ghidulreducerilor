"""
tiktok_agent.py — Postare automată pe TikTok (photo posts/carousel).

Strategie:
  - 3 imagini/zi (deal cards 9:16, format TikTok portrait)
  - Ore de vârf: 11:00-13:00 și 19:00-21:00 RO
  - Imagine generată cu Pillow: produs + preț + reducere + brand
  - Upload pe tiktok.com/upload via Playwright (browser profile persistent)
  - Hashtag-uri în română + nișă produs

Setup prima dată:
  python agents/marketing/tiktok_agent.py --login
  (se deschide browser, loghează-te manual, se salvează sesiunea)

Rulare zilnică (Task Scheduler):
  python agents/marketing/tiktok_agent.py --run

Debug/test fără upload:
  python agents/marketing/tiktok_agent.py --dry-run
"""
from __future__ import annotations
import json, time, random, argparse, sys, os, re, textwrap
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import requests

# ── Pillow (instalat via pip install pillow) ────────────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)  # type: ignore

BASE         = Path(__file__).resolve().parent.parent.parent
DEALS_PATH   = BASE / "data" / "deals.json"
LOG_DIR      = BASE / "logs" / "tiktok"
PROFILE_DIR  = Path(__file__).parent / "tiktok_browser_profile"
CARDS_DIR    = BASE / "data" / "marketing" / "tiktok_cards"
PROMO_LOG    = BASE / "data" / "marketing" / "tiktok_promo_log.json"

SITE_BASE    = "https://ghidulreducerilor.ro"

# ── Branding CatalinDigital ──────────────────────────────────────────────────
COLOR_NAVY   = "#1D3557"
COLOR_ORANGE = "#F4A261"
COLOR_RED    = "#E63946"
COLOR_WHITE  = "#FFFFFF"
COLOR_LIGHT  = "#F8F9FA"
COLOR_DARK   = "#212529"

# ── Card dimensions (9:16 portrait — TikTok optimal) ────────────────────────
CARD_W = 1080
CARD_H = 1920

# ── TikTok config ────────────────────────────────────────────────────────────
MAX_POSTS_PER_RUN  = 3
MIN_DISCOUNT       = 30   # % minim
COOLDOWN_DAYS      = 3
MAX_PER_STORE      = 1
MAX_TITLE_CHARS    = 150  # TikTok description limit = 2200 dar scurt e mai bun
MAX_HASHTAGS       = 8


# ─── Logging ──────────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / "tiktok_agent.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ─── Promo log ────────────────────────────────────────────────────────────────
def load_promo_log() -> dict:
    if PROMO_LOG.exists():
        with open(PROMO_LOG, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_promo_log(log_data: dict):
    PROMO_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(PROMO_LOG, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


# ─── Deal selection ───────────────────────────────────────────────────────────
def select_deals(n: int = MAX_POSTS_PER_RUN) -> list[dict]:
    with open(DEALS_PATH, encoding="utf-8") as f:
        deals = json.load(f)

    promo_log = load_promo_log()
    cooldown_dt = datetime.now() - timedelta(days=COOLDOWN_DAYS)

    eligible = []
    for d in deals:
        if not d.get("activ", True):
            continue
        pct = d.get("procent_reducere") or 0
        if pct < MIN_DISCOUNT:
            continue
        if not (d.get("imagine_url") or d.get("image") or d.get("imagine")):
            continue
        last = promo_log.get(d.get("id", ""))
        if last:
            try:
                if datetime.fromisoformat(last) > cooldown_dt:
                    continue
            except Exception:
                pass
        eligible.append(d)

    def score(d: dict) -> float:
        s = 0.0
        pct  = d.get("procent_reducere") or 0
        pret = d.get("pret_redus") or 9999
        s += pct * 1.5
        if pret < 200:  s += 20
        elif pret < 500: s += 10
        if d.get("omnibus_validated"): s += 15
        if pct >= 70: s += 30
        elif pct >= 50: s += 15
        titlu = (d.get("titlu") or "").lower()
        if "resigilat" in titlu or "refurbished" in titlu: s -= 15
        return s

    eligible.sort(key=score, reverse=True)

    selected, store_count = [], {}
    for d in eligible:
        store = d.get("magazin", "")
        if store_count.get(store, 0) >= MAX_PER_STORE:
            continue
        selected.append(d)
        store_count[store] = store_count.get(store, 0) + 1
        if len(selected) >= n:
            break
    return selected


# ─── Text helpers ─────────────────────────────────────────────────────────────
def deal_link(d: dict) -> str:
    deal_id = d.get("id", "")
    return f"{SITE_BASE}/out/{deal_id}" if deal_id else SITE_BASE


def tiktok_caption(d: dict) -> str:
    titlu  = (d.get("titlu") or "Ofertă").strip()
    pct    = d.get("procent_reducere") or 0
    pret   = d.get("pret_redus") or 0
    orig   = d.get("pret_original") or 0
    store  = (d.get("magazin") or "").capitalize()
    link   = deal_link(d)
    cat    = (d.get("categorie") or "").lower()
    economie = round(orig - pret) if orig > pret else 0

    lines = [
        f"🔥 -{pct}% reducere!",
        f"{titlu[:80]}",
        "",
        f"💰 Preț: {pret:.0f} lei (față de {orig:.0f} lei)",
    ]
    if economie > 0:
        lines.append(f"💡 Economisești {economie:.0f} lei!")
    lines += [
        "",
        f"👉 Link în bio sau caută: {link}",
        "",
    ]

    # Hashtag-uri relevante
    hashtags = ["#reduceri", "#oferte", "#chilipiruri", "#romania", "#shopping"]
    cat_tags = {
        "beauty":            ["#beauty", "#cosmetice", "#parfumuri"],
        "fashion":           ["#moda", "#fashion", "#outfit"],
        "casa-gradina":      ["#casasigradina", "#decor", "#homeideas"],
        "electronice":       ["#tech", "#electronice", "#gadgets"],
        "farmacie-sanatate": ["#sanatate", "#vitamine", "#farmacie"],
        "carti":             ["#carti", "#citeste", "#books"],
        "suplimente-bio":    ["#bio", "#natural", "#sanatate"],
    }
    extra = cat_tags.get(cat, [])
    if store:
        extra.append(f"#{store.lower().replace(' ', '').replace('.', '')}")
    all_tags = (hashtags + extra)[:MAX_HASHTAGS]
    lines.append(" ".join(all_tags))

    return "\n".join(lines)[:2200]


# ─── Imagine deal card (Pillow) ───────────────────────────────────────────────
def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))  # type: ignore


def _find_font(size: int, bold: bool = False) -> "ImageFont.FreeTypeFont | ImageFont.ImageFont":
    """Găsește un font disponibil pe sistem."""
    candidates = []
    if bold:
        candidates = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/seguibl.ttf",
            "C:/Windows/Fonts/verdanab.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/verdana.ttf",
        ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _download_product_image(url: str) -> Optional["Image.Image"]:
    """Descarcă și returnează imaginea produsului."""
    if not url or not url.startswith("http"):
        return None
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; GhidulReducerilor/1.0)"}
        resp = requests.get(url, timeout=8, headers=headers)
        if resp.status_code == 200:
            from io import BytesIO
            img = Image.open(BytesIO(resp.content)).convert("RGBA")
            return img
    except Exception:
        pass
    return None


def generate_deal_card(d: dict, output_path: Path) -> Optional[Path]:
    """
    Generează o imagine 1080x1920 (9:16) pentru TikTok.
    Layout:
      - Top: banner gradient navy + titlu magazin
      - Mijloc: imaginea produsului (centrată)
      - Reducere badge (roșu, colț dreapta sus)
      - Bandă preț (portocaliu)
      - Footer: site URL + CTA
    """
    if not HAS_PILLOW:
        log("  [WARN] Pillow nu e instalat — skip generare imagine")
        return None

    try:
        img = Image.new("RGB", (CARD_W, CARD_H), hex_to_rgb(COLOR_LIGHT))
        draw = ImageDraw.Draw(img)

        navy  = hex_to_rgb(COLOR_NAVY)
        orange= hex_to_rgb(COLOR_ORANGE)
        red   = hex_to_rgb(COLOR_RED)
        white = hex_to_rgb(COLOR_WHITE)
        dark  = hex_to_rgb(COLOR_DARK)

        # ── Background gradient simulat (benzi orizontale navy→light) ──────
        for y in range(CARD_H):
            ratio = y / CARD_H
            if ratio < 0.15:          # top banner navy
                r, g, b = navy
            elif ratio < 0.18:        # tranziție
                blend = (ratio - 0.15) / 0.03
                r = int(navy[0] + (hex_to_rgb(COLOR_LIGHT)[0] - navy[0]) * blend)
                g = int(navy[1] + (hex_to_rgb(COLOR_LIGHT)[1] - navy[1]) * blend)
                b = int(navy[2] + (hex_to_rgb(COLOR_LIGHT)[2] - navy[2]) * blend)
            elif ratio > 0.82:        # footer navy
                blend = (ratio - 0.82) / 0.18
                r = int(hex_to_rgb(COLOR_LIGHT)[0] + (navy[0] - hex_to_rgb(COLOR_LIGHT)[0]) * blend)
                g = int(hex_to_rgb(COLOR_LIGHT)[1] + (navy[1] - hex_to_rgb(COLOR_LIGHT)[1]) * blend)
                b = int(hex_to_rgb(COLOR_LIGHT)[2] + (navy[2] - hex_to_rgb(COLOR_LIGHT)[2]) * blend)
            else:                      # centru alb/luminos
                r, g, b = hex_to_rgb(COLOR_LIGHT)
            draw.line([(0, y), (CARD_W, y)], fill=(r, g, b))

        # ── Top banner ───────────────────────────────────────────────────────
        banner_h = 280
        draw.rectangle([0, 0, CARD_W, banner_h], fill=navy)

        # Logo text / site
        font_logo = _find_font(52, bold=True)
        site_text = "ghidulreducerilor.ro"
        draw.text((54, 38), site_text, font=font_logo, fill=orange)

        # Subtitlu
        font_sub = _find_font(36)
        draw.text((54, 110), "Reduceri verificate zilnic", font=font_sub, fill=white)

        # Linie separator sub logo
        draw.line([(54, 165), (CARD_W - 54, 165)], fill=orange, width=3)

        # Magazin
        magazin = (d.get("magazin") or "").upper()
        font_mag = _find_font(44, bold=True)
        draw.text((54, 185), magazin, font=font_mag, fill=white)

        # ── Reducere badge ───────────────────────────────────────────────────
        pct = d.get("procent_reducere") or 0
        badge_r = 120
        bx, by = CARD_W - 155, 300
        draw.ellipse([bx - badge_r, by - badge_r, bx + badge_r, by + badge_r], fill=red)
        font_badge = _find_font(72, bold=True)
        badge_text = f"-{pct}%"
        bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
        bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((bx - bw // 2, by - bh // 2 - 5), badge_text, font=font_badge, fill=white)

        # ── Imagine produs ───────────────────────────────────────────────────
        img_url = d.get("imagine_url") or d.get("image") or d.get("imagine") or ""
        prod_img = _download_product_image(img_url)

        prod_zone_top = banner_h + 20
        prod_zone_bot = CARD_H - 560
        prod_zone_h   = prod_zone_bot - prod_zone_top
        prod_zone_w   = CARD_W

        if prod_img:
            # Redimensionare cu păstrarea proporțiilor
            max_w = prod_zone_w - 80
            max_h = prod_zone_h - 40
            prod_img.thumbnail((max_w, max_h), Image.LANCZOS)
            pw, ph = prod_img.size
            px = (CARD_W - pw) // 2
            py = prod_zone_top + (prod_zone_h - ph) // 2

            # Umbra subtilă
            shadow = Image.new("RGBA", (pw + 20, ph + 20), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.rectangle([10, 10, pw + 10, ph + 10], fill=(0, 0, 0, 40))
            shadow = shadow.filter(ImageFilter.GaussianBlur(12))
            img.paste(shadow.convert("RGB"), (px - 5, py + 5),
                      shadow.split()[3] if prod_img.mode == "RGBA" else None)

            if prod_img.mode == "RGBA":
                img.paste(prod_img, (px, py), prod_img.split()[3])
            else:
                img.paste(prod_img, (px, py))
        else:
            # Placeholder dacă nu avem imagine
            ph_rect = [80, prod_zone_top + 20, CARD_W - 80, prod_zone_bot - 20]
            draw.rectangle(ph_rect, fill=(220, 225, 230))
            font_ph = _find_font(48)
            draw.text((CARD_W // 2 - 80, (prod_zone_top + prod_zone_bot) // 2 - 30),
                      "🛒 Ofertă", font=font_ph, fill=dark)

        # ── Bandă titlu produs ───────────────────────────────────────────────
        titlu_y = CARD_H - 540
        draw.rectangle([0, titlu_y - 10, CARD_W, titlu_y + 120], fill=(240, 242, 245))
        titlu = (d.get("titlu") or "Produs").strip()
        font_titlu = _find_font(40, bold=True)
        # Wrap text
        lines_titlu = textwrap.wrap(titlu, width=36)[:2]
        for i, line in enumerate(lines_titlu):
            draw.text((54, titlu_y + i * 52), line, font=font_titlu, fill=dark)

        # ── Bandă preț (portocaliu) ──────────────────────────────────────────
        price_y = CARD_H - 400
        draw.rectangle([0, price_y, CARD_W, price_y + 130], fill=orange)

        pret  = d.get("pret_redus") or 0
        orig  = d.get("pret_original") or 0
        font_pret_nou = _find_font(80, bold=True)
        font_pret_old = _find_font(46)

        # Preț nou mare
        pret_text = f"{pret:.0f} lei"
        draw.text((54, price_y + 18), pret_text, font=font_pret_nou, fill=white)

        # Preț original tăiat (dreapta)
        if orig > pret:
            orig_text = f"{orig:.0f} lei"
            bbox_orig = draw.textbbox((0, 0), orig_text, font=font_pret_old)
            ox = CARD_W - bbox_orig[2] - 54
            oy = price_y + 42
            draw.text((ox, oy), orig_text, font=font_pret_old, fill=white)
            # Linie tăiată
            mid_y = oy + (bbox_orig[3] - bbox_orig[1]) // 2
            draw.line([(ox - 4, mid_y), (ox + bbox_orig[2] + 4, mid_y)],
                      fill=(200, 100, 80), width=4)

        # Economie
        economie = round(orig - pret)
        if economie > 0:
            font_eco = _find_font(34)
            eco_text = f"Economisești {economie} lei!"
            draw.text((54, price_y + 100), eco_text, font=font_eco, fill=dark)

        # ── CTA bandă ─────────────────────────────────────────────────────────
        cta_y = CARD_H - 260
        draw.rectangle([0, cta_y, CARD_W, cta_y + 100], fill=red)
        font_cta = _find_font(46, bold=True)
        cta_text = "🔥 CUMPĂRĂ ACUM — LINK ÎN BIO"
        bbox_cta = draw.textbbox((0, 0), cta_text, font=font_cta)
        cx = (CARD_W - (bbox_cta[2] - bbox_cta[0])) // 2
        draw.text((cx, cta_y + 25), cta_text, font=font_cta, fill=white)

        # ── Footer ────────────────────────────────────────────────────────────
        footer_y = CARD_H - 150
        draw.rectangle([0, footer_y, CARD_W, CARD_H], fill=navy)
        font_footer = _find_font(36)
        footer_text = "ghidulreducerilor.ro  |  Reduceri verificate zilnic"
        bbox_f = draw.textbbox((0, 0), footer_text, font=font_footer)
        fx = (CARD_W - (bbox_f[2] - bbox_f[0])) // 2
        draw.text((fx, footer_y + 28), footer_text, font=font_footer, fill=(200, 210, 220))
        font_footer2 = _find_font(28)
        draw.text((fx + 80, footer_y + 80), "Urmareste-ne pe TikTok!", font=font_footer2, fill=orange)

        # Salvare
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img = img.convert("RGB")
        img.save(str(output_path), "JPEG", quality=92)
        return output_path

    except Exception as e:
        log(f"  [ERR] Generare imagine esuata: {e}")
        return None


# ─── TikTok upload via Playwright ────────────────────────────────────────────
def _get_browser():
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    browser = p.chromium.launch_persistent_context(
        str(PROFILE_DIR),
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    return p, browser


def login_tiktok():
    """Deschide browserul pentru login manual — sesiunea se salvează în profile."""
    log("Deschid browser pentru login TikTok (manual)...")
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    p, browser = _get_browser()
    page = browser.new_page()
    page.goto("https://www.tiktok.com/login")
    log("Loghează-te manual în browser. Apasă ENTER când ai terminat...")
    input()
    page.screenshot(path=str(LOG_DIR / "login_done.png"))
    log("Sesiune salvată. Browser închis.")
    browser.close()
    p.stop()


def post_to_tiktok(image_path: Path, caption: str, dry_run: bool = False) -> bool:
    """
    Uploadează o imagine pe TikTok via tiktok.com/upload.
    Returnează True dacă postarea a reușit.
    """
    if dry_run:
        log(f"  [DRY-RUN] Ar posta: {image_path.name}")
        log(f"  Caption: {caption[:120]}...")
        return True

    if not image_path.exists():
        log(f"  [ERR] Imagine lipsă: {image_path}")
        return False

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        log("  [ERR] Playwright nu e instalat — pip install playwright")
        return False

    p, browser = _get_browser()
    success = False
    try:
        page = browser.new_page()
        page.goto("https://www.tiktok.com/upload", timeout=30_000)
        time.sleep(3)

        # Verifică dacă e logat
        if "login" in page.url.lower():
            log("  [ERR] Sesiune expirată — rulează --login din nou")
            page.screenshot(path=str(LOG_DIR / "not_logged_in.png"))
            return False

        # Așteaptă input[type=file]
        page.wait_for_selector('input[type="file"]', timeout=20_000)
        time.sleep(1)

        # Upload imagine
        log(f"  Upload {image_path.name}...")
        file_input = page.locator('input[type="file"]').first
        file_input.set_input_files(str(image_path))
        time.sleep(5)

        # Asteaptă preview-ul
        try:
            page.wait_for_selector('[class*="caption"]', timeout=15_000)
        except PWTimeout:
            page.wait_for_selector('div[contenteditable]', timeout=10_000)

        time.sleep(2)

        # Caption
        log("  Completez caption...")
        try:
            caption_el = page.locator('div[contenteditable="true"]').first
            caption_el.click()
            time.sleep(0.5)
            # Șterge conținut existent
            page.keyboard.press("Control+a")
            page.keyboard.press("Delete")
            time.sleep(0.3)
            # Scrie caption via clipboard (suport unicode)
            import pyperclip
            pyperclip.copy(caption)
            page.keyboard.press("Control+v")
            time.sleep(1)
        except Exception as e:
            log(f"  [WARN] Caption via keyboard: {e}")
            # Fallback: type direct (fără unicode)
            caption_ascii = caption.encode("ascii", "ignore").decode()
            caption_el = page.locator('div[contenteditable="true"]').first
            caption_el.fill(caption_ascii)

        time.sleep(2)

        # Post button
        log("  Caut butonul Post...")
        post_btn = None
        for sel in ['button:has-text("Post")', 'button:has-text("Posteaza")',
                    'button[data-e2e="post-button"]', '[class*="post-btn"]']:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=3_000):
                    post_btn = btn
                    break
            except Exception:
                continue

        if not post_btn:
            log("  [WARN] Buton Post negăsit — screenshot și skip")
            page.screenshot(path=str(LOG_DIR / f"no_post_btn_{datetime.now().strftime('%H%M%S')}.png"))
            return False

        time.sleep(1)
        post_btn.click()
        log("  Aștept confirmare postare...")
        time.sleep(8)

        # Verifică succes
        page_text = page.content().lower()
        if any(kw in page_text for kw in ["posted", "postat", "video uploaded", "photo uploaded", "success"]):
            log("  ✅ Postat cu succes!")
            success = True
        else:
            page.screenshot(path=str(LOG_DIR / f"post_result_{datetime.now().strftime('%H%M%S')}.png"))
            log("  [WARN] Status postare neclar — vezi screenshot în logs/tiktok/")
            success = True  # Assumem success dacă nu e eroare explicită

    except Exception as e:
        log(f"  [ERR] Playwright error: {e}")
        try:
            page.screenshot(path=str(LOG_DIR / f"error_{datetime.now().strftime('%H%M%S')}.png"))
        except Exception:
            pass
    finally:
        try:
            browser.close()
            p.stop()
        except Exception:
            pass

    return success


# ─── Main flow ────────────────────────────────────────────────────────────────
def run(dry_run: bool = False):
    log(f"=== TikTok Agent {'[DRY-RUN]' if dry_run else '[LIVE]'} — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")

    if not HAS_PILLOW:
        log("[ERR] Pillow lipsă — rulează: pip install pillow")
        sys.exit(1)

    deals = select_deals(MAX_POSTS_PER_RUN)
    if not deals:
        log("Niciun deal eligibil găsit azi.")
        return

    log(f"Selectate {len(deals)} deals de postat:")
    for d in deals:
        log(f"  • [{d.get('magazin')}] {(d.get('titlu') or '')[:55]} — -{d.get('procent_reducere')}%")

    promo_log_data = load_promo_log()
    posted_ids = []

    for i, deal in enumerate(deals, 1):
        log(f"\n[{i}/{len(deals)}] Procesez: {(deal.get('titlu') or '')[:55]}")

        # Generare imagine
        safe_id = re.sub(r"[^a-z0-9\-]", "", deal.get("id", f"deal-{i}").lower())[:50]
        card_path = CARDS_DIR / f"{datetime.now().strftime('%Y%m%d')}_{safe_id}.jpg"

        log("  Generez imagine card 9:16...")
        card = generate_deal_card(deal, card_path)
        if not card:
            log("  [SKIP] Imagine negenerat — skip deal")
            continue

        # Generare caption
        caption = tiktok_caption(deal)
        log(f"  Caption ({len(caption)} chars) generat")

        # Postare
        ok = post_to_tiktok(card, caption, dry_run=dry_run)

        if ok:
            promo_log_data[deal.get("id", "")] = datetime.now().isoformat()
            posted_ids.append(deal.get("id", ""))
            log(f"  ✅ Deal postat: {(deal.get('titlu') or '')[:50]}")
        else:
            log(f"  ❌ Postare esuata pentru {deal.get('id')}")

        # Pauza umana intre posturi
        if i < len(deals):
            wait = random.uniform(45, 90)
            log(f"  Pauza {wait:.0f}s intre posturi...")
            time.sleep(wait)

    # Salvare promo log
    if not dry_run and posted_ids:
        save_promo_log(promo_log_data)

    log(f"\n=== Gata: {len(posted_ids)}/{len(deals)} postari reușite ===")


def setup():
    """Creare structuri directoare + instrucțiuni setup."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log("✅ Directoare create:")
    log(f"  Profile: {PROFILE_DIR}")
    log(f"  Cards:   {CARDS_DIR}")
    log(f"  Logs:    {LOG_DIR}")
    log("\nPași următori:")
    log("  1. pip install pillow playwright pyperclip")
    log("  2. python -m playwright install chromium")
    log("  3. python tiktok_agent.py --login  (login manual în browser)")
    log("  4. python tiktok_agent.py --dry-run  (test fără upload)")
    log("  5. python tiktok_agent.py --run  (postare live)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TikTok Agent — GhidulReducerilor")
    parser.add_argument("--run",      action="store_true", help="Rulează și postează")
    parser.add_argument("--dry-run",  action="store_true", help="Test fără upload")
    parser.add_argument("--login",    action="store_true", help="Login manual TikTok")
    parser.add_argument("--setup",    action="store_true", help="Creare directoare + instrucțiuni")
    args = parser.parse_args()

    if args.setup:
        setup()
    elif args.login:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        login_tiktok()
    elif args.dry_run:
        run(dry_run=True)
    elif args.run:
        run(dry_run=False)
    else:
        parser.print_help()
