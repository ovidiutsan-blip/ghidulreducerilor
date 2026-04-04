"""
Agent eMAG — Scraping dedicat produse eMAG.ro

Flux:
  1. Scrape categorii eMAG (pagini SSR, sortate dupa discount)
  2. Extrage date produse din carduri HTML
  3. Get og:image de pe pagina fiecarui produs
  4. Genereaza linkuri Profitshare via POST /affiliate-links/
  5. Salveaza in data/raw/emag_YYYY-MM-DD.json

Usage:
  python agents/agent_emag.py
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
from urllib.parse import urlencode

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
        logging.FileHandler(LOGS_DIR / "agent_emag.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("agent_emag")

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

# Load store config
with open(ROOT / "config" / "stores_config.json", "r", encoding="utf-8") as f:
    STORE_CONFIG = json.load(f)["emag"]


# ─── Helpers ─────────────────────────────────────────────────────────
def deal_id(url: str) -> str:
    return f"emag-{hashlib.md5(url.encode()).hexdigest()[:8]}"


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
        log.warning("Profitshare credentials lipsesc — linkurile nu vor fi generate")
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
                log.info(f"  PS batch {i // 20 + 1}: {len(batch)} linkuri -> {len(results)} generate")
            else:
                log.error(f"  PS API error {resp.status}: {resp.read().decode()[:200]}")
        except Exception as e:
            log.error(f"  PS eroare: {e}")
        finally:
            conn.close()

        if i + 20 < len(links_data):
            time.sleep(0.5)

    return all_results


# ─── og:image fetcher ────────────────────────────────────────────────
def get_og_image(product_url: str) -> str:
    """Extrage og:image de pe pagina de produs."""
    try:
        resp = session.get(product_url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        og = soup.select_one('meta[property="og:image"]')
        if og:
            img = og.get("content", "")
            if img.startswith("//"):
                img = "https:" + img
            return img
    except Exception as e:
        log.debug(f"  og:image error for {product_url[:50]}: {e}")
    return ""


# ─── Card image fallback ────────────────────────────────────────────
def get_card_image(card) -> str:
    """Extrage imagine din cardul de produs eMAG."""
    for selector in ["img[src*='emagst']", "img[data-src*='emagst']", "img.lozad", "img.product-image"]:
        img_el = card.select_one(selector)
        if img_el:
            img_url = img_el.get("src") or img_el.get("data-src") or img_el.get("data-original") or ""
            if img_url and not img_url.startswith("http"):
                img_url = "https:" + img_url if img_url.startswith("//") else ""
            if img_url and "placeholder" not in img_url and "data:image" not in img_url:
                return img_url
    return ""


# ─── eMAG Scraper ────────────────────────────────────────────────────
def scrape_emag() -> list:
    """Scrape produse reale din categoriile eMAG (SSR)."""
    log.info("=== Agent eMAG: Scraping produse ===")
    categories = STORE_CONFIG["categories"]
    max_per_cat = STORE_CONFIG.get("max_products_per_category", 6)
    max_pages = STORE_CONFIG.get("max_pages", 2)
    min_discount = STORE_CONFIG.get("min_discount", 15)
    rate_limit = STORE_CONFIG.get("rate_limit_seconds", 0.5)
    today = datetime.now().strftime("%Y-%m-%d")

    all_deals = []

    for cat_info in categories:
        cat_name = cat_info["name"]
        cat_url = cat_info["url"]
        cat_deals = []
        log.info(f"  Categorie: {cat_name}")

        for page in range(1, max_pages + 1):
            url = f"{cat_url}&p={page}" if "?" in cat_url else f"{cat_url}?p={page}"
            try:
                resp = session.get(url, timeout=15)
                if resp.status_code != 200:
                    log.warning(f"    Pagina {page}: HTTP {resp.status_code}")
                    break

                soup = BeautifulSoup(resp.text, "html.parser")

                # Metoda 1: card-item cu data-name (SSR clasic)
                cards = soup.select(".card-item.card-standard")
                if not cards:
                    cards = soup.select("div.card-item, div[class*='card-item']")
                if not cards:
                    cards = soup.select("[data-name]")

                if not cards:
                    log.info(f"    Pagina {page}: 0 produse (skip)")
                    break

                for card in cards:
                    if len(cat_deals) >= max_per_cat:
                        break

                    deal = parse_emag_card(card, cat_name, today)
                    if deal and deal["procent_reducere"] >= min_discount:
                        cat_deals.append(deal)

                log.info(f"    Pagina {page}: {len(cards)} carduri, extras {len(cat_deals)} deals")
                time.sleep(rate_limit)

            except Exception as e:
                log.error(f"    Eroare {cat_name} p{page}: {e}")
                break

        all_deals.extend(cat_deals)

    log.info(f"  eMAG total: {len(all_deals)} produse cu reducere")
    return all_deals


def parse_emag_card(card, category: str, today: str) -> dict | None:
    """Parseaza un card de produs eMAG. Incearca ambele metode de extragere."""

    # ─── Metoda 1: data-name/data-url attributes (simplu, rapid) ────
    name = card.get("data-name", "")
    product_url = card.get("data-url", "")

    if name and product_url:
        # Pret din [data-product] JSON
        price = 0
        fav_btn = card.select_one("[data-product]")
        if fav_btn:
            try:
                pdata = json.loads(fav_btn.get("data-product", "{}"))
                price = float(pdata.get("price", 0))
            except Exception:
                pass

        # Discount din badge
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
            return None

        # Imagine: og:image de pe pagina de produs (testat, merge 100%)
        img = get_og_image(product_url)
        if not img:
            img = get_card_image(card)

        return {
            "id": deal_id(product_url),
            "slug": slugify(name),
            "magazin": "emag",
            "titlu": name[:150],
            "pret_original": old_price,
            "pret_redus": price,
            "procent_reducere": discount,
            "imagine_url": img,
            "product_url": product_url,
            "link_afiliat": "",  # se completeaza cu Profitshare
            "categorie": category,
            "data_adaugare": today,
            "activ": True,
        }

    # ─── Metoda 2: selectori CSS (mai robust) ────────────────────────
    title_el = card.select_one("a.card-v2-title, [data-name], a[title]")
    if not title_el:
        return None
    title = title_el.get("title") or title_el.get("data-name") or title_el.get_text(strip=True)
    if not title or len(title) < 5:
        return None

    link_el = card.select_one("a.card-v2-title, a[href*='/pd/'], a.product-title")
    if not link_el or not link_el.get("href"):
        return None
    product_url = link_el["href"]
    if product_url.startswith("/"):
        product_url = "https://www.emag.ro" + product_url

    # Imagine din card
    img_url = get_card_image(card)

    # Preturi
    price_new = 0
    price_old = 0

    price_el = card.select_one(".product-new-price, .price .money-int, [class*='new-price']")
    if price_el:
        price_new = extract_price(price_el.get_text(strip=True))

    old_price_el = card.select_one(".product-old-price, [class*='old-price'], s")
    if old_price_el:
        price_old = extract_price(old_price_el.get_text(strip=True))

    if price_new <= 0 or price_old <= price_new:
        return None

    disc = discount_pct(price_old, price_new)
    if disc < 10:
        return None

    # og:image (mai bun decat card image)
    og_img = get_og_image(product_url)
    if og_img:
        img_url = og_img

    return {
        "id": deal_id(product_url),
        "slug": slugify(title),
        "magazin": "emag",
        "titlu": title[:150],
        "pret_original": price_old,
        "pret_redus": price_new,
        "procent_reducere": disc,
        "imagine_url": img_url,
        "product_url": product_url,
        "link_afiliat": "",
        "categorie": category,
        "data_adaugare": datetime.now().strftime("%Y-%m-%d"),
        "activ": True,
    }


# ─── Main ─────────────────────────────────────────────────────────
def run() -> list:
    """Punct de intrare — ruleaza agent eMAG complet."""
    today = datetime.now().strftime("%Y-%m-%d")
    log.info(f"Agent eMAG — Start — {today}")
    start = time.time()

    # Step 1: Scrape produse
    deals = scrape_emag()

    if not deals:
        log.warning("Niciun produs scraped. Se pastreaza datele existente.")
        return []

    # Step 2: Genereaza linkuri Profitshare
    log.info(f"\n  Generare linkuri Profitshare pentru {len(deals)} produse...")
    links_to_gen = []
    for d in deals:
        if d["product_url"] and "profitshare" not in d["product_url"]:
            links_to_gen.append({"name": d["id"], "url": d["product_url"]})

    if links_to_gen:
        ps_map = generate_ps_links(links_to_gen)
        for d in deals:
            if d["id"] in ps_map:
                d["link_afiliat"] = ps_map[d["id"]]
            else:
                # Fallback: product URL direct (functioneaza dar fara tracking)
                d["link_afiliat"] = d["product_url"]
        log.info(f"  {len(ps_map)}/{len(links_to_gen)} linkuri Profitshare generate")
    else:
        for d in deals:
            d["link_afiliat"] = d["product_url"]

    # Step 3: Filtreaza produse fara imagine
    deals_with_img = [d for d in deals if d.get("imagine_url")]
    if len(deals_with_img) < len(deals):
        log.info(f"  {len(deals) - len(deals_with_img)} produse fara imagine (excluse)")
    deals = deals_with_img

    # Step 4: Salveaza raw output
    output_file = RAW_DIR / f"emag_{today}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)

    elapsed = round(time.time() - start, 1)
    log.info(f"Agent eMAG — Finalizat in {elapsed}s — {len(deals)} produse salvate in {output_file}")

    return deals


if __name__ == "__main__":
    run()
