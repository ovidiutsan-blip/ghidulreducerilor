#!/usr/bin/env python3
"""
Scrape produse de la magazinele aprobate pe Profitshare, genereaza linkuri afiliate,
si merge in deals.json.

REGULA: Doar magazine aprobate pe Profitshare cu linkuri afiliate valide!
Magazine aprobate: eMAG (agent separat), FashionDays, Libris, Vexio, ForIT, Fornello, Watch24, ITGalaxy

Usage:
  python scripts/scrape_and_merge.py
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
    text = text.replace(".", "").replace(",", ".").replace("\xa0", "")
    text = re.sub(r"[a-zA-Z%]+", "", text).strip()
    m = re.search(r"(\d+\.?\d*)", text)
    return float(m.group(1)) if m else 0


def slugify(text):
    import unicodedata
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80]


def deal_id(store, url):
    return f"{store}-{hashlib.md5(url.encode()).hexdigest()[:8]}"


def generate_ps_links(links_data):
    """Generate Profitshare affiliate links in batches of 20."""
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
                print(f"  PS batch {i // 20 + 1}: {len(batch)} sent -> {len(ps_map)} total links")
            else:
                print(f"  PS API error: {resp.status}")
        except Exception as e:
            print(f"  PS error: {e}")
        finally:
            conn.close()
        time.sleep(0.3)

    return ps_map


# ─── WATCH24 SCRAPER ─────────────────────────────────────────────────
def scrape_watch24():
    """Scrape Watch24.ro promotions — SSR, data OK."""
    print("=== Scraping Watch24.ro ===")
    deals = []
    today = time.strftime("%Y-%m-%d")

    for page in range(1, 4):
        url = f"https://www.watch24.ro/promotii?page={page}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                break

            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("article.product-box")
            if not cards:
                break

            for card in cards:
                try:
                    # Title + link from JS data
                    script = card.select_one("script")
                    if script and script.string:
                        name_m = re.search(r"item_name:\s*'([^']+)'", script.string)
                        title = name_m.group(1) if name_m else ""
                    else:
                        title = ""

                    link_el = card.select_one("a[href*='watch24.ro']")
                    if not link_el:
                        continue
                    product_url = link_el.get("href", "")

                    if not title:
                        title_el = card.select_one("img[alt]")
                        title = title_el.get("alt", "") if title_el else ""

                    if not title or len(title) < 5:
                        continue

                    # Image
                    img_el = card.select_one("img[src*='cdn.watch24']")
                    img_url = img_el.get("src", "") if img_el else ""

                    # Price block: "500,00 lei199,00 lei-60%"
                    price_el = card.select_one(".price")
                    if not price_el:
                        continue

                    old_el = price_el.select_one("del, s, .price-old")
                    new_els = price_el.select("span")

                    price_old = 0
                    price_new = 0

                    if old_el:
                        price_old = extract_price(old_el.get_text())

                    # Get all price numbers from the block
                    all_prices = re.findall(r"(\d[\d.,]*)\s*lei", price_el.get_text())
                    if len(all_prices) >= 2:
                        p1 = extract_price(all_prices[0])
                        p2 = extract_price(all_prices[1])
                        price_old = max(p1, p2)
                        price_new = min(p1, p2)
                    elif len(all_prices) == 1:
                        price_new = extract_price(all_prices[0])

                    if price_new <= 0 or price_old <= price_new:
                        continue

                    discount = round((price_old - price_new) / price_old * 100)
                    if discount < 15:
                        continue

                    deals.append({
                        "id": deal_id("watch24", product_url),
                        "slug": slugify(title),
                        "magazin": "watch24",
                        "titlu": title[:150],
                        "pret_original": price_old,
                        "pret_redus": price_new,
                        "procent_reducere": discount,
                        "imagine_url": img_url,
                        "product_url": product_url,
                        "link_afiliat": "",
                        "categorie": "ceasuri",
                        "data_adaugare": today,
                        "activ": True,
                    })
                except Exception:
                    continue

            print(f"  Pagina {page}: {len(cards)} carduri, total {len(deals)} deals")
            time.sleep(0.5)
        except Exception as e:
            print(f"  Error page {page}: {e}")
            break

    print(f"  Watch24 total: {len(deals)}")
    return deals


# ─── FORIT SCRAPER ───────────────────────────────────────────────────
def scrape_forit():
    """Scrape ForIT.ro promotions."""
    print("\n=== Scraping ForIT.ro ===")
    deals = []
    today = time.strftime("%Y-%m-%d")

    url = "https://www.forit.ro/promotii/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")

        # ForIT uses similar OpenCart structure
        cards = soup.select("article.product-box, .product-layout, .product-thumb")
        if not cards:
            # Try broader
            cards = soup.select("[class*='product-box'], [class*='product-item']")

        for card in cards[:20]:
            try:
                link_el = card.select_one("a[href*='forit.ro']")
                if not link_el:
                    continue
                product_url = link_el.get("href", "")

                # Title
                title = ""
                script = card.select_one("script")
                if script and script.string:
                    name_m = re.search(r"item_name:\s*'([^']+)'", script.string)
                    if name_m:
                        title = name_m.group(1)

                if not title:
                    img_el = card.select_one("img[alt]")
                    title = img_el.get("alt", "") if img_el else ""

                if not title or len(title) < 5:
                    continue

                # Image
                img_el = card.select_one("img[src*='http']")
                img_url = img_el.get("src", "") if img_el else ""

                # Prices
                price_el = card.select_one("[class*='price']")
                if not price_el:
                    continue

                all_prices = re.findall(r"(\d[\d.,]*)\s*lei", price_el.get_text())
                if len(all_prices) < 2:
                    continue

                p1 = extract_price(all_prices[0])
                p2 = extract_price(all_prices[1])
                price_old = max(p1, p2)
                price_new = min(p1, p2)

                if price_new <= 0 or price_old <= price_new:
                    continue

                discount = round((price_old - price_new) / price_old * 100)
                if discount < 15:
                    continue

                deals.append({
                    "id": deal_id("forit", product_url),
                    "slug": slugify(title),
                    "magazin": "forit",
                    "titlu": title[:150],
                    "pret_original": price_old,
                    "pret_redus": price_new,
                    "procent_reducere": discount,
                    "imagine_url": img_url,
                    "product_url": product_url,
                    "link_afiliat": "",
                    "categorie": "electronice",
                    "data_adaugare": today,
                    "activ": True,
                })
            except Exception:
                continue

        print(f"  ForIT total: {len(deals)}")
    except Exception as e:
        print(f"  Error: {e}")

    return deals


# ─── FORNELLO SCRAPER ─────────────────────────────────────────────────
def scrape_fornello():
    """Scrape Fornello.ro promotions — SSR, Profitshare approved."""
    print("\n=== Scraping Fornello.ro ===")
    deals = []
    today = time.strftime("%Y-%m-%d")

    for page_url in ["https://www.fornello.ro/promotii/", "https://www.fornello.ro/"]:
        try:
            r = requests.get(page_url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(".p-product-card")

            for card in cards:
                try:
                    # Title from img alt or title element
                    img_el = card.select_one("img[alt]")
                    title = img_el.get("alt", "") if img_el else ""
                    if not title or len(title) < 5:
                        title_el = card.select_one("[class*='title'], [class*='name']")
                        title = title_el.get_text(strip=True) if title_el else ""
                    if not title or len(title) < 5:
                        continue

                    # Link
                    link_el = card.select_one("a[href]")
                    if not link_el:
                        continue
                    product_url = link_el.get("href", "")
                    if product_url.startswith("/"):
                        product_url = "https://www.fornello.ro" + product_url

                    # Image — get the promo image or product image
                    img_url = ""
                    for img_sel in ["img[src*='cs-photos/products']", "img[src*='cs-content']", "img[alt]"]:
                        ie = card.select_one(img_sel)
                        if ie:
                            img_url = ie.get("src", "")
                            if img_url:
                                break

                    # New price from .price-html
                    new_el = card.select_one(".price-html, .p-product-card__prices--final .price-html")
                    price_new = 0
                    if new_el:
                        price_new = extract_price(new_el.get_text())

                    # Old price from discount section
                    old_el = card.select_one(".p-product-card__prices--discount-price")
                    price_old = 0
                    if old_el:
                        price_old = extract_price(old_el.get_text())

                    if price_new <= 0:
                        continue

                    if price_old <= price_new:
                        price_old = price_new  # No discount, show at regular price

                    discount = 0
                    if price_old > price_new:
                        discount = round((price_old - price_new) / price_old * 100)

                    deals.append({
                        "id": deal_id("fornello", product_url),
                        "slug": slugify(title),
                        "magazin": "fornello",
                        "titlu": title[:150],
                        "pret_original": price_old,
                        "pret_redus": price_new,
                        "procent_reducere": discount,
                        "imagine_url": img_url,
                        "product_url": product_url,
                        "link_afiliat": "",
                        "categorie": "casa-gradina",
                        "data_adaugare": today,
                        "activ": True,
                    })
                except Exception:
                    continue

            print(f"  {page_url[-30:]}: {len(cards)} cards")
        except Exception as e:
            print(f"  Error: {e}")

    # Deduplicate
    seen = set()
    unique = []
    for d in deals:
        if d["id"] not in seen:
            seen.add(d["id"])
            unique.append(d)

    print(f"  Fornello total: {len(unique)}")
    return unique


def main():
    all_new = []

    # Scrape all Profitshare-approved stores with SSR pages
    all_new.extend(scrape_watch24())
    all_new.extend(scrape_forit())
    all_new.extend(scrape_fornello())

    if not all_new:
        print("\nNo new deals. Exiting.")
        return

    # Filter: must have image
    all_new = [d for d in all_new if d.get("imagine_url")]

    # Generate Profitshare links
    print(f"\n=== Generating Profitshare links for {len(all_new)} deals ===")
    links_to_gen = [{"name": d["id"], "url": d["product_url"]} for d in all_new]
    ps_map = generate_ps_links(links_to_gen)

    # CRITICAL: Only keep deals that got Profitshare links
    valid_deals = []
    for d in all_new:
        if d["id"] in ps_map:
            d["link_afiliat"] = ps_map[d["id"]]
            valid_deals.append(d)

    print(f"  {len(valid_deals)}/{len(all_new)} deals with valid Profitshare links")

    if not valid_deals:
        print("No deals with affiliate links. Exiting.")
        return

    # Merge into deals.json — keep eMAG deals, replace others
    deals_path = ROOT / "data" / "deals.json"
    existing = json.loads(deals_path.read_text(encoding="utf-8"))

    # Keep eMAG (from agent_emag), remove old scraped from other stores
    emag_deals = [d for d in existing if d["magazin"] == "emag"]

    final = emag_deals + valid_deals
    final.sort(key=lambda d: d.get("procent_reducere", 0), reverse=True)

    deals_path.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")

    # Summary
    stores = {}
    for d in final:
        s = d["magazin"]
        stores[s] = stores.get(s, 0) + 1

    print(f"\n{'=' * 50}")
    print(f"Total deals.json: {len(final)}")
    for s in sorted(stores):
        print(f"  {s}: {stores[s]}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
