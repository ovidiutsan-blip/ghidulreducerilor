#!/usr/bin/env python3
"""
Scrape Elefant.ro products and merge into deals.json with Profitshare links.
"""
import requests, re, hashlib, json, time, hmac, os, http.client, sys
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Load env
for env_file in [ROOT / ".env", ROOT / ".env.local"]:
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            eq = line.find("=")
            if eq > 0:
                k, v = line[:eq].strip(), line[eq + 1:].strip()
                os.environ.setdefault(k, v)

API_USER = os.environ.get("PROFITSHARE_API_USER", "")
API_KEY = os.environ.get("PROFITSHARE_API_KEY", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ro-RO,ro;q=0.9",
}


def extract_price(text):
    text = text.replace(".", "").replace(",", ".").replace("\xa0", "").replace("lei", "").strip()
    m = re.search(r"(\d+\.?\d*)", text)
    return float(m.group(1)) if m else 0


def slugify(text):
    import unicodedata
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80]


def generate_ps_links(links_data):
    """Generate Profitshare affiliate links."""
    if not API_USER or not API_KEY:
        print("  WARN: No Profitshare credentials")
        return {}

    ps_map = {}
    for i in range(0, len(links_data), 20):
        batch = links_data[i:i + 20]
        post_data = {}
        for j, link in enumerate(batch):
            post_data[f"{j}[name]"] = link["name"]
            post_data[f"{j}[url]"] = link["url"]

        body = urlencode(post_data)
        date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
        sig = f"POSTaffiliate-links/?/{API_USER}{date}"
        auth = hmac.new(API_KEY.encode(), sig.encode(), hashlib.sha1).hexdigest()

        h = {
            "Date": date, "X-PS-Client": API_USER,
            "X-PS-Accept": "json", "X-PS-Auth": auth,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        conn = http.client.HTTPSConnection("api.profitshare.ro", timeout=30)
        try:
            conn.request("POST", "/affiliate-links/?", body, h)
            resp = conn.getresponse()
            if resp.status in (200, 201):
                results = json.loads(resp.read().decode("utf-8")).get("result", [])
                for r in results:
                    ps_url = r.get("ps_url", "").replace("http://profitshare.ro", "https://profitshare.ro")
                    if ps_url:
                        ps_map[r["name"]] = ps_url
                print(f"  PS batch: {len(ps_map)} links generated")
            else:
                print(f"  PS API error: {resp.status}")
        except Exception as e:
            print(f"  PS error: {e}")
        finally:
            conn.close()

    return ps_map


def scrape_elefant():
    """Scrape Elefant.ro products from product pages."""
    print("=== Scraping Elefant.ro ===")
    deals = []
    categories = [
        ("carti", "https://www.elefant.ro/carti"),
        ("jucarii", "https://www.elefant.ro/list/jucarii-copii-bebe/jucarii"),
    ]

    for cat_name, cat_url in categories:
        print(f"  Categorie: {cat_name}")
        try:
            r = requests.get(cat_url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                print(f"    HTTP {r.status_code}")
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(".product-list-item")

            product_links = []
            for card in cards:
                a = card.select_one('a[href*="elefant.ro"]')
                if a:
                    href = a.get("href", "")
                    if href and "/INTERSHOP" not in href and href.startswith("http"):
                        product_links.append(href)

            print(f"    {len(product_links)} product links, fetching top 10...")

            for url in product_links[:10]:
                try:
                    pr = requests.get(url, headers=HEADERS, timeout=10)
                    ps = BeautifulSoup(pr.text, "html.parser")

                    title_el = ps.select_one("h1")
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)

                    old_el = ps.select_one(".old-price")
                    new_el = ps.select_one(".current-price")
                    if not new_el:
                        continue

                    price_new = extract_price(new_el.get_text())
                    price_old = extract_price(old_el.get_text()) if old_el else 0

                    if price_old <= price_new or price_new <= 0:
                        continue

                    discount = round((price_old - price_new) / price_old * 100)
                    if discount < 15:
                        continue

                    img_el = ps.select_one('img[src*="media.elefant"]')
                    img_url = img_el.get("src", "") if img_el else ""

                    deal_id = f"elefant-{hashlib.md5(url.encode()).hexdigest()[:8]}"
                    deals.append({
                        "id": deal_id,
                        "slug": slugify(title),
                        "magazin": "elefant",
                        "titlu": title[:150],
                        "pret_original": price_old,
                        "pret_redus": price_new,
                        "procent_reducere": discount,
                        "imagine_url": img_url,
                        "product_url": url,
                        "link_afiliat": "",
                        "categorie": cat_name,
                        "data_adaugare": "2026-04-04",
                        "activ": True,
                    })
                    print(f"    + {title[:50]} ({discount}% off, {price_new} lei)")
                    time.sleep(0.5)
                except Exception:
                    continue
        except Exception as e:
            print(f"    Error: {e}")

    print(f"  Elefant total: {len(deals)}")
    return deals


def scrape_evomag():
    """Scrape evoMAG products."""
    print("\n=== Scraping evoMAG.ro ===")
    deals = []
    categories = [
        ("laptopuri", "https://www.evomag.ro/portabile-laptopuri-notebook/"),
        ("telefoane", "https://www.evomag.ro/telefoane-tablete-702-702-smartphone/"),
        ("monitoare", "https://www.evomag.ro/monitoare-monitoare-led/"),
    ]

    for cat_name, cat_url in categories:
        print(f"  Categorie: {cat_name}")
        try:
            r = requests.get(cat_url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                print(f"    HTTP {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            items = soup.select(".nice_product_item")
            print(f"    {len(items)} product items")

            # evoMAG cards have title, image, price but no old price in listing
            # We need to fetch product pages for old price
            for item in items[:8]:
                try:
                    link_el = item.select_one("a[href][title]")
                    if not link_el:
                        continue
                    title = link_el.get("title", "").strip()
                    href = link_el.get("href", "")
                    if href.startswith("/"):
                        href = "https://www.evomag.ro" + href

                    # Get image from listing
                    img_el = item.select_one("img[src*='static']")
                    img_url = img_el.get("src", "") if img_el else ""

                    # Get price from listing
                    price_el = item.select_one(".real_price, .npi_price")
                    if not price_el:
                        continue
                    price_new = extract_price(price_el.get_text())
                    if price_new <= 0:
                        continue

                    # Fetch product page for old price
                    pr = requests.get(href, headers=HEADERS, timeout=10)
                    ps = BeautifulSoup(pr.text, "html.parser")

                    # Look for old/original price on product page
                    old_el = ps.select_one('[class*="old_price"], [class*="oldprice"], del, s')
                    if not old_el:
                        # Try promozone prices
                        promos = ps.select('[class*="promozone_price"]')
                        if len(promos) >= 2:
                            prices = [extract_price(p.get_text()) for p in promos]
                            prices = [p for p in prices if p > 0]
                            if prices:
                                price_old = max(prices)
                                if price_old > price_new:
                                    old_el = True  # flag

                    if old_el and not isinstance(old_el, bool):
                        price_old = extract_price(old_el.get_text())
                    elif not isinstance(old_el, bool):
                        continue

                    if price_old <= price_new:
                        continue

                    discount = round((price_old - price_new) / price_old * 100)
                    if discount < 10:
                        continue

                    deal_id = f"evomag-{hashlib.md5(href.encode()).hexdigest()[:8]}"
                    deals.append({
                        "id": deal_id,
                        "slug": slugify(title),
                        "magazin": "evomag",
                        "titlu": title[:150],
                        "pret_original": price_old,
                        "pret_redus": price_new,
                        "procent_reducere": discount,
                        "imagine_url": img_url,
                        "product_url": href,
                        "link_afiliat": "",
                        "categorie": cat_name,
                        "data_adaugare": "2026-04-04",
                        "activ": True,
                    })
                    print(f"    + {title[:50]} ({discount}% off)")
                    time.sleep(0.5)
                except Exception:
                    continue
        except Exception as e:
            print(f"    Error: {e}")

    print(f"  evoMAG total: {len(deals)}")
    return deals


def main():
    # Scrape stores
    elefant_deals = scrape_elefant()
    evomag_deals = scrape_evomag()

    new_deals = elefant_deals + evomag_deals

    if not new_deals:
        print("\nNo new deals scraped. Exiting.")
        return

    # Generate Profitshare links
    print(f"\n=== Generating Profitshare links for {len(new_deals)} deals ===")
    links_to_gen = [{"name": d["id"], "url": d["product_url"]} for d in new_deals]
    ps_map = generate_ps_links(links_to_gen)

    for d in new_deals:
        if d["id"] in ps_map:
            d["link_afiliat"] = ps_map[d["id"]]
        elif not d["link_afiliat"]:
            d["link_afiliat"] = d["product_url"]

    # Filter: must have image
    new_deals = [d for d in new_deals if d.get("imagine_url")]

    # Merge into deals.json
    deals_path = ROOT / "data" / "deals.json"
    existing = json.loads(deals_path.read_text(encoding="utf-8"))

    # Keep existing non-scraped deals (eMAG stays)
    prefixes_to_replace = ("elefant-", "evomag-")
    kept = [d for d in existing if not any(d["id"].startswith(p) for p in prefixes_to_replace)]
    final = kept + new_deals
    final.sort(key=lambda d: d.get("procent_reducere", 0), reverse=True)

    deals_path.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")

    # Summary
    stores = {}
    for d in final:
        s = d["magazin"]
        stores[s] = stores.get(s, 0) + 1

    print(f"\n{'='*50}")
    print(f"Total deals.json: {len(final)}")
    for s in sorted(stores):
        print(f"  {s}: {stores[s]}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
