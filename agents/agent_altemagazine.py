"""
Agent Alte Magazine — Scraping multi-store (FashionDays, Elefant, evoMAG + stub-uri 2Performant)

Flux:
  1. Citeste config/stores_config.json pentru magazinele active (non-eMAG)
  2. Scrape fiecare magazin cu scraper-ul dedicat
  3. Genereaza linkuri afiliate (Profitshare sau 2Performant)
  4. Salveaza in data/raw/altemagazine_YYYY-MM-DD.json

Usage:
  python agents/agent_altemagazine.py
"""

import hashlib
import hmac
import http.client
import json
import os
import re
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, quote

import requests
from bs4 import BeautifulSoup

# Setup
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
LOGS_DIR = ROOT / "logs"
RAW_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_DIR / "agent_altemagazine.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("agent_altemagazine")

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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
}

session = requests.Session()
session.headers.update(HEADERS)

# Load all store configs (exclude eMAG — handled by agent_emag)
with open(ROOT / "config" / "stores_config.json", "r", encoding="utf-8") as f:
    ALL_CONFIGS = json.load(f)

STORE_CONFIGS = {k: v for k, v in ALL_CONFIGS.items() if k != "emag" and k != "_doc"}


# ─── Helpers ─────────────────────────────────────────────────────────
def deal_id(magazin: str, url: str) -> str:
    return f"{magazin}-{hashlib.md5(url.encode()).hexdigest()[:8]}"


def slugify(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:80]


def extract_price(text: str) -> float:
    text = text.replace(".", "").replace(",", ".").replace("\xa0", "")
    match = re.search(r"(\d+\.?\d*)", text)
    return float(match.group(1)) if match else 0


def discount_pct(old: float, new: float) -> int:
    if old <= 0 or new >= old:
        return 0
    return round((old - new) / old * 100)


# ─── Profitshare link generation ─────────────────────────────────────
def generate_ps_links(links_data: list[dict]) -> dict:
    """Genereaza linkuri Profitshare in batch-uri de 20."""
    if not API_USER or not API_KEY:
        log.warning("Profitshare credentials lipsesc")
        return {}

    all_results = {}
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

        headers = {
            "Date": date, "X-PS-Client": API_USER,
            "X-PS-Accept": "json", "X-PS-Auth": auth,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        conn = http.client.HTTPSConnection("api.profitshare.ro", timeout=30)
        try:
            conn.request("POST", "/affiliate-links/?", body, headers)
            resp = conn.getresponse()
            if resp.status in (200, 201):
                results = json.loads(resp.read().decode("utf-8")).get("result", [])
                for r in results:
                    ps_url = r.get("ps_url", "").replace("http://profitshare.ro", "https://profitshare.ro")
                    if ps_url:
                        all_results[r["name"]] = ps_url
                log.info(f"  PS batch {i // 20 + 1}: {len(batch)} -> {len(results)} linkuri")
            else:
                log.error(f"  PS API error {resp.status}")
        except Exception as e:
            log.error(f"  PS eroare: {e}")
        finally:
            conn.close()

        if i + 20 < len(links_data):
            time.sleep(0.5)

    return all_results


# ─── 2Performant link generation ─────────────────────────────────────
def generate_2performant_link(product_url: str, config: dict) -> str:
    """Construieste link de afiliere 2Performant."""
    tp = config.get("twoperformant", {})
    campaign_id = tp.get("campaign_id", "")
    aff_code = tp.get("aff_code", "")

    if not campaign_id or not aff_code:
        return product_url

    encoded_url = quote(product_url, safe="")
    return f"https://event.2performant.com/events/click?ad_type=quicklink&aff_code={aff_code}&unique={campaign_id}&redirect_to={encoded_url}"


# ─── FashionDays Scraper ─────────────────────────────────────────────
def scrape_fashiondays(config: dict) -> list:
    """Scrape FashionDays.ro produse cu reducere."""
    log.info("  === Scraping FashionDays.ro ===")
    all_deals = []
    today = datetime.now().strftime("%Y-%m-%d")
    max_pages = config.get("max_pages", 2)
    min_discount = config.get("min_discount", 15)

    for cat_info in config["categories"]:
        cat_name = cat_info["name"]
        cat_url = cat_info["url"]
        log.info(f"    Categorie: {cat_name}")

        for page in range(1, max_pages + 1):
            url = f"{cat_url}?page={page}"
            try:
                resp = session.get(url, timeout=15)
                if resp.status_code != 200:
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select("[class*='product-card'], [class*='ProductCard'], article.product")
                if not cards:
                    break

                for card in cards:
                    try:
                        title_el = card.select_one("[class*='product-name'], [class*='title'], h3, h4")
                        if not title_el:
                            continue
                        title = title_el.get_text(strip=True)

                        link_el = card.select_one("a[href*='fashiondays.ro']") or card.select_one("a")
                        if not link_el or not link_el.get("href"):
                            continue
                        product_url = link_el["href"]
                        if product_url.startswith("/"):
                            product_url = "https://www.fashiondays.ro" + product_url

                        img_el = card.select_one("img[src*='http'], img[data-src*='http']")
                        img_url = ""
                        if img_el:
                            img_url = img_el.get("src") or img_el.get("data-src") or ""

                        # Extract prices
                        price_new = 0
                        price_old = 0
                        for el in card.select("[class*='price'], [class*='Price'], span"):
                            text = el.get_text(strip=True)
                            price = extract_price(text)
                            if price > 0:
                                if price_new == 0:
                                    price_new = price
                                elif price > price_new:
                                    price_old = price

                        if price_new <= 0 or price_old <= price_new:
                            continue

                        disc = discount_pct(price_old, price_new)
                        if disc < min_discount:
                            continue

                        all_deals.append({
                            "id": deal_id("fashiondays", product_url),
                            "slug": slugify(title),
                            "magazin": "fashiondays",
                            "titlu": title[:150],
                            "pret_original": price_old,
                            "pret_redus": price_new,
                            "procent_reducere": disc,
                            "imagine_url": img_url,
                            "product_url": product_url,
                            "link_afiliat": "",
                            "categorie": cat_name,
                            "data_adaugare": today,
                            "activ": True,
                        })
                    except Exception:
                        continue

                log.info(f"      Pagina {page}: {len(cards)} carduri")
                time.sleep(config.get("rate_limit_seconds", 1.0))
            except Exception as e:
                log.error(f"      Eroare {cat_name}: {e}")
                break

    log.info(f"    FashionDays total: {len(all_deals)} produse")
    return all_deals


# ─── Elefant Scraper ─────────────────────────────────────────────────
def scrape_elefant(config: dict) -> list:
    """Scrape Elefant.ro produse cu reducere."""
    log.info("  === Scraping Elefant.ro ===")
    all_deals = []
    today = datetime.now().strftime("%Y-%m-%d")
    max_pages = config.get("max_pages", 2)
    min_discount = config.get("min_discount", 15)

    for cat_info in config["categories"]:
        cat_name = cat_info["name"]
        cat_url = cat_info["url"]
        log.info(f"    Categorie: {cat_name}")

        for page in range(1, max_pages + 1):
            url = f"{cat_url}?p={page}"
            try:
                resp = session.get(url, timeout=15)
                if resp.status_code != 200:
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select(".product-card, .product-item, [class*='ProductCard']")
                if not cards:
                    break

                for card in cards:
                    try:
                        title_el = card.select_one("a[title], .product-title, h3 a")
                        if not title_el:
                            continue
                        title = title_el.get("title") or title_el.get_text(strip=True)

                        link = title_el.get("href", "")
                        if link.startswith("/"):
                            link = "https://www.elefant.ro" + link

                        img_el = card.select_one("img[src*='http']")
                        img_url = img_el.get("src", "") if img_el else ""

                        prices = []
                        for p_el in card.select("[class*='price'], .money"):
                            val = extract_price(p_el.get_text(strip=True))
                            if val > 0:
                                prices.append(val)

                        if len(prices) < 2:
                            continue

                        price_new = min(prices)
                        price_old = max(prices)
                        disc = discount_pct(price_old, price_new)

                        if disc < min_discount or price_new <= 0:
                            continue

                        all_deals.append({
                            "id": deal_id("elefant", link),
                            "slug": slugify(title),
                            "magazin": "elefant",
                            "titlu": title[:150],
                            "pret_original": price_old,
                            "pret_redus": price_new,
                            "procent_reducere": disc,
                            "imagine_url": img_url,
                            "product_url": link,
                            "link_afiliat": "",
                            "categorie": cat_name,
                            "data_adaugare": today,
                            "activ": True,
                        })
                    except Exception:
                        continue

                log.info(f"      Pagina {page}: {len(cards)} carduri")
                time.sleep(config.get("rate_limit_seconds", 1.0))
            except Exception as e:
                log.error(f"      Eroare {cat_name}: {e}")
                break

    log.info(f"    Elefant total: {len(all_deals)} produse")
    return all_deals


# ─── evoMAG Scraper ──────────────────────────────────────────────────
def scrape_evomag(config: dict) -> list:
    """Scrape evoMAG.ro produse cu reducere."""
    log.info("  === Scraping evoMAG.ro ===")
    all_deals = []
    today = datetime.now().strftime("%Y-%m-%d")
    max_pages = config.get("max_pages", 2)
    min_discount = config.get("min_discount", 15)

    for cat_info in config["categories"]:
        cat_name = cat_info["name"]
        cat_url = cat_info["url"]
        log.info(f"    Categorie: {cat_name}")

        for page in range(1, max_pages + 1):
            url = f"{cat_url}?p={page}"
            try:
                resp = session.get(url, timeout=15)
                if resp.status_code != 200:
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select(".product_grid--item, .npi_product, [class*='product-card']")
                if not cards:
                    break

                for card in cards:
                    try:
                        title_el = card.select_one("a.npi_name, .product_grid--name a, a[title]")
                        if not title_el:
                            continue
                        title = title_el.get("title") or title_el.get_text(strip=True)

                        link = title_el.get("href", "")
                        if link.startswith("/"):
                            link = "https://www.evomag.ro" + link

                        img_el = card.select_one("img")
                        img_url = ""
                        if img_el:
                            img_url = (
                                img_el.get("src")
                                or img_el.get("data-src")
                                or img_el.get("data-original")
                                or ""
                            )
                            if img_url.startswith("//"):
                                img_url = "https:" + img_url
                            elif img_url.startswith("/"):
                                img_url = "https://www.evomag.ro" + img_url

                        # evoMAG foloseste <sup>XX</sup> pentru bani (ex: 432<sup>99</sup>)
                        # Inserez virgula inainte ca get_text() sa lipeasca cifrele.
                        for sup in card.find_all("sup"):
                            sup_text = sup.get_text(strip=True)
                            if sup_text.isdigit() and len(sup_text) <= 2:
                                sup.string = "," + sup_text

                        prices = []
                        # Selectori stricti pt evoMAG, evit <sup> orfane
                        for p_el in card.select(".product_pret, .npi_pret, .price, .pret, [class*='product_pret']"):
                            val = extract_price(p_el.get_text(strip=True))
                            if val >= 1:  # ignor fragmente sub 1 leu
                                prices.append(val)

                        if len(prices) < 2:
                            continue

                        price_new = min(prices)
                        price_old = max(prices)
                        # Sanity: daca price_new e sub 1/5 din price_old, skip (probabil parsing greșit)
                        if price_new * 5 < price_old:
                            continue
                        disc = discount_pct(price_old, price_new)

                        if disc < min_discount or price_new <= 0:
                            continue

                        all_deals.append({
                            "id": deal_id("evomag", link),
                            "slug": slugify(title),
                            "magazin": "evomag",
                            "titlu": title[:150],
                            "pret_original": price_old,
                            "pret_redus": price_new,
                            "procent_reducere": disc,
                            "imagine_url": img_url,
                            "product_url": link,
                            "link_afiliat": "",
                            "categorie": cat_name,
                            "data_adaugare": today,
                            "activ": True,
                        })
                    except Exception:
                        continue

                log.info(f"      Pagina {page}: {len(cards)} carduri")
                time.sleep(config.get("rate_limit_seconds", 1.0))
            except Exception as e:
                log.error(f"      Eroare {cat_name}: {e}")
                break

    log.info(f"    evoMAG total: {len(all_deals)} produse")
    return all_deals


# ─── Generic store scraper (for 2Performant stores when approved) ────
def scrape_generic(store_slug: str, config: dict) -> list:
    """Scraper generic — foloseste selectorii din config."""
    log.info(f"  === Scraping {config['name']} (generic) ===")
    all_deals = []
    today = datetime.now().strftime("%Y-%m-%d")
    max_pages = config.get("max_pages", 1)
    min_discount = config.get("min_discount", 20)
    selectors = config.get("selectors", {})

    for cat_info in config["categories"]:
        cat_name = cat_info["name"]
        cat_url = cat_info["url"]
        log.info(f"    Categorie: {cat_name}")

        for page in range(1, max_pages + 1):
            url = f"{cat_url}{'&' if '?' in cat_url else '?'}page={page}"
            try:
                resp = session.get(url, timeout=15)
                if resp.status_code != 200:
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select(selectors.get("card", ".product-card"))
                if not cards:
                    break

                for card in cards:
                    try:
                        title_el = card.select_one(selectors.get("title", "h3, h4, a[title]"))
                        if not title_el:
                            continue
                        title = title_el.get("title") or title_el.get_text(strip=True)
                        if not title or len(title) < 5:
                            continue

                        link_el = card.select_one(selectors.get("product_link", "a"))
                        if not link_el or not link_el.get("href"):
                            continue
                        product_url = link_el["href"]
                        if product_url.startswith("/"):
                            product_url = config["base_url"] + product_url

                        img_el = card.select_one(selectors.get("image", "img[src*='http']"))
                        img_url = ""
                        if img_el:
                            img_url = img_el.get("src") or img_el.get("data-src") or ""

                        prices = []
                        for p_el in card.select(selectors.get("price_elements", "[class*='price']")):
                            val = extract_price(p_el.get_text(strip=True))
                            if val > 0:
                                prices.append(val)

                        if len(prices) < 2:
                            continue

                        price_new = min(prices)
                        price_old = max(prices)
                        disc = discount_pct(price_old, price_new)

                        if disc < min_discount or price_new <= 0:
                            continue

                        all_deals.append({
                            "id": deal_id(store_slug, product_url),
                            "slug": slugify(title),
                            "magazin": store_slug,
                            "titlu": title[:150],
                            "pret_original": price_old,
                            "pret_redus": price_new,
                            "procent_reducere": disc,
                            "imagine_url": img_url,
                            "product_url": product_url,
                            "link_afiliat": "",
                            "categorie": cat_name,
                            "data_adaugare": today,
                            "activ": True,
                        })
                    except Exception:
                        continue

                log.info(f"      Pagina {page}: {len(cards)} carduri")
                time.sleep(config.get("rate_limit_seconds", 2.0))
            except Exception as e:
                log.error(f"      Eroare {cat_name}: {e}")
                break

    log.info(f"    {config['name']} total: {len(all_deals)} produse")
    return all_deals


# ─── Store dispatcher ────────────────────────────────────────────────
# Toate magazinele sunt scraped prin scrape_generic (selectori din config)
# Scraperele dedicate (scrape_fashiondays/elefant/evomag) sunt pastrate doar pentru referinta.
STORE_SCRAPERS = {}


def scrape_store(store_slug: str, config: dict) -> list:
    """Dispatches to the correct scraper for a store."""
    if store_slug in STORE_SCRAPERS:
        return STORE_SCRAPERS[store_slug](config)
    else:
        return scrape_generic(store_slug, config)


# ─── Deduplicate ─────────────────────────────────────────────────────
def deduplicate(deals: list) -> list:
    seen = set()
    unique = []
    for d in deals:
        if d["id"] not in seen:
            seen.add(d["id"])
            unique.append(d)
    return unique


# ─── Main ─────────────────────────────────────────────────────────
def run() -> list:
    """Punct de intrare — ruleaza scraping pe toate magazinele non-eMAG."""
    today = datetime.now().strftime("%Y-%m-%d")
    log.info(f"Agent Alte Magazine — Start — {today}")
    start = time.time()

    all_deals = []

    # Step 1: Scrape fiecare magazin activ
    for store_slug, config in STORE_CONFIGS.items():
        status = config.get("status", "neaplicat")
        if status not in ("activ",):
            log.info(f"  Skip {config['name']}: status={status}")
            continue

        try:
            deals = scrape_store(store_slug, config)
            all_deals.extend(deals)
        except Exception as e:
            log.error(f"  Eroare la {config['name']}: {e}")

    # Deduplicate
    all_deals = deduplicate(all_deals)
    log.info(f"\n  Total produse unice (non-eMAG): {len(all_deals)}")

    if not all_deals:
        log.warning("Niciun produs scraped de la alte magazine.")
        return []

    # Step 2: Genereaza linkuri afiliate
    log.info(f"  Generare linkuri afiliate...")

    # Separa dupa retea
    ps_deals = []
    tp_deals = []
    for d in all_deals:
        store_config = STORE_CONFIGS.get(d["magazin"], {})
        network = store_config.get("affiliate_network", "profitshare")
        if network == "profitshare":
            ps_deals.append(d)
        elif network == "2performant":
            tp_deals.append(d)

    # Profitshare links (batch)
    if ps_deals:
        links_to_gen = []
        for d in ps_deals:
            if d["product_url"] and "profitshare" not in d["product_url"]:
                links_to_gen.append({"name": d["id"], "url": d["product_url"]})

        if links_to_gen:
            ps_map = generate_ps_links(links_to_gen)
            for d in ps_deals:
                if d["id"] in ps_map:
                    d["link_afiliat"] = ps_map[d["id"]]
                else:
                    d["link_afiliat"] = d["product_url"]
            log.info(f"  Profitshare: {len(ps_map)}/{len(links_to_gen)} linkuri generate")

    # 2Performant links (URL construction, no API needed)
    if tp_deals:
        for d in tp_deals:
            store_config = STORE_CONFIGS.get(d["magazin"], {})
            d["link_afiliat"] = generate_2performant_link(d["product_url"], store_config)
        log.info(f"  2Performant: {len(tp_deals)} linkuri construite")

    # Fallback: deals fara link afiliat primesc product_url
    for d in all_deals:
        if not d.get("link_afiliat"):
            d["link_afiliat"] = d.get("product_url", "")

    # Step 3: Filtreaza produse fara imagine
    deals_with_img = [d for d in all_deals if d.get("imagine_url")]
    if len(deals_with_img) < len(all_deals):
        log.info(f"  {len(all_deals) - len(deals_with_img)} produse fara imagine (excluse)")
    all_deals = deals_with_img

    # Step 4: Salveaza raw output
    output_file = RAW_DIR / f"altemagazine_{today}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_deals, f, ensure_ascii=False, indent=2)

    elapsed = round(time.time() - start, 1)
    log.info(f"Agent Alte Magazine — Finalizat in {elapsed}s — {len(all_deals)} produse")

    # Rezumat pe magazine
    stores = {}
    for d in all_deals:
        s = d["magazin"]
        stores[s] = stores.get(s, 0) + 1
    for s in sorted(stores):
        log.info(f"    {s}: {stores[s]} produse")

    return all_deals


if __name__ == "__main__":
    run()
