"""
facebook_agent.py — Generează posturi gata de copiat în grupuri Facebook RO.

Output: data/marketing/fb_posts_YYYY-MM-DD.json
  - 5 posturi de stiluri diferite (deal simplu, comparație preț, urgență, listă, story)
  - Fiecare post include textul + link-ul afiliaat + tag-uri recomandate
  - Verificare live a link-ului înainte de a include deal-ul

Grupuri țintă principale:
  - Oferte Romania (500k+)
  - Reduceri Romania
  - Vânătoare de chilipiruri
  - Oferte și Reduceri Online Romania
  - Economisim impreuna
"""

import json
import random
import requests
from pathlib import Path
from datetime import datetime

BASE       = Path(__file__).parent.parent.parent
SITE_BASE  = "https://ghidulreducerilor.ro"
OUTPUT_DIR = BASE / "data" / "marketing"


def _deal_link(d: dict) -> str:
    """Link corect pentru un deal: /out/{id} (redirect tracker intern)."""
    deal_id = d.get("id", "")
    if deal_id:
        return f"{SITE_BASE}/out/{deal_id}"
    # fallback: link afiliat direct
    return d.get("link_afiliat") or d.get("affiliate_url") or SITE_BASE

# ─── Template-uri posturi FB ─────────────────────────────────────────────────

def post_simplu(d: dict) -> str:
    titlu = d.get("titlu") or d.get("title", "Produs")
    pct   = d.get("procent_reducere") or d.get("discount_percent") or 0
    pret  = d.get("pret_redus") or d.get("price") or 0
    orig  = d.get("pret_original") or d.get("originalPrice") or 0
    store = (d.get("magazin") or d.get("store", "")).capitalize()
    link  = _deal_link(d)
    return (
        f"🔥 REDUCERE -{pct}% la {store}!\n\n"
        f"📦 {titlu}\n"
        f"💰 {pret} lei (față de {orig} lei)\n\n"
        f"👉 {link}\n\n"
        f"#reduceri #oferte #{store.lower()} #ghidulreducerilor"
    )


def post_comparatie(d: dict) -> str:
    titlu = d.get("titlu") or d.get("title", "Produs")
    pct   = d.get("procent_reducere") or d.get("discount_percent") or 0
    pret  = d.get("pret_redus") or d.get("price") or 0
    orig  = d.get("pret_original") or d.get("originalPrice") or 0
    economie = orig - pret
    store = (d.get("magazin") or d.get("store", "")).capitalize()
    link  = _deal_link(d)
    return (
        f"💡 Economisești {economie:.0f} lei cu această ofertă!\n\n"
        f"🏷️ {titlu}\n\n"
        f"❌ Prețul normal: {orig} lei\n"
        f"✅ Prețul azi: {pret} lei\n"
        f"📉 Reducere: -{pct}%\n\n"
        f"🛒 Cumpără acum: {link}\n\n"
        f"#chilipir #reduceri #{store.lower()}"
    )


def post_urgenta(d: dict) -> str:
    titlu = d.get("titlu") or d.get("title", "Produs")
    pct   = d.get("procent_reducere") or d.get("discount_percent") or 0
    pret  = d.get("pret_redus") or d.get("price") or 0
    store = (d.get("magazin") or d.get("store", "")).capitalize()
    link  = _deal_link(d)
    return (
        f"⏰ OFERTĂ LIMITATĂ — fii primul!\n\n"
        f"➡️ {titlu}\n"
        f"💥 -{pct}% → doar {pret} lei pe {store}\n\n"
        f"Stocurile se epuizează repede la reduceri atât de mari.\n\n"
        f"🔗 {link}\n\n"
        f"#ofertazilei #reduceri #stocurilimitate"
    )


def post_lista(deals: list[dict]) -> str:
    """Post cu o listă de 3-5 deals (pentru postări 'top reduceri azi')."""
    linii = ["🛍️ TOP REDUCERI AZI — ce merită cumpărat:\n"]
    for i, d in enumerate(deals[:5], 1):
        titlu = (d.get("titlu") or d.get("title", "Produs"))[:45]
        pct   = d.get("procent_reducere") or d.get("discount_percent") or 0
        pret  = d.get("pret_redus") or d.get("price") or 0
        store = (d.get("magazin") or d.get("store", "")).capitalize()
        link  = _deal_link(d)
        linii.append(f"{i}. {titlu} — -{pct}% → {pret} lei ({store})\n   👉 {link}")
    linii.append(f"\nToate ofertele: {SITE_BASE}\n\n#reduceri #oferte #ghidulreducerilor")
    return "\n".join(linii)


def post_story(d: dict) -> str:
    """Post mai personal/narativ — mai bun pentru engagement."""
    titlu = d.get("titlu") or d.get("title", "produsul")
    pct   = d.get("procent_reducere") or d.get("discount_percent") or 0
    pret  = d.get("pret_redus") or d.get("price") or 0
    orig  = d.get("pret_original") or d.get("originalPrice") or 0
    store = (d.get("magazin") or d.get("store", "")).capitalize()
    link  = _deal_link(d)
    return (
        f"Azi dimineață am găsit asta și nu m-am putut abține să nu o împart cu voi 😅\n\n"
        f"{titlu} la -{pct}% pe {store}.\n\n"
        f"Normal costă {orig} lei, acum e {pret} lei. Economisești {orig-pret:.0f} lei.\n\n"
        f"Link direct (verificat, merge): {link}\n\n"
        f"P.S. Urmăriți ghidulreducerilor.ro — postăm cele mai bune oferte zilnic 🙏"
    )


# ─── Verificare live ─────────────────────────────────────────────────────────

def verify_link_live(url: str, timeout: int = 8) -> bool:
    """Verifică rapid dacă un link funcționează (HTTP 200)."""
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code < 400
    except Exception:
        try:
            r = requests.get(url, timeout=timeout, allow_redirects=True,
                             headers={"User-Agent": "Mozilla/5.0"}, stream=True)
            return r.status_code < 400
        except Exception:
            return False


# ─── Generator principal ─────────────────────────────────────────────────────

def generate_posts(deals: list[dict], verify_live: bool = True) -> dict:
    """
    Generează set complet de posturi pentru azi.
    Returnează dict cu toate posturile + metadata.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    verified_deals = []

    for d in deals:
        link = d.get("link_afiliat") or d.get("affiliate_url") or ""
        if verify_live and link:
            ok = verify_link_live(link)
            if not ok:
                print(f"  [skip] Link mort: {link[:60]}")
                continue
        verified_deals.append(d)

    if not verified_deals:
        return {"date": today, "posts": [], "deals_verified": 0}

    # Alegeăm deal-ul star pentru posturi individuale
    star = verified_deals[0]
    second = verified_deals[1] if len(verified_deals) > 1 else star

    posts = [
        {
            "tip": "deal_simplu",
            "deal_id": star.get("id"),
            "deal_titlu": star.get("titlu") or star.get("title"),
            "text": post_simplu(star),
            "imagine": star.get("imagine_url") or star.get("image"),
            "grupuri_recomandate": ["Oferte Romania", "Reduceri Romania"],
        },
        {
            "tip": "comparatie_pret",
            "deal_id": star.get("id"),
            "deal_titlu": star.get("titlu") or star.get("title"),
            "text": post_comparatie(star),
            "imagine": star.get("imagine_url") or star.get("image"),
            "grupuri_recomandate": ["Vânătoare de chilipiruri", "Economisim impreuna"],
        },
        {
            "tip": "urgenta",
            "deal_id": second.get("id"),
            "deal_titlu": second.get("titlu") or second.get("title"),
            "text": post_urgenta(second),
            "imagine": second.get("imagine_url") or second.get("image"),
            "grupuri_recomandate": ["Oferte și Reduceri Online Romania"],
        },
        {
            "tip": "lista_top",
            "deal_id": None,
            "deal_titlu": f"Top {min(5, len(verified_deals))} reduceri",
            "text": post_lista(verified_deals),
            "imagine": verified_deals[0].get("imagine_url") or verified_deals[0].get("image"),
            "grupuri_recomandate": ["Oferte Romania", "Reduceri Romania", "Vânătoare de chilipiruri"],
        },
        {
            "tip": "story_personal",
            "deal_id": random.choice(verified_deals[:3]).get("id"),
            "deal_titlu": (random.choice(verified_deals[:3]).get("titlu") or
                           random.choice(verified_deals[:3]).get("title")),
            "text": post_story(random.choice(verified_deals[:3])),
            "imagine": random.choice(verified_deals[:3]).get("imagine_url"),
            "grupuri_recomandate": ["Oferte Romania"],
        },
    ]

    return {
        "date": today,
        "deals_verified": len(verified_deals),
        "deals_skipped": len(deals) - len(verified_deals),
        "posts": posts,
    }


def save_posts(data: dict) -> Path:
    """Salvează posturile generate în data/marketing/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"fb_posts_{data['date']}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return out


if __name__ == "__main__":
    from deal_selector import select_top_deals
    deals = select_top_deals(8)
    print(f"Deals selectate: {len(deals)}")
    data = generate_posts(deals, verify_live=True)
    path = save_posts(data)
    print(f"\nSalvat: {path}")
    print(f"Posturi generate: {len(data['posts'])}, deal-uri verificate: {data['deals_verified']}")
    print("\n--- PREVIEW POST 1 ---")
    if data["posts"]:
        print(data["posts"][0]["text"])
