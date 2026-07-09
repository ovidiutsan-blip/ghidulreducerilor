#!/usr/bin/env python3
"""Generator postari pentru Facebook PERSONAL (profil, nu pagina).

De ce exista separat de facebook_page_agent.py:
- Profilul personal are reach organic mult mai mare decat o Pagina (Pagina e
  gatuita la ~2-5% din prieteni; profilul ajunge la aproape toti).
- DAR postarea automata pe profil personal e impotriva ToS Facebook si duce la
  ban de cont. De aceea acest tool NU posteaza — genereaza DRAFT-uri gata de
  copy-paste pe care le pui manual (2-3 minute/zi).

Ce face:
1. Alege cele mai bune deal-uri care CHIAR produc comision (2Performant /
   Profitshare) — sare peste linkurile brute evomag/vegis.ro care nu aduc bani.
2. Le scrie in ton personal, de prieten care a gasit un chilipir (nu de marketer).
3. Aplica tactica "link in primul comentariu" (Facebook gatuie postarile cu link
   extern in corp; linkul in comentariu pastreaza reach-ul).
4. Roteste magazine/categorii si nu repeta deal-uri de la o zi la alta (log local).
5. Scrie totul intr-un fisier .md datat, gata de copiat.

Rulare:
    python agents/marketing/personal_fb_generator.py            # 5 postari azi
    python agents/marketing/personal_fb_generator.py --count 3  # cate postari
    python agents/marketing/personal_fb_generator.py --reset    # sterge log dedup
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEALS = ROOT / "data" / "deals.json"
STORES = ROOT / "data" / "stores.json"
OUT_DIR = ROOT / "data" / "marketing"
LOG = OUT_DIR / "fb_personal_log.json"

SITE = "https://ghidulreducerilor.ro"

# Doar linkuri care produc comision. Excludem brute (evomag.ro, vegis.ro direct).
def earns_commission(link: str) -> bool:
    link = (link or "").lower()
    if "2performant" in link or "profitshare" in link or "quicklink" in link:
        return True
    return False


# Hook-uri de deschidere (ton personal, variat, ca sa nu para sablon)
HOOKS = [
    "Am dat peste asta si mi s-a parut chilipir real 👀",
    "Nu stiu voi, dar eu la pretul asta as lua 👇",
    "Gasit azi cautand cadouri, poate prinde bine cuiva 🎁",
    "Chestii de care chiar ai nevoie in casa, la pret bun acum:",
    "Daca tot cautati reduceri reale (nu prostii umflate), asta e ok:",
    "M-am uitat prin reduceri si asta iese in evidenta:",
    "Pentru cei care ma tot intreaba de unde iau chilipiruri 😄",
    "Reducere serioasa aici, am verificat ca pretul e real:",
]

CTA_COMMENT = [
    "Detalii + pretul actual aici 👉 {url}",
    "Link + alte reduceri la {magazin} 👉 {url}",
    "Aici il gasiti 👉 {url}",
    "Toate reducerile la {magazin} 👉 {url}",
]


def load_json(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def deal_score(d: dict) -> float:
    """Scor: reducere procentuala + economie absoluta (log-scalata)."""
    proc = float(d.get("procent_reducere") or 0)
    econ = float(d.get("pret_original") or 0) - float(d.get("pret_redus") or 0)
    return proc + min(econ / 20.0, 40.0)


def clean_title(t: str) -> str:
    t = (t or "").strip()
    # scoate prefixul "Resigilat!" lipit si ID-urile din coada
    t = t.replace("Resigilat!", "Resigilat — ")
    for marker in [" (ID ", " (id ", " - ID "]:
        if marker in t:
            t = t.split(marker)[0]
    return t.strip().rstrip("(").strip()


def pick_deals(count: int, max_price: float = 400.0,
               min_price: float = 25.0) -> list[dict]:
    raw = load_json(DEALS, [])
    arr = raw if isinstance(raw, list) else raw.get("deals", [])
    log = load_json(LOG, {})
    seen = set(log.keys())

    pool = []
    for d in arr:
        if d.get("activ") is False:
            continue
        if d.get("id") in seen:
            continue
        try:
            po = float(d.get("pret_original") or 0)
            pr = float(d.get("pret_redus") or 0)
            proc = float(d.get("procent_reducere") or 0)
        except (TypeError, ValueError):
            continue
        if pr <= 0 or po <= pr or proc < 30:
            continue
        if pr > max_price:  # produse de impuls pentru prieteni, nu software scump
            continue
        if pr < min_price:  # sub ~25 lei nu e "chilipir" de recomandat prietenilor
            continue
        if not earns_commission(d.get("link_afiliat", "")):
            continue
        titlu = d.get("titlu") or ""
        if len(titlu) < 12:
            continue
        if not d.get("imagine_url"):
            continue
        pool.append(d)

    pool.sort(key=deal_score, reverse=True)

    # Rotatie: max 1 deal per magazin in selectia zilnica, ca sa para variat
    picked, used_stores = [], set()
    for d in pool:
        if d["magazin"] in used_stores:
            continue
        picked.append(d)
        used_stores.add(d["magazin"])
        if len(picked) >= count:
            break
    # daca n-am umplut (putine magazine), completeaza fara restrictie
    if len(picked) < count:
        for d in pool:
            if d in picked:
                continue
            picked.append(d)
            if len(picked) >= count:
                break
    return picked


def store_name(magazin: str, stores: list[dict]) -> str:
    for s in stores:
        if s.get("slug") == magazin:
            return s.get("nume", magazin)
    return magazin


def render_post(d: dict, stores: list[dict]) -> dict:
    magazin = d["magazin"]
    nume = store_name(magazin, stores)
    titlu = clean_title(d["titlu"])
    pr = int(round(float(d["pret_redus"])))
    po = int(round(float(d["pret_original"])))
    proc = int(round(float(d["procent_reducere"])))
    # UTM ca sa vezi in Google Analytics cat trafic aduce FB-ul personal
    url = f"{SITE}/reduceri/{magazin}?utm_source=facebook&utm_medium=personal&utm_campaign=fb_perso"

    hook = random.choice(HOOKS)
    body = (
        f"{hook}\n\n"
        f"{titlu}\n"
        f"💰 {pr} lei (era {po} lei) — adica -{proc}%\n\n"
        f"(pret verificat, nu reducere umflata)"
    )
    comment = random.choice(CTA_COMMENT).format(url=url, magazin=nume)
    return {"id": d["id"], "body": body, "comment": comment, "url": url,
            "magazin": nume, "proc": proc}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=5)
    ap.add_argument("--max-price", type=float, default=400.0,
                    help="pret maxim (lei) — produse de impuls, implicit 400")
    ap.add_argument("--min-price", type=float, default=25.0,
                    help="pret minim (lei) — sub asta nu e chilipir de recomandat, implicit 25")
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.reset and LOG.exists():
        LOG.unlink()
        print("Log dedup sters.")

    stores = load_json(STORES, [])
    if isinstance(stores, dict):
        stores = stores.get("stores", [])

    deals = pick_deals(args.count, args.max_price, args.min_price)
    if not deals:
        print("Niciun deal nou eligibil (toate promovate deja sau fara comision). "
              "Ruleaza cu --reset ca sa reiei de la capat.")
        return

    posts = [render_post(d, stores) for d in deals]

    today = date.today().isoformat()
    out = OUT_DIR / f"fb_personal_{today}.md"
    lines = [
        f"# Postari Facebook personal — {today}",
        "",
        "**Cum folosesti:** pentru fiecare postare, copiezi textul de la *POSTARE*, ",
        "il pui pe profilul tau, atasezi manual o poza a produsului (optional dar ",
        "creste reach-ul), postezi. **Imediat dupa**, pui textul de la *PRIMUL ",
        "COMENTARIU* ca prim comentariu la postare (asa Facebook nu iti gatuie reach-ul ",
        "pentru link extern).",
        "",
        "**Reguli anti-ban:** max 2-3 postari/zi pe profil, la interval de cateva ore. ",
        "Nu posta acelasi text de mai multe ori. Raspunde la comentarii (semnal pozitiv ",
        "pentru algoritm).",
        "",
        "---",
        "",
    ]
    for i, p in enumerate(posts, 1):
        lines += [
            f"## {i}. {p['magazin']} · -{p['proc']}%",
            "",
            "**POSTARE (copiaza asta pe profil):**",
            "```",
            p["body"],
            "```",
            "",
            "**PRIMUL COMENTARIU (pune imediat dupa postare):**",
            "```",
            p["comment"],
            "```",
            f"Poza produs: `{next((d.get('imagine_url') for d in deals if d['id']==p['id']), '')}`",
            "",
            "---",
            "",
        ]
    out.write_text("\n".join(lines), encoding="utf-8")

    # actualizeaza log dedup
    log = load_json(LOG, {})
    now = datetime.now().isoformat()
    for p in posts:
        log[p["id"]] = now
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK: {len(posts)} postari scrise in: {out}")
    for p in posts:
        print(f"   - {p['magazin']} (-{p['proc']}%)")


if __name__ == "__main__":
    main()
