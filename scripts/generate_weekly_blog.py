"""Auto-blog generator: creates a weekly "Top Reduceri Saptamana" TSX article.

Picks top-discount active deals with validated omnibus price, groups by store,
generates a TSX article module, and registers it in lib/blog.ts.

Run weekly (Monday 07:00 UTC via GitHub Actions).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# -- Config ---------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DEALS_PATH = REPO_ROOT / "data" / "deals.json"
STORES_PATH = REPO_ROOT / "data" / "stores.json"
ARTICLES_DIR = REPO_ROOT / "app" / "blog" / "articles"
BLOG_REGISTRY = REPO_ROOT / "lib" / "blog.ts"
MAX_DEALS = 12
MIN_DISCOUNT_PCT = 25

STORE_EMOJI = {
    "emag": "🛒",
    "fashiondays": "👗",
    "altex": "💻",
    "flanco": "📺",
    "notino": "💄",
    "answear": "👜",
    "drmax": "💊",
    "vegis": "🌿",
    "mathaus": "🔨",
    "hiris": "✨",
    "streamstore": "💿",
    "alecoair": "❄️",
    "case-smart": "🏠",
    "novodoors": "🚪",
    "techstar": "💻",
    "hotpick": "🔌",
    "fornello": "🍳",
    "libris": "📚",
    "elefant": "📖",
    "watch24": "⌚",
    "forit": "🖥️",
}

# -- Helpers --------------------------------------------------------------

def load_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def disc_pct(d: dict) -> float:
    p = d.get("procent_reducere")
    if isinstance(p, (int, float)) and p > 0:
        return float(p)
    pv = d.get("pret_original")
    pn = d.get("pret_redus") or d.get("price")
    try:
        pv = float(pv)
        pn = float(pn)
        if pv > 0 and 0 < pn < pv:
            return round((pv - pn) / pv * 100, 1)
    except (TypeError, ValueError):
        pass
    return 0.0


def fmt_price(v) -> str:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    # Romanian-style: 1.234,56 (but simple integer-ish)
    if f.is_integer():
        return f"{int(f)} RON"
    return f"{f:.2f}".replace(".", ",") + " RON"


def escape_jsx(s: str) -> str:
    """Escape text for JSX: quotes, braces, backticks."""
    if s is None:
        return ""
    return (
        s.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("`", "\\`")
    )


def week_info(today: date | None = None):
    today = today or date.today()
    # ISO week starting Monday
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    iso_year, iso_week, _ = today.isocalendar()
    slug = f"top-reduceri-saptamana-{iso_year}-w{iso_week:02d}"
    range_ro = f"{monday.strftime('%d %b')} - {sunday.strftime('%d %b %Y')}"
    return {
        "slug": slug,
        "iso": f"{iso_year}-W{iso_week:02d}",
        "monday": monday.isoformat(),
        "today": today.isoformat(),
        "range_ro": range_ro,
        "year": iso_year,
        "week": iso_week,
    }


# -- Main -----------------------------------------------------------------

def select_top_deals(deals: list[dict]) -> list[dict]:
    def is_valid(d):
        if not d.get("activ", True):
            return False
        if d.get("is_fake_discount") is True:
            return False
        if disc_pct(d) < MIN_DISCOUNT_PCT:
            return False
        if not d.get("titlu"):
            return False
        if not (d.get("id") or d.get("slug")):
            return False
        return True

    pool = [d for d in deals if is_valid(d)]
    # Dedup per store: max 2 deals per store to spread variety
    per_store: dict[str, list[dict]] = {}
    pool.sort(key=disc_pct, reverse=True)
    for d in pool:
        store = d.get("magazin") or d.get("store") or "unknown"
        per_store.setdefault(store, []).append(d)

    final: list[dict] = []
    # round-robin first pass, then fill
    i = 0
    while len(final) < MAX_DEALS and any(per_store.values()):
        stores = list(per_store.keys())
        if i >= len(stores):
            break
        store = stores[i % len(stores)]
        if per_store[store]:
            final.append(per_store[store].pop(0))
        if not per_store[store]:
            del per_store[store]
        i += 1

    # fill remaining by raw pool order
    for d in pool:
        if len(final) >= MAX_DEALS:
            break
        if d not in final:
            final.append(d)

    return final[:MAX_DEALS]


def render_article_tsx(week: dict, deals: list[dict], stores_lookup: dict) -> str:
    title = f"Top Reduceri Săptămâna {week['range_ro']} — {len(deals)} Oferte Verificate"
    description = (
        f"Selecția editorială a celor mai bune {len(deals)} reduceri active în săptămâna {week['range_ro']}. "
        "Produse cu reducere reală (validare omnibus), link direct către magazin, prețuri în RON."
    )
    excerpt = (
        f"În săptămâna {week['range_ro']} am selectat {len(deals)} oferte cu reducere de peste "
        f"{MIN_DISCOUNT_PCT}% — toate validate prin regula omnibus (preț minim ultimele 30 de zile) "
        "și cu link afiliat funcțional. Actualizat automat luni dimineața."
    )

    # Pick top emoji from deals
    top_deal = deals[0] if deals else None
    cover_emoji = STORE_EMOJI.get((top_deal or {}).get("magazin", ""), "🛍️")

    # Build deal items JSX
    deal_items_jsx = []
    for d in deals:
        store = d.get("magazin") or "necunoscut"
        store_info = stores_lookup.get(store, {})
        store_label = store_info.get("nume") or store_info.get("name") or store.capitalize()
        emoji = STORE_EMOJI.get(store, "🛍️")
        titlu = escape_jsx(d.get("titlu", ""))
        pret_orig = d.get("pret_original") or d.get("originalPrice")
        pret_redus = d.get("pret_redus") or d.get("price")
        pct = int(round(disc_pct(d)))
        deal_id = d.get("id") or d.get("slug")
        out_url = f"/out/{deal_id}"

        price_block = ""
        if pret_orig and pret_redus:
            price_block = (
                f"          <p className=\"deal-price\">\n"
                f"            <span className=\"old\">{fmt_price(pret_orig)}</span>{{' → '}}\n"
                f"            <strong>{fmt_price(pret_redus)}</strong>{{' '}}\n"
                f"            <span className=\"disc\">(-{pct}%)</span>\n"
                f"          </p>\n"
            )
        else:
            price_block = f"          <p className=\"deal-price\"><span className=\"disc\">-{pct}%</span></p>\n"

        item = (
            f"      <div className=\"deal-card\">\n"
            f"        <h3>{emoji} {store_label}</h3>\n"
            f"        <p className=\"deal-title\">{titlu}</p>\n"
            f"{price_block}"
            f"        <p><a href=\"{out_url}\" rel=\"nofollow sponsored\">Vezi oferta pe {store_label} →</a></p>\n"
            f"      </div>\n"
        )
        deal_items_jsx.append(item)

    deals_jsx = "\n".join(deal_items_jsx)

    tsx = f'''import type {{ BlogArticle }} from '@/lib/blog'

export const article: BlogArticle = {{
  meta: {{
    slug: '{week["slug"]}',
    title: '{escape_jsx(title)}',
    description: '{escape_jsx(description)}',
    excerpt: '{escape_jsx(excerpt)}',
    publishedAt: '{week["monday"]}',
    updatedAt: '{week["today"]}',
    author: 'Redacția GhidulReducerilor',
    tags: ['top-reduceri', 'saptamanal', 'oferte-verificate', '{week["year"]}'],
    coverEmoji: '{cover_emoji}',
    readingTimeMinutes: 4,
  }},
  Body: () => (
    <>
      <h2>Cele mai bune {len(deals)} reduceri din săptămâna {week["range_ro"]}</h2>
      <p>
        În fiecare luni dimineață publicăm o selecție editorială cu cele mai bune oferte active
        din magazinele partenere. Toate ofertele de mai jos au <strong>reducere reală</strong> —
        validăm prețul minim din ultimele 30 de zile (regulament Omnibus) înainte de a le
        include. Dacă un produs are <em>fake discount</em>, nu intră pe această listă.
      </p>
      <p>
        Fiecare link este afiliat: plătești exact prețul afișat pe site-ul magazinului, dar noi
        primim un mic comision care ne ajută să păstrăm site-ul gratuit. Mulțumim că ne susții.
      </p>

      <h2>Ofertele săptămânii</h2>
      <div className="weekly-deals-grid">
{deals_jsx}      </div>

      <h2>Cum folosești lista pentru a economisi maxim</h2>
      <ul>
        <li>
          <strong>Compară cu istoricul de preț</strong> înainte de cumpărare. Majoritatea
          magazinelor afișează graficul Omnibus al prețului minim în ultimele 30 de zile — dacă
          reducerea e reală, vezi că prețul curent e sub pragul de referință.
        </li>
        <li>
          <strong>Folosește codurile promo</strong> pe lângă reducerea afișată. Pe pagina fiecărui
          magazin, la secțiunea <em>Coduri promoționale</em>, verificăm manual săptămânal care
          coduri funcționează. Le aplici la checkout după ce selectezi produsul.
        </li>
        <li>
          <strong>Setează alertă de preț</strong> dacă oferta nu e pe lista săptămânii dar îți
          place produsul — unele magazine scad prețul cu 10-20% în plus în ultima zi de campanie.
        </li>
        <li>
          <strong>Verifică politica de retur</strong>. În România legea garantează 14 zile
          calendaristice de retur fără motiv la cumpărăturile online, dar multe magazine oferă
          între 30 și 100 de zile. Important mai ales pentru îmbrăcăminte și electronice mari.
        </li>
      </ul>

      <p className="blog-cta-note">
        Lista se actualizează automat luni dimineața. Dacă vrei să primești varianta săptămânală
        direct pe email, <a href="/newsletter">abonează-te la newsletter</a>.
      </p>
    </>
  ),
}}
'''
    return tsx


def register_in_blog_ts(week_slug: str) -> bool:
    """Insert new article import and registry entry. Returns True if modified."""
    source = BLOG_REGISTRY.read_text(encoding="utf-8")
    camel = re.sub(r"[-_](\w)", lambda m: m.group(1).upper(), week_slug)
    camel = camel[0].lower() + camel[1:]

    import_stmt = f"import {{ article as {camel} }} from '@/app/blog/articles/{week_slug}'"
    if import_stmt in source:
        print(f"[!] Registry already contains {week_slug}, skipping insert")
        return False

    # Insert import after last existing import
    import_matches = list(re.finditer(r"^import .+ from '@/app/blog/articles/[^']+'$", source, re.MULTILINE))
    if not import_matches:
        print("[!] No existing article imports found — cannot insert")
        return False
    last_import = import_matches[-1]
    insert_pos = last_import.end()
    source = source[:insert_pos] + "\n" + import_stmt + source[insert_pos:]

    # Insert entry at END of REGISTRY array
    registry_match = re.search(r"const REGISTRY: BlogArticle\[\] = \[(.*?)\n\]", source, re.DOTALL)
    if not registry_match:
        print("[!] REGISTRY array not found — cannot insert")
        return False

    old_block = registry_match.group(0)
    inner = registry_match.group(1)
    new_inner = inner.rstrip() + f",\n  {camel},\n"
    # normalize commas: avoid double comma
    new_inner = re.sub(r",\s*,", ",", new_inner)
    new_block = f"const REGISTRY: BlogArticle[] = [{new_inner}]"
    source = source.replace(old_block, new_block)

    BLOG_REGISTRY.write_text(source, encoding="utf-8")
    print(f"[+] Registered {camel} in lib/blog.ts")
    return True


def main():
    print("[*] Loading data...")
    deals = load_json(DEALS_PATH)
    stores = load_json(STORES_PATH)
    stores_lookup = {s.get("slug"): s for s in stores}
    print(f"[*] {len(deals)} deals, {len(stores)} stores")

    week = week_info()
    print(f"[*] Week: {week['iso']} ({week['range_ro']})")

    article_dir = ARTICLES_DIR / week["slug"]
    # We actually use a flat file, not a directory (matching existing pattern)
    article_file = ARTICLES_DIR / f"{week['slug']}.tsx"
    if article_file.exists():
        print(f"[!] {article_file.name} already exists — aborting to avoid overwrite")
        return 0

    top_deals = select_top_deals(deals)
    print(f"[*] Selected {len(top_deals)} deals (min discount {MIN_DISCOUNT_PCT}%)")
    for d in top_deals[:5]:
        print(f"    - {disc_pct(d):>5.1f}% {d.get('magazin')} - {d.get('titlu','')[:60]}")

    if len(top_deals) < 5:
        print(f"[!] Only {len(top_deals)} qualifying deals — need at least 5. Aborting.")
        return 1

    tsx = render_article_tsx(week, top_deals, stores_lookup)
    article_file.write_text(tsx, encoding="utf-8")
    print(f"[+] Wrote {article_file.relative_to(REPO_ROOT)}")

    register_in_blog_ts(week["slug"])

    print("[+] Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
