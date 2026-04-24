"""Profitshare feed -> data/deals.json transformer.
For each target merchant, fetch N pages, filter for real discounts (price_discounted < price_vat),
map to Deal schema, merge into existing deals.json (dedupe by product_url).
"""
import os, sys, json, hmac, hashlib, re, time
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv
load_dotenv()

API_URL = "https://api.profitshare.ro"
API_USER = os.getenv("PROFITSHARE_API_USER", "")
API_KEY = os.getenv("PROFITSHARE_API_KEY", "")
# Resolve repo root relative to this script (portable: works on Win local + Ubuntu CI)
BASE = Path(__file__).resolve().parent.parent
DEALS_PATH = BASE / "data" / "deals.json"


def call(method, endpoint, query=""):
    date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    sig = f"{method}{endpoint}/?{query}/{API_USER}{date_str}"
    auth = hmac.new(API_KEY.encode(), sig.encode(), hashlib.sha1).hexdigest()
    headers = {
        "Date": date_str, "X-PS-Client": API_USER,
        "X-PS-Accept": "json", "X-PS-Auth": auth,
    }
    url = f"{API_URL}/{endpoint}/" + (f"?{query}" if query else "")
    return requests.get(url, headers=headers, timeout=30)


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]


def fix_affiliate_link(link: str) -> str:
    """Profitshare returns `//app.profitshare.ro/...` -> prepend https:"""
    if link.startswith("//"):
        return "https:" + link
    return link


_BAD_IMG_PATTERNS = ("lazy-loader", "/layout/", "placeholder", "no-image", "noimage")

def is_bad_image(url: str) -> bool:
    """Return True if url is a known placeholder/bad image that must be replaced."""
    if not url or not url.startswith("http"):
        return True
    u = url.lower()
    if u.endswith(".gif"):
        return True
    return any(p in u for p in _BAD_IMG_PATTERNS)


def product_to_deal(p: dict, magazin: str, categorie: str, allowed_cats: list | None = None) -> dict:
    # Filter by Profitshare category_name when whitelist provided (ex: vegis -> only supplements, not food)
    if allowed_cats is not None:
        feed_cat = (p.get("category_name") or "").strip()
        if feed_cat not in allowed_cats:
            return None
    price_vat = float(p.get("price_vat") or 0)
    price_disc_raw = p.get("price_discounted")
    try:
        price_disc = float(price_disc_raw) if price_disc_raw not in (None, "", 0, "0") else None
    except (ValueError, TypeError):
        price_disc = None
    if price_disc is None or price_vat <= 0 or price_disc >= price_vat:
        return None
    pct = round((1 - price_disc / price_vat) * 100)
    name = p.get("name", "").strip()
    link = p.get("link", "")
    aff_link = fix_affiliate_link(p.get("affiliate_link", ""))
    img = p.get("image_original") or p.get("image") or ""
    # Normalize http -> https for https:// URLs
    if img.startswith("http://"):
        img = "https://" + img[7:]
    # Elimina placeholder-uri cunoscute — image_repair.py va incarca imaginea reala
    if is_bad_image(img):
        img = ""
    return {
        "id": f"ps-{magazin}-{slugify(name)[:40]}-{p.get('part_number', '')[-8:]}",
        "slug": slugify(name),
        "magazin": magazin,
        "titlu": name[:200],
        "imagine_url": img,
        "pret_original": round(price_vat, 2),
        "pret_redus": round(price_disc, 2),
        "procent_reducere": pct,
        "link_afiliat": aff_link,
        "product_url": link,
        "categorie": categorie,
        "data_adaugare": datetime.utcnow().strftime("%Y-%m-%d"),
        "activ": True,
        "is_active": True,
        "sursa": "profitshare",
    }


def fetch_deals(magazin: str, adv_id: int, categorie: str, max_pages: int = 20, min_pct: int = 10, allowed_cats: list | None = None):
    """Returns (deals, valid_urls, fetch_success).
    valid_urls = set of product_url for ALL products with a valid discount this run.
    fetch_success = True if at least one raw product was returned by the API (not API error).
    """
    deals = []
    valid_urls = set()
    total_raw = 0
    for page in range(1, max_pages + 1):
        resp = None
        # Retry with exponential backoff on 429
        for attempt in range(4):
            resp = call("GET", "affiliate-products", f"filters[advertiser]={adv_id}&page={page}")
            if resp.ok:
                break
            if resp.status_code == 429:
                wait = 2 ** attempt  # 1, 2, 4, 8 seconds
                print(f"  {magazin} page {page}: 429 backoff {wait}s (attempt {attempt+1}/4)")
                time.sleep(wait)
                continue
            # Non-429 error: stop
            break
        if resp is None or not resp.ok:
            print(f"  {magazin} page {page}: fail {resp.status_code if resp else 'no-response'}")
            break
        products = resp.json().get("result", {}).get("products", [])
        if not products:
            break
        total_raw += len(products)
        for p in products:
            d = product_to_deal(p, magazin, categorie, allowed_cats=allowed_cats)
            if d and d["procent_reducere"] >= min_pct:
                deals.append(d)
                valid_urls.add(d["product_url"])
        time.sleep(0.3)
    return deals, valid_urls, total_raw > 0


def main():
    if not API_USER or not API_KEY:
        print("WARN: PROFITSHARE_API_USER or PROFITSHARE_API_KEY missing; skipping feed import.")
        return
    # Load existing deals
    with open(DEALS_PATH, "r", encoding="utf-8") as f:
        existing = json.load(f)
    # Only block re-import on ACTIVE deals — expired deals allow re-import from another source.
    existing_urls = set(d.get("product_url") or d.get("link_afiliat") for d in existing if d.get("activ", True))
    existing_ids = set(d.get("id") for d in existing)
    print(f"Existing deals: {len(existing)}")

    # Per-merchant targets: loaded from ps_merchants.json (mirrors 2p_merchants.json pattern)
    ps_merchants_path = BASE / "agents" / "ps_merchants.json"
    with open(ps_merchants_path, encoding="utf-8") as _mf:
        _merchants = json.load(_mf)
    targets = [
        (m["slug"], m["adv_id"], m["categorie"],
         m.get("max_pages", 20), m.get("min_pct", 10), m.get("cat_whitelist"))
        for m in _merchants if m.get("activ", True)
    ]
    print(f"Loaded {len(targets)} active merchants from ps_merchants.json")

    all_new = []
    all_seen_urls: set = set()   # valid product_urls across all merchants this run
    successful_slugs: set = set()  # merchants where API call returned data (not error)

    for magazin, adv_id, categorie, max_pages, min_pct, allowed_cats in targets:
        print(f"\n[{magazin}] fetching {max_pages}p (min {min_pct}% reducere), cat='{categorie}', whitelist={allowed_cats is not None}")
        new_deals, valid_urls, success = fetch_deals(magazin, adv_id, categorie, max_pages=max_pages, min_pct=min_pct, allowed_cats=allowed_cats)
        print(f"  extracted: {len(new_deals)} deals w/ real discount")
        if success:
            all_seen_urls |= valid_urls
            successful_slugs.add(magazin)
        # Dedupe vs existing
        added = 0
        for d in new_deals:
            if d["product_url"] in existing_urls or d["id"] in existing_ids:
                continue
            existing_urls.add(d["product_url"])
            existing_ids.add(d["id"])
            all_new.append(d)
            added += 1
        print(f"  after dedupe: +{added} new")

    # ─── Expire PS deals no longer in feed ───────────────────────────────────
    # Only expire deals from merchants we successfully fetched (not API errors).
    expired_count = 0
    now_date = datetime.utcnow().strftime("%Y-%m-%d")
    for d in existing:
        if (d.get("activ") and
                d.get("magazin") in successful_slugs and
                d.get("id", "").startswith("ps-") and
                d.get("product_url") not in all_seen_urls):
            d["activ"] = False
            d["is_active"] = False
            d["expired_at"] = now_date
            expired_count += 1
    if expired_count:
        print(f"  Expired: {expired_count} PS deals no longer in feed (reducere incheiata)")

    print(f"\nTOTAL new deals: {len(all_new)}")
    merged = existing + all_new
    # Sort: active first, then by procent_reducere desc
    merged.sort(key=lambda d: (-1 if d.get("activ") else 0, -(d.get("procent_reducere") or 0)))
    with open(DEALS_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"WROTE {DEALS_PATH} -> {len(merged)} total deals")

    # Summary by magazin + categorie
    from collections import Counter
    by_mag = Counter(d["magazin"] for d in merged if d.get("activ"))
    by_cat = Counter(d["categorie"] for d in merged if d.get("activ"))
    print("\nActive deals by magazin:")
    for k, v in by_mag.most_common():
        print(f"  {k}: {v}")
    print("\nActive deals by categorie:")
    for k, v in by_cat.most_common():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
