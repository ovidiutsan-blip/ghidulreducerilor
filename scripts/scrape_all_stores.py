#!/usr/bin/env python3
"""
Scrape real products from all stores + generate Profitshare links.
Flow: eMAG SSR scrape -> PS campaigns -> other stores direct -> PS link generation -> deals.json
"""
import http.client, hmac, hashlib, time, json, os, re, sys, requests
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

API_HOST = "api.profitshare.ro"
API_USER = os.environ.get("PROFITSHARE_API_USER", "")
API_KEY = os.environ.get("PROFITSHARE_API_KEY", "")
PS_STORES = {"emag", "fashion-days", "vexio", "libris", "fornello", "forit"}

STORE_SEARCH = {
    "notino": "https://www.notino.ro/cauta/?q={}",
    "answear": "https://www.answear.ro/s/{}",
    "decathlon": "https://www.decathlon.ro/search?Ntt={}",
    "catena": "https://www.catena.ro/cautare?q={}",
    "cel": "https://www.cel.ro/cauta/{}",
    "pcgarage": "https://www.pcgarage.ro/cauta/?q={}",
}

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ro-RO,ro;q=0.9",
})


def make_auth(method, endpoint, qs=""):
    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    sig = f"{method}{endpoint}?{qs}/{API_USER}{date}"
    auth = hmac.new(API_KEY.encode(), sig.encode(), hashlib.sha1).hexdigest()
    return {
        "Date": date, "X-PS-Client": API_USER,
        "X-PS-Accept": "json", "X-PS-Auth": auth,
        "Content-Type": "application/x-www-form-urlencoded",
    }


def generate_ps_links(links_data):
    """Generate Profitshare tracking links in batches of 20."""
    all_results = {}
    for i in range(0, len(links_data), 20):
        batch = links_data[i:i+20]
        post_data = {}
        for j, link in enumerate(batch):
            post_data[f"{j}[name]"] = link["name"]
            post_data[f"{j}[url]"] = link["url"]
        body = urlencode(post_data)
        headers = make_auth("POST", "affiliate-links/", "")
        conn = http.client.HTTPSConnection(API_HOST, timeout=30)
        try:
            conn.request("POST", "/affiliate-links/?", body, headers)
            resp = conn.getresponse()
            if resp.status in (200, 201):
                results = json.loads(resp.read().decode("utf-8")).get("result", [])
                for r in results:
                    ps_url = r.get("ps_url", "").replace("http://profitshare.ro", "https://profitshare.ro")
                    if ps_url:
                        all_results[r["name"]] = ps_url
        finally:
            conn.close()
        time.sleep(0.5)
    return all_results


def scrape_emag():
    """Scrape real products from eMAG category pages (SSR)."""
    print("=== STEP 1: Scraping eMAG products ===")
    deals = []
    categories = [
        ("https://www.emag.ro/telefoane-mobile/sort-discountdesc/c", "electronice"),
        ("https://www.emag.ro/laptopuri/sort-discountdesc/c", "electronice"),
        ("https://www.emag.ro/televizoare/sort-discountdesc/c", "electronice"),
        ("https://www.emag.ro/tablete/sort-discountdesc/c", "electronice"),
        ("https://www.emag.ro/casti-audio/sort-discountdesc/c", "electronice"),
        ("https://www.emag.ro/aparate-de-aer-conditionat/sort-discountdesc/c", "casa"),
        ("https://www.emag.ro/masini-de-spalat-rufe/sort-discountdesc/c", "casa"),
        ("https://www.emag.ro/aspiratoare-robot/sort-discountdesc/c", "casa"),
    ]

    for url, cat in categories:
        cat_name = url.split("/")[3]
        try:
            r = session.get(url, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(".card-item.card-standard")
            count = 0

            for card in cards[:3]:
                name = card.get("data-name", "")
                product_url = card.get("data-url", "")
                if not name or not product_url:
                    continue

                price = 0
                fav_btn = card.select_one("[data-product]")
                if fav_btn:
                    try:
                        pdata = json.loads(fav_btn.get("data-product", "{}"))
                        price = float(pdata.get("price", 0))
                    except Exception:
                        pass

                discount = 0
                badge = card.select_one(".badge-discount")
                if badge:
                    m = re.search(r"(\d+)", badge.get_text())
                    if m:
                        d = int(m.group(1))
                        if 10 <= d <= 85:
                            discount = d

                old_price = round(price / (1 - discount / 100)) if discount > 0 and price > 0 else 0
                if price <= 0 or discount < 10:
                    continue

                # Get og:image from product page
                img = ""
                try:
                    pr = session.get(product_url, timeout=10)
                    ps = BeautifulSoup(pr.text, "html.parser")
                    og = ps.select_one('meta[property="og:image"]')
                    if og:
                        img = og.get("content", "")
                        if img.startswith("//"):
                            img = "https:" + img
                except Exception:
                    pass

                deal_id = f"emag-{hashlib.md5(product_url.encode()).hexdigest()[:8]}"
                deals.append({
                    "id": deal_id, "magazin": "emag", "titlu": name[:100],
                    "pret_redus": price, "pret_original": old_price, "procent_reducere": discount,
                    "imagine_url": img, "product_url": product_url, "link_afiliat": product_url,
                    "categorie": cat, "data_adaugare": "2026-04-04", "activ": True,
                })
                count += 1

            if count:
                print(f"  {cat_name}: {count} products")
            time.sleep(0.5)
        except Exception as e:
            print(f"  {cat_name}: error {str(e)[:40]}")

    print(f"  Total eMAG: {len(deals)}")
    return deals


def load_other_stores():
    """Load other store deals from backup with direct search links."""
    print("\n=== STEP 2: Other stores (direct links) ===")
    backup_path = ROOT / "data" / "deals_backup_20260404.json"
    if not backup_path.exists():
        print("  No backup found, skipping")
        return []

    with open(backup_path, "r", encoding="utf-8") as f:
        old_deals = json.load(f)

    other_deals = []
    for d in old_deals:
        store = d.get("magazin", "")
        if store in STORE_SEARCH:
            title = d.get("titlu", "")
            link = STORE_SEARCH[store].format(quote_plus(title))
            d["link_afiliat"] = link
            d["product_url"] = link
            other_deals.append(d)
        elif store in PS_STORES and store != "emag":
            # Non-eMAG Profitshare stores — keep with search URL
            title = d.get("titlu", "")
            store_urls = {
                "fashion-days": "https://www.fashiondays.ro/search/{}",
                "vexio": "https://www.vexio.ro/cauta/{}",
                "libris": "https://www.libris.ro/cautare?fsearch={}",
                "fornello": "https://www.fornello.ro/cautare?s={}",
                "forit": "https://www.forit.ro/cauta/{}",
            }
            if store in store_urls:
                link = store_urls[store].format(quote_plus(title))
                d["link_afiliat"] = link
                d["product_url"] = link
                other_deals.append(d)

    print(f"  Other stores: {len(other_deals)}")
    return other_deals


def load_campaigns():
    """Load Profitshare campaigns."""
    print("\n=== STEP 3: Profitshare campaigns ===")
    camp_path = ROOT / "data" / "raw" / "profitshare_campaigns.json"
    if camp_path.exists():
        with open(camp_path, "r", encoding="utf-8") as f:
            campaigns = json.load(f)
        print(f"  Campaigns: {len(campaigns)}")
        return campaigns
    print("  No campaigns file found")
    return []


def main():
    if not API_USER or not API_KEY:
        print("Missing PROFITSHARE_API_USER / PROFITSHARE_API_KEY")
        sys.exit(1)

    # Collect all deals
    emag_deals = scrape_emag()
    other_deals = load_other_stores()
    campaign_deals = load_campaigns()

    all_deals = emag_deals + other_deals + campaign_deals

    # Generate Profitshare links for eligible stores
    print(f"\n=== STEP 4: Generating Profitshare links ===")
    links_to_gen = []
    for d in all_deals:
        if d["magazin"] in PS_STORES and "profitshare.ro" not in d.get("link_afiliat", ""):
            url = d.get("product_url") or d.get("link_afiliat", "")
            if url and "profitshare" not in url:
                links_to_gen.append({"name": d["id"], "url": url})

    print(f"  Generating PS links for {len(links_to_gen)} deals...")
    ps_map = generate_ps_links(links_to_gen)
    print(f"  Got {len(ps_map)} links back")

    for d in all_deals:
        if d["id"] in ps_map:
            d["link_afiliat"] = ps_map[d["id"]]

    # Save
    deals_path = ROOT / "data" / "deals.json"
    with open(deals_path, "w", encoding="utf-8") as f:
        json.dump(all_deals, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"FINAL: {len(all_deals)} deals saved to deals.json")
    print(f"{'='*60}")

    stores = {}
    for d in all_deals:
        s = d["magazin"]
        stores.setdefault(s, {"total": 0, "ps": 0, "direct": 0})
        stores[s]["total"] += 1
        if "profitshare.ro" in d.get("link_afiliat", ""):
            stores[s]["ps"] += 1
        else:
            stores[s]["direct"] += 1

    for s in sorted(stores):
        info = stores[s]
        print(f"  {s:15s}: {info['total']:2d} deals ({info['ps']} PS, {info['direct']} direct)")


if __name__ == "__main__":
    main()
