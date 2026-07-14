#!/usr/bin/env python3
"""personal_fb_autoposter.py — Postează AUTONOM pe profilul Facebook PERSONAL.

⚠️  CITEȘTE ÎNAINTE DE A ARMA:
Automatizarea postării pe un profil personal încalcă ToS Facebook. Făcută în rafală
sau la ore fixe = tipar de bot = risc de ban de cont (ireversibil). Acest agent e
proiectat cu DISCIPLINĂ ANTI-DETECȚIE ca să reducă riscul la minim, dar riscul NU e
zero. Prima rulare live rulează SUPRAVEGHEAT.

Ce face (o postare per invocare):
1. Alege 1 deal nepromovat care produce comision (reutilizează logica din
   personal_fb_generator.py — dedup partajat prin fb_personal_log.json).
2. Postează pe timeline-ul personal: text în corp + link afiliat ca PRIM COMENTARIU
   (așa Facebook nu gâtuie reach-ul pentru link extern).
3. Reutilizează profilul browser persistent logat (fb_browser_profile/) din
   facebook_poster.py — aceeași sesiune, aceeași autentificare.

Disciplină anti-ban (toate configurabile în fb_autopost_config.json):
- Fereastră de zi (implicit 10:00–20:00) — nu postează noaptea.
- Plafon zilnic (implicit 4 postări/zi) — nu 8.
- Gap minim între postări (implicit 110 min) — ~2h.
- Jitter aleator la start (0–35 min) — postările NU cad la ore fixe.
- Probabilitate de skip (implicit 25%) — sare aleator peste sloturi ca să spargă
  tiparul de ceas (~3 postări/zi din 6 sloturi, nepredictibil).
- Detecție checkpoint/captcha/block → HALT imediat + alertă. Cât timp e HALTED,
  refuză să ruleze până rulezi `--reset-halt` (previne escaladarea soft-block→ban).

Model de rulare (recomandat): Task Scheduler declanșează `--run` la fiecare 2h în
fereastra de zi. Fiecare rulare postează CEL MULT una și iese. Fără daemon persistent.

Comenzi:
    python agents/marketing/personal_fb_autoposter.py --dry-run   # arată ce AR posta, fără browser
    python agents/marketing/personal_fb_autoposter.py --once-live # 1 postare reală, SUPRAVEGHEAT (ignoră gap/skip)
    python agents/marketing/personal_fb_autoposter.py --run       # 1 postare dacă regulile permit (pt. Task Scheduler)
    python agents/marketing/personal_fb_autoposter.py --status    # starea agentului azi
    python agents/marketing/personal_fb_autoposter.py --reset-halt # scoate flag-ul HALT după ce ai rezolvat manual
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import date, datetime
from pathlib import Path

# reutilizăm logica de selecție deal-uri (același pachet)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from personal_fb_generator import (  # noqa: E402
    pick_deals, render_post, load_json, clean_title, STORES,
)

# consola Windows e cp1252 → forțăm UTF-8 ca diacriticele din print să nu crape
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "marketing"
DEDUP_LOG = OUT_DIR / "fb_personal_log.json"          # partajat cu generatorul
STATE = OUT_DIR / "fb_autopost_state.json"
CONFIG = OUT_DIR / "fb_autopost_config.json"
LOG_DIR = ROOT / "logs" / "fb_autopost"
PROFILE_DIR = Path(__file__).resolve().parent / "fb_browser_profile"

DEFAULT_CONFIG = {
    "window_start_hour": 10,
    "window_end_hour": 20,
    "max_per_day": 4,
    "min_gap_minutes": 110,
    "jitter_max_minutes": 35,
    "skip_probability": 0.25,
    "max_price": 400.0,
    "min_price": 25.0,
    # link_in_body=True (implicit): linkul intră în corpul postării — FIABIL pentru
    # un agent autonom (nu poate rata comentariul pe altă postare). False = tactica
    # link-in-primul-comentariu (reach ceva mai bun, dar automatizarea e fragilă).
    "link_in_body": True,
}

# semnale că Facebook ne-a prins → oprire imediată
BLOCK_SIGNALS = [
    "checkpoint", "/checkpoint/", "temporarily blocked", "you're temporarily blocked",
    "temporar blocat", "activitate neobișnuită", "activitate neobisnuita",
    "confirmă că ești", "confirma ca esti", "suspicious", "cont dezactivat",
    "your account has been disabled", "we've limited",
]


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_state() -> dict:
    return load_json(STATE, {"last_post_ts": None, "posts_today": {},
                             "stores_today": {}, "halted": False, "halt_reason": None})


def save_state(st: dict):
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cfg() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(load_json(CONFIG, {}))
    return cfg


def posts_today(st: dict) -> int:
    return int(st.get("posts_today", {}).get(date.today().isoformat(), 0))


def stores_today(st: dict) -> list[str]:
    return list(st.get("stores_today", {}).get(date.today().isoformat(), []))


def record_post(st: dict, deal_id: str, magazin: str):
    today = date.today().isoformat()
    st.setdefault("posts_today", {})[today] = posts_today(st) + 1
    lst = st.setdefault("stores_today", {}).setdefault(today, [])
    if magazin not in lst:
        lst.append(magazin)
    st["last_post_ts"] = datetime.now().isoformat()
    save_state(st)
    # dedup partajat cu generatorul
    dl = load_json(DEDUP_LOG, {})
    dl[deal_id] = datetime.now().isoformat()
    DEDUP_LOG.write_text(json.dumps(dl, ensure_ascii=False, indent=2), encoding="utf-8")


def minutes_since_last(st: dict) -> float:
    last = st.get("last_post_ts")
    if not last:
        return 1e9
    try:
        return (datetime.now() - datetime.fromisoformat(last)).total_seconds() / 60.0
    except ValueError:
        return 1e9


def eligibility(st: dict, cfg: dict) -> tuple[bool, str]:
    """Verifică fereastra de zi, plafonul, gap-ul. Returnează (poate_posta, motiv)."""
    if st.get("halted"):
        return False, f"HALTED ({st.get('halt_reason')}) — rulează --reset-halt după ce rezolvi manual"
    now = datetime.now()
    if not (cfg["window_start_hour"] <= now.hour < cfg["window_end_hour"]):
        return False, f"în afara ferestrei de zi ({cfg['window_start_hour']}:00–{cfg['window_end_hour']}:00)"
    if posts_today(st) >= cfg["max_per_day"]:
        return False, f"plafon zilnic atins ({cfg['max_per_day']})"
    gap = minutes_since_last(st)
    if gap < cfg["min_gap_minutes"]:
        return False, f"gap prea mic ({gap:.0f} min < {cfg['min_gap_minutes']} min)"
    return True, "ok"


def scrub_sku(title: str) -> str:
    """Curăță coada de tip SKU dintr-un titlu ca să sune a om, nu a catalog."""
    import re
    t = title.strip()
    # "- JON 3272", " JON3272", " CMP1556", "ND7006" la coadă
    t = re.sub(r"[\s\-–—]+[A-Z]{2,}[\s\-]?\d{2,}[A-Za-z0-9]*\s*$", "", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip().rstrip(",-–—").strip()


def pick_one(cfg: dict, exclude_stores: list[str]) -> dict | None:
    """Alege 1 deal, preferând un magazin nepostat încă azi (rotație = variație).
    pick_deals(N) întoarce deja un deal per magazin, top-scored → luăm primul
    magazin care nu e în exclude_stores. Dacă toate au fost postate, permitem
    cel mai bun repeat ca să nu blocăm postarea."""
    deals = pick_deals(12, cfg["max_price"], cfg["min_price"])
    if not deals:
        return None
    for d in deals:
        if d["magazin"] not in exclude_stores:
            return d
    return deals[0]


def build_post(cfg: dict, exclude_stores: list[str]) -> tuple[dict | None, dict | None]:
    """Selectează dealul și construiește postarea (cu SKU curățat). Folosit și de
    dry-run și de postarea reală, ca output-ul afișat == output-ul postat."""
    deal = pick_one(cfg, exclude_stores)
    if not deal:
        return None, None
    stores = load_json(STORES, [])
    if isinstance(stores, dict):
        stores = stores.get("stores", [])
    d2 = dict(deal)
    d2["titlu"] = scrub_sku(clean_title(deal.get("titlu", "")))
    post = render_post(d2, stores)
    return deal, post


# ─── Postare pe timeline personal via Playwright ─────────────────────────────

def _screenshot(page, name: str):
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        p = LOG_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{name}.png"
        page.screenshot(path=str(p))
        return p
    except Exception:
        return None


def _detect_block(page) -> str | None:
    """Returnează motivul blocării dacă Facebook ne-a prins, altfel None."""
    try:
        url = (page.url or "").lower()
        body = ""
        try:
            body = (page.inner_text("body", timeout=3000) or "").lower()
        except Exception:
            pass
        blob = url + " " + body
        for sig in BLOCK_SIGNALS:
            if sig in blob:
                return sig
    except Exception:
        pass
    return None


def _human_delay(a=1.2, b=3.5):
    time.sleep(random.uniform(a, b))


def _click_first(page, selectors: list, timeout=4000) -> bool:
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                loc.click(timeout=timeout)
                return True
        except Exception:
            continue
    return False


def _composer_open(page) -> bool:
    """True dacă dialogul de creare postare (cu textbox) e încă deschis."""
    try:
        return page.locator('div[role="dialog"] div[role="textbox"]').count() > 0
    except Exception:
        return False


def _dialog_open(page) -> bool:
    try:
        return page.locator('div[role="dialog"]').count() > 0
    except Exception:
        return False


def _ensure_promote_off(page):
    """Pe ecranul de setări, oprește orice switch pornit (Promovează postarea)
    ca să nu se declanșeze o promovare plătită. Best-effort."""
    try:
        switches = page.locator('div[role="dialog"] div[role="switch"]')
        for i in range(switches.count()):
            el = switches.nth(i)
            try:
                if el.get_attribute("aria-checked") == "true":
                    el.click(timeout=2000)
                    time.sleep(0.4)
            except Exception:
                continue
    except Exception:
        pass


def post_to_timeline(post: dict, publish: bool = True,
                     link_in_body: bool = True) -> tuple[bool, str]:
    """Postează pe timeline-ul personal.
    - link_in_body=True: linkul e deja în post['body'] → nu comentăm (fiabil).
    - link_in_body=False: după publicare, punem linkul ca prim comentariu pe
      postarea care conține titlul dealului (nu pe .first, ca să nu greșim postarea).
    Dacă publish=False (mod test): completează compozitorul, face screenshot și
    NU publică. Returnează (succes, motiv). Setează HALT dacă detectează block."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "playwright neinstalat (pip install playwright && playwright install chromium)"

    st = load_state()
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                str(PROFILE_DIR), headless=False,
                viewport={"width": 1280, "height": 900},
                args=["--disable-blink-features=AutomationControlled"],
            )
        except Exception as e:
            return False, f"nu pot lansa browserul (profil ocupat?): {e}"

        page = context.pages[0] if context.pages else context.new_page()
        try:
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=30000)
            _human_delay(2, 4)

            blk = _detect_block(page)
            if blk:
                st["halted"] = True; st["halt_reason"] = f"block la login: {blk}"
                save_state(st); _screenshot(page, "block_login")
                return False, f"BLOCK detectat ({blk}) — agent oprit"

            # verifică că suntem logați (compozitorul există)
            # NB: FB folosește "gândeşti" cu ş-cedilă (U+015F), nu ș-virgulă →
            # potrivim pe substringul "La ce te" ca să evităm capcana de caractere.
            composer_sel = [
                'div[role="button"]:has-text("La ce te")',
                'span:has-text("La ce te")',
                'div[role="region"] div[role="button"]:has-text("La ce te")',
                'div[role="button"]:has-text("Ce ai în minte")',
            ]
            if not _click_first(page, composer_sel, timeout=8000):
                _screenshot(page, "no_composer")
                return False, "nu găsesc compozitorul (poate nu ești logat — rulează facebook_poster.py --setup)"
            _human_delay(1.5, 3)

            # textbox din dialog
            box = page.locator('div[role="dialog"] div[role="textbox"]').first
            box.click(timeout=6000)
            _human_delay(0.8, 1.8)
            # tastare umană
            for chunk in post["body"].split("\n"):
                page.keyboard.type(chunk, delay=random.randint(8, 28))
                page.keyboard.press("Shift+Enter")
                _human_delay(0.15, 0.5)
            _human_delay(1.2, 2.5)

            if not publish:
                shot = _screenshot(page, "test_compose")
                return True, f"TEST-COMPOSE ok (compozitor completat, NEPUBLICAT). Screenshot: {shot}"

            # Primul ecran are butonul principal "Înainte" → ecran de setări.
            # (unele conturi au direct "Postează"; îl încercăm întâi, scurt)
            if not _click_first(page, [
                'div[aria-label="Postează"]',
                'div[role="button"]:has-text("Postează")',
            ], timeout=2000):
                if not _click_first(page, [
                    'div[aria-label="Înainte"]',
                    'div[role="button"]:has-text("Înainte")',
                ], timeout=5000):
                    _screenshot(page, "no_inainte")
                    return False, "nu găsesc butonul Înainte/Postează"
                _human_delay(1.5, 3)
                # ecran de setări: FORȚEAZĂ OFF promovarea plătită (evită cheltuială accidentală)
                _ensure_promote_off(page)
                _human_delay(0.5, 1.2)
                _click_first(page, [
                    'div[aria-label="Postează"]',
                    'div[role="button"][aria-label="Postează"]',
                    'div[role="button"]:has-text("Postează")',
                    'button:has-text("Postează")',
                ], timeout=6000)
            # Publicarea poate dura ("Se postează…" rămâne pe ecran la conexiuni
            # lente) — aștept până la 30s să se închidă compozitorul înainte de a
            # decide. Verificarea la delay fix (4-6.5s) dădea fals negativ: raporta
            # eșec deși postarea ajungea pe timeline (14 iul 2026).
            _human_delay(2, 3.5)
            publish_deadline = time.time() + 30
            while _composer_open(page) and time.time() < publish_deadline:
                time.sleep(1.5)

            blk = _detect_block(page)
            if blk:
                st["halted"] = True; st["halt_reason"] = f"block la postare: {blk}"
                save_state(st); _screenshot(page, "block_post")
                return False, f"BLOCK detectat după postare ({blk}) — agent oprit"

            # dismite eventualul prompt de boost apărut DUPĂ publicare (nu înainte!)
            if _dialog_open(page) and not _composer_open(page):
                _click_first(page, [
                    'div[aria-label="Închide"]', 'div[aria-label="Close"]',
                    'div[role="button"]:has-text("Nu acum")',
                ], timeout=2500)
                _human_delay(0.5, 1.2)

            # VERIFICĂ publicarea: compozitorul trebuie să fi dispărut
            if _composer_open(page):
                _screenshot(page, "publish_failed")
                return False, "publicarea a eșuat (compozitorul a rămas deschis)"

            _screenshot(page, "posted")

            if link_in_body:
                return True, "POSTAT (link în corp)"

            # link-in-comment: comentează pe postarea care conține titlul dealului
            comment_ok = _add_comment_to_post(page, post["comment"], post.get("match_snippet", ""))
            if not comment_ok:
                # postarea e sus, doar linkul lipsește — degradare grațioasă
                return True, f"POSTAT (dar comentariul-link a eșuat — adaugă manual: {post['comment']})"
            return True, "POSTAT + comentariu-link OK"
        except Exception as e:
            _screenshot(page, "error")
            return False, f"eroare în timpul postării: {e}"
        finally:
            _human_delay(1, 2)
            try:
                context.close()
            except Exception:
                pass


def _add_comment_to_post(page, comment_text: str, snippet: str) -> bool:
    """Pune linkul ca prim comentariu pe postarea care conține `snippet` (titlul
    dealului), NU pe prima postare — ca să nu comentăm pe postarea greșită."""
    try:
        page.goto("https://www.facebook.com/me", wait_until="domcontentloaded", timeout=25000)
        _human_delay(3, 4.5)
        if snippet:
            art = page.locator(f'div[role="article"]:has-text({json.dumps(snippet)})').first
        else:
            art = page.locator('div[role="article"]').first
        if art.count() == 0:
            _screenshot(page, "comment_post_not_found")
            return False
        try:
            art.scroll_into_view_if_needed(timeout=4000)
        except Exception:
            pass
        _human_delay(0.8, 1.6)
        # deschide zona de comentariu DIN ACEST articol (nu global) — etichete RO/EN
        commented = False
        for sel in ['[aria-label="Comentează"]', '[aria-label*="omentari"]',
                    '[aria-label*="omment"]', '[aria-label="Lasă un comentariu"]',
                    'div[role="textbox"]']:
            try:
                loc = art.locator(sel).first
                if loc.count() > 0:
                    loc.click(timeout=5000)
                    commented = True
                    break
            except Exception:
                continue
        if not commented:
            _screenshot(page, "comment_no_box")
            return False
        _human_delay(1, 2)
        cbox = art.locator('div[role="textbox"]').last
        cbox.click(timeout=5000)
        page.keyboard.type(comment_text, delay=random.randint(6, 20))
        _human_delay(2, 3.2)   # lasă preview-ul de link să se genereze
        page.keyboard.press("Enter")
        _human_delay(2.5, 4)
        _screenshot(page, "commented")
        return True
    except Exception:
        _screenshot(page, "comment_error")
        return False


# ─── CLI ─────────────────────────────────────────────────────────────────────

def cmd_status():
    st = load_state(); cfg = load_cfg()
    ok, why = eligibility(st, cfg)
    print(f"Data: {date.today().isoformat()}")
    print(f"Postări azi: {posts_today(st)}/{cfg['max_per_day']}")
    print(f"Ultima postare: {st.get('last_post_ts') or '—'}")
    print(f"HALTED: {st.get('halted')} ({st.get('halt_reason') or '—'})")
    print(f"Poate posta acum: {ok} ({why})")


def _title_line(body: str) -> str:
    """Extrage linia de titlu din corpul postării (pt. snippet de potrivire)."""
    for i, ln in enumerate(body.split("\n")):
        s = ln.strip()
        if i == 0 or not s:
            continue
        if s.startswith("💰") or s.startswith("("):
            continue
        return s
    return ""


def do_post(cfg: dict, supervised: bool) -> int:
    st = load_state()
    deal, post = build_post(cfg, exclude_stores=stores_today(st))
    if not deal:
        log("Niciun deal nou eligibil (toate promovate sau fără comision). "
            "Rulează generatorul cu --reset dacă vrei să reiei.")
        return 0

    link_in_body = bool(cfg.get("link_in_body", True))
    # snippet pt. a găsi postarea corectă la comentariu (mod link-in-comment)
    post["match_snippet"] = " ".join(_title_line(post["body"]).split()[:4])
    if link_in_body:
        post["body"] = post["body"] + f"\n\n👉 {post['url']}"

    log(f"Deal ales: {post['magazin']} (-{post['proc']}%) | link_in_body={link_in_body}")
    log(f"Corp:\n{post['body']}")
    if not link_in_body:
        log(f"Comentariu: {post['comment']}")

    ok, msg = post_to_timeline(post, link_in_body=link_in_body)
    if ok:
        record_post(st, deal["id"], deal["magazin"])
        log(f"✅ {msg}")
        return 0
    log(f"❌ {msg}")
    return 1


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="arată ce ar posta, fără browser")
    g.add_argument("--once-live", action="store_true", help="1 postare reală, supravegheat (ignoră gap/skip)")
    g.add_argument("--test-compose", action="store_true", help="deschide compozitorul și completează textul, dar NU publică (validare selectori)")
    g.add_argument("--run", action="store_true", help="1 postare dacă regulile permit (Task Scheduler)")
    g.add_argument("--status", action="store_true", help="starea agentului")
    g.add_argument("--reset-halt", action="store_true", help="scoate flag-ul HALT")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG.exists():
        CONFIG.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")

    cfg = load_cfg()

    if args.status:
        cmd_status(); return
    if args.reset_halt:
        st = load_state(); st["halted"] = False; st["halt_reason"] = None; save_state(st)
        print("HALT scos. Agentul poate rula din nou."); return

    if args.dry_run:
        st = load_state()
        deal, post = build_post(cfg, exclude_stores=stores_today(st))
        if not deal:
            print("Niciun deal nou eligibil."); return
        link_in_body = bool(cfg.get("link_in_body", True))
        print("=== DRY-RUN (nu s-a postat nimic) ===")
        print(f"Magazin: {post['magazin']} (-{post['proc']}%) | link_in_body={link_in_body}\n")
        if link_in_body:
            print(post["body"] + f"\n\n👉 {post['url']}")
        else:
            print(post["body"]); print("\n[PRIM COMENTARIU]"); print(post["comment"])
        return

    if args.test_compose:
        st = load_state()
        if st.get("halted"):
            log(f"HALTED ({st.get('halt_reason')}). Rulează --reset-halt întâi."); sys.exit(2)
        deal, post = build_post(cfg, exclude_stores=stores_today(st))
        if not deal:
            log("Niciun deal eligibil de testat."); return
        log(f"TEST-COMPOSE cu: {post['magazin']} (-{post['proc']}%) — NU se publică.")
        ok, msg = post_to_timeline(post, publish=False)
        log(("✅ " if ok else "❌ ") + msg)
        sys.exit(0 if ok else 1)

    if args.once_live:
        log("Mod --once-live: postare reală supravegheată (ignor gap/skip, dar respect HALT).")
        st = load_state()
        if st.get("halted"):
            log(f"HALTED ({st.get('halt_reason')}). Rulează --reset-halt întâi."); sys.exit(2)
        sys.exit(do_post(cfg, supervised=True))

    if args.run:
        st = load_state()
        ok, why = eligibility(st, cfg)
        if not ok:
            log(f"Skip: {why}"); return
        # spargem tiparul de ceas: skip aleator + jitter
        if random.random() < cfg["skip_probability"]:
            log(f"Skip aleator (probabilitate {cfg['skip_probability']}) — anti-tipar."); return
        jitter = random.uniform(0, cfg["jitter_max_minutes"] * 60)
        log(f"Jitter: aștept {jitter/60:.1f} min înainte de postare (anti-ore-fixe)...")
        time.sleep(jitter)
        # re-verifică eligibilitatea după somn (poate s-a schimbat ziua/ora)
        st = load_state()
        ok, why = eligibility(st, cfg)
        if not ok:
            log(f"Skip după jitter: {why}"); return
        sys.exit(do_post(cfg, supervised=False))

    ap.print_help()


if __name__ == "__main__":
    main()
