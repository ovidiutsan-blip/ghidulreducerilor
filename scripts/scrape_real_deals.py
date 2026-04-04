#!/usr/bin/env python3
"""
Scraper real de produse — extrage oferte cu reduceri de pe magazine românești.
Generează linkuri de afiliere Profitshare și salvează în data/deals.json.

Magazine suportate:
  - eMAG.ro (categorii promoții)
  - FashionDays.ro
  - Elefant.ro
  - evoMAG.ro

Usage:
  python scripts/scrape_real_deals.py
  python scripts/scrape_real_deals.py --max-pages 3
"""

import json
import hashlib
import hmac
import os
import sys
import time
import re
import logging
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, quote

import requests
from bs4 import BeautifulSoup

# Setup
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_DIR / "scrape_real.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("scrape_real")

# Load env
for env_file in [ROOT / ".env", ROOT / ".env.local"]:
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            eq = line.find("=")
            if eq > 0:
                k, v = line[:eq].strip(), line[eq + 1 :].strip()
                os.environ.setdefault(k, v)

API_USER = os.environ.get("PROFITSHARE_API_USER", "")
API_KEY = os.environ.get("PROFITSHARE_API_KEY", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
}


def deal_id(magazin: str, url: str) -> str:
    return f"{magazin}-{hashlib.md5(url.encode()).hexdigest()[:8]}"


def slugify(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:80]


def discount_pct(old: float, new: float) -> int:
    if old <= 0 or new >= old:
        return 0
    return round((old - new) / old * 100)


# ─── Profitshare link generation ─────────────────────────────────────
def ps_generate_links(product_urls: list[dict]) -> dict:
    """
    Generează linkuri Profitshare pentru o listă de URL-uri.
    Input: [{"name": "id", "url": "https://..."}, ...]
    Returns: {original_url: profitshare_url}
    """
    if not API_USER or not API_KEY:
        log.warning("Profitshare credentials lipsesc — linkurile nu vor fi generate")
        return {}

    result_map = {}
    batch_size = 20

    for i in range(0, len(product_urls), batch_size):
        batch = product_urls[i : i + batch_size]
        post_data = {}
        for j, item in enumerate(batch):
            post_data[f"{j}[name]"] = item["name"]
            post_data[f"{j}[url]"] = item["url"]

        body = urlencode(post_data)
        endpoint = "affiliate-links/"
        date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
        sig = f"POST{endpoint}?/{API_USER}{date}"
        auth = hmac.new(API_KEY.encode(), sig.encode(), hashlib.sha1).hexdigest()

        headers = {
            "Date": date,
            "X-PS-Client": API_USER,
            "X-PS-Accept": "json",
            "X-PS-Auth": auth,
            "Content-Type": "application/x-www-form-urlencoded",
        }

        try:
            resp = requests.post(
                f"https://api.profitshare.ro/{endpoint}?",
                data=body,
                headers=headers,
                timeout=30,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                results = data.get("result", [])
                if isinstance(results, list):
                    for r in results:
                        ps_url = r.get("ps_url", "").replace(
                            "http://profitshare.ro", "https://profitshare.ro"
                        )
                        if ps_url:
                            name = r.get("name", "")
                            orig = next(
                                (b["url"] for b in batch if b["name"] == name), None
                            )
                            if orig:
                                result_map[orig] = ps_url
                log.info(f"  PS batch {i // batch_size + 1}: {len(batch)} linkuri")
            else:
                log.error(f"  PS API error {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            log.error(f"  PS eroare: {e}")

        if i + batch_size < len(product_urls):
            time.sleep(0.5)

    return result_map


# ─── eMAG Scraper ────────────────────────────────────────────────────
EMAG_CATEGORIES = [
    ("electronice", "https://www.emag.ro/telefoane-mobile/c?ref=hp_menu_quick-nav_1_1&type=category"),
    ("laptopuri", "https://www.emag.ro/laptopuri/c?ref=hp_menu_quick-nav_1_2&type=category"),
    ("televizoare", "https://www.emag.ro/televizoare/c?ref=hp_menu_quick-nav_1_3&type=category"),
    ("electrocasnice", "https://www.emag.ro/masini-de-spalat-rufe/c"),
    ("ingrijire-personala", "https://www.emag.ro/aparate-de-ingrijire-personala/c"),
    ("gaming", "https://www.emag.ro/console-jocuri/c"),
    ("tablete", "https://www.emag.ro/tablete/c"),
    ("casti", "https://www.emag.ro/casti/c"),
    ("aparate-foto", "https://www.emag.ro/aparate-foto-dslr/c"),
    ("smartwatch", "https://www.emag.ro/smartwatch/c"),
]


def scrape_emag(max_pages: int = 2) -> list:
    """Scrape eMAG product listings."""
    log.info("=== Scraping eMAG.ro ===")
    all_deals = []

    for cat_name, cat_url in EMAG_CATEGORIES:
        log.info(f"  Categorie: {cat_name}")
        for page in range(1, max_pages + 1):
            url = f"{cat_url}&p={page}" if "?" in cat_url else f"{cat_url}?p={page}"
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code != 200:
                    log.warning(f"    Pagina {page}: HTTP {resp.status_code}")
                    break

                soup = BeautifulSoup(resp.text, "html.parser")

                # eMAG card products
                cards = soup.select("div.card-item, div.card-standard, div[class*='card-item']")
                if not cards:
                    # Try alternate selectors
                    cards = soup.select("[data-name]")

                if not cards:
                    log.info(f"    Pagina {page}: 0 produse (skip)")
                    break

                for card in cards:
                    try:
                        deal = parse_emag_card(card, cat_name)
                        if deal and deal["pret_redus"] > 0 and deal["procent_reducere"] >= 10:
                            all_deals.append(deal)
                    except Exception as e:
                        continue

                log.info(f"    Pagina {page}: {len(cards)} carduri, total: {len(all_deals)}")
                time.sleep(1)

            except Exception as e:
                log.error(f"    Eroare {cat_name} p{page}: {e}")
                break

    log.info(f"  eMAG total: {len(all_deals)} produse cu reducere")
    return all_deals


def parse_emag_card(card, category: str) -> dict | None:
    """Parsează un card de produs eMAG."""
    # Titlu
    title_el = card.select_one("a.card-v2-title, [data-name], a[title]")
    if not title_el:
        return None
    title = title_el.get("title") or title_el.get("data-name") or title_el.get_text(strip=True)
    if not title or len(title) < 5:
        return None

    # URL produs
    link_el = card.select_one("a.card-v2-title, a[href*='/pd/'], a.product-title")
    if not link_el or not link_el.get("href"):
        return None
    product_url = link_el["href"]
    if product_url.startswith("/"):
        product_url = "https://www.emag.ro" + product_url

    # Imagine
    img_el = card.select_one("img[src*='emagst'], img[data-src*='emagst'], img.lozad, img.product-image")
    img_url = ""
    if img_el:
        img_url = img_el.get("src") or img_el.get("data-src") or img_el.get("data-original") or ""
        if img_url and not img_url.startswith("http"):
            img_url = "https:" + img_url if img_url.startswith("//") else ""
        # Skip placeholder images
        if "placeholder" in img_url or "data:image" in img_url:
            img_url = ""

    # Prețuri
    price_new = 0
    price_old = 0

    # Preț nou
    price_el = card.select_one(".product-new-price, .price .money-int, [class*='new-price']")
    if price_el:
        price_text = price_el.get_text(strip=True)
        price_new = extract_price(price_text)

    # Preț vechi
    old_price_el = card.select_one(".product-old-price, [class*='old-price'], .rrp-lbl + span, s")
    if old_price_el:
        old_text = old_price_el.get_text(strip=True)
        price_old = extract_price(old_text)

    if price_new <= 0:
        return None

    # Dacă nu avem preț vechi, skip (nu e reducere)
    if price_old <= price_new:
        return None

    disc = discount_pct(price_old, price_new)
    if disc < 10:
        return None

    return {
        "id": deal_id("emag", product_url),
        "slug": slugify(title),
        "magazin": "emag",
        "titlu": title[:150],
        "pret_original": price_old,
        "pret_redus": price_new,
        "procent_reducere": disc,
        "imagine_url": img_url,
        "product_url": product_url,
        "link_afiliat": "",  # filled later by Profitshare
        "categorie": category,
        "data_adaugare": datetime.now().strftime("%Y-%m-%d"),
        "activ": True,
    }


# ─── FashionDays Scraper ─────────────────────────────────────────────
FASHIONDAYS_CATEGORIES = [
    ("femei-imbracaminte", "https://www.fashiondays.ro/t/femei-imbracaminte/"),
    ("femei-incaltaminte", "https://www.fashiondays.ro/t/femei-incaltaminte/"),
    ("barbati-imbracaminte", "https://www.fashiondays.ro/t/barbati-imbracaminte/"),
    ("barbati-incaltaminte", "https://www.fashiondays.ro/t/barbati-incaltaminte/"),
]


def scrape_fashiondays(max_pages: int = 2) -> list:
    """Scrape FashionDays product listings."""
    log.info("=== Scraping FashionDays.ro ===")
    all_deals = []

    for cat_name, cat_url in FASHIONDAYS_CATEGORIES:
        log.info(f"  Categorie: {cat_name}")
        for page in range(1, max_pages + 1):
            url = f"{cat_url}?page={page}"
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code != 200:
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.select("[class*='product-card'], [class*='ProductCard'], article.product")

                if not cards:
                    break

                for card in cards:
                    try:
                        deal = parse_fashiondays_card(card, cat_name)
                        if deal and deal["pret_redus"] > 0 and deal["procent_reducere"] >= 15:
                            all_deals.append(deal)
                    except:
                        continue

                log.info(f"    Pagina {page}: {len(cards)} carduri")
                time.sleep(1)
            except Exception as e:
                log.error(f"    Eroare {cat_name}: {e}")
                break

    log.info(f"  FashionDays total: {len(all_deals)} produse cu reducere")
    return all_deals


def parse_fashiondays_card(card, category: str) -> dict | None:
    """Parsează un card de produs FashionDays."""
    title_el = card.select_one("[class*='product-name'], [class*='title'], h3, h4")
    if not title_el:
        return None
    title = title_el.get_text(strip=True)

    link_el = card.select_one("a[href*='fashiondays.ro']") or card.select_one("a")
    if not link_el or not link_el.get("href"):
        return None
    product_url = link_el["href"]
    if product_url.startswith("/"):
        product_url = "https://www.fashiondays.ro" + product_url

    img_el = card.select_one("img[src*='http'], img[data-src*='http']")
    img_url = ""
    if img_el:
        img_url = img_el.get("src") or img_el.get("data-src") or ""

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
        return None

    disc = discount_pct(price_old, price_new)
    if disc < 15:
        return None

    return {
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
        "categorie": category,
        "data_adaugare": datetime.now().strftime("%Y-%m-%d"),
        "activ": True,
    }


# ─── Elefant.ro Scraper ──────────────────────────────────────────────
ELEFANT_CATEGORIES = [
    ("carti", "https://www.elefant.ro/carti/reduceri"),
    ("electronice", "https://www.elefant.ro/electronice-si-it/reduceri"),
    ("jucarii", "https://www.elefant.ro/jucarii-si-jocuri/reduceri"),
]


def scrape_elefant(max_pages: int = 2) -> list:
    """Scrape Elefant.ro product listings."""
    log.info("=== Scraping Elefant.ro ===")
    all_deals = []

    for cat_name, cat_url in ELEFANT_CATEGORIES:
        log.info(f"  Categorie: {cat_name}")
        for page in range(1, max_pages + 1):
            url = f"{cat_url}?p={page}"
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
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

                        if disc < 15 or price_new <= 0:
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
                            "data_adaugare": datetime.now().strftime("%Y-%m-%d"),
                            "activ": True,
                        })
                    except:
                        continue

                log.info(f"    Pagina {page}: {len(cards)} carduri")
                time.sleep(1)
            except Exception as e:
                log.error(f"    Eroare {cat_name}: {e}")
                break

    log.info(f"  Elefant total: {len(all_deals)} produse")
    return all_deals


# ─── evoMAG Scraper ───────────────────────────────────────────────────
EVOMAG_CATEGORIES = [
    ("telefoane", "https://www.evomag.ro/telefoane-mobile-smartphone/filtru/stare-produs-nou,oferta-da/"),
    ("laptopuri", "https://www.evomag.ro/componente-laptop-notebook/filtru/stare-produs-nou,oferta-da/"),
    ("televizoare", "https://www.evomag.ro/tv-audio-video-televizoare/filtru/stare-produs-nou,oferta-da/"),
]


def scrape_evomag(max_pages: int = 2) -> list:
    """Scrape evoMAG product listings."""
    log.info("=== Scraping evoMAG.ro ===")
    all_deals = []

    for cat_name, cat_url in EVOMAG_CATEGORIES:
        log.info(f"  Categorie: {cat_name}")
        for page in range(1, max_pages + 1):
            url = f"{cat_url}?p={page}"
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
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

                        img_el = card.select_one("img[src*='http']")
                        img_url = img_el.get("src", "") if img_el else ""

                        prices = []
                        for p_el in card.select("[class*='price'], .money, .pret"):
                            val = extract_price(p_el.get_text(strip=True))
                            if val > 0:
                                prices.append(val)

                        if len(prices) < 2:
                            continue

                        price_new = min(prices)
                        price_old = max(prices)
                        disc = discount_pct(price_old, price_new)

                        if disc < 15 or price_new <= 0:
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
                            "data_adaugare": datetime.now().strftime("%Y-%m-%d"),
                            "activ": True,
                        })
                    except:
                        continue

                log.info(f"    Pagina {page}: {len(cards)} carduri")
                time.sleep(1)
            except Exception as e:
                log.error(f"    Eroare {cat_name}: {e}")
                break

    log.info(f"  evoMAG total: {len(all_deals)} produse")
    return all_deals


# ─── Helpers ──────────────────────────────────────────────────────────
def extract_price(text: str) -> float:
    """Extrage preț numeric din text."""
    text = text.replace(".", "").replace(",", ".").replace("\xa0", "")
    match = re.search(r"(\d+\.?\d*)", text)
    if match:
        return float(match.group(1))
    return 0


def deduplicate(deals: list) -> list:
    """Deduplică după ID."""
    seen = set()
    unique = []
    for d in deals:
        if d["id"] not in seen:
            seen.add(d["id"])
            unique.append(d)
    return unique


# ─── Main ─────────────────────────────────────────────────────────────
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Scraper real multi-magazin")
    parser.add_argument("--max-pages", type=int, default=2, help="Pagini per categorie")
    parser.add_argument("--skip-links", action="store_true", help="Skip Profitshare link generation")
    args = parser.parse_args()

    log.info("🚀 Scraper Real — Multi-magazin")
    log.info(f"   Max pagini: {args.max_pages}")
    start = time.time()

    # Scrape all stores
    new_deals = []
    new_deals.extend(scrape_emag(args.max_pages))
    new_deals.extend(scrape_fashiondays(args.max_pages))
    new_deals.extend(scrape_elefant(args.max_pages))
    new_deals.extend(scrape_evomag(args.max_pages))

    # Deduplicate
    new_deals = deduplicate(new_deals)
    log.info(f"\n📊 Total produse unice: {len(new_deals)}")

    # Generate Profitshare affiliate links
    if not args.skip_links and new_deals:
        log.info("\n🔗 Generare linkuri Profitshare...")
        links_to_gen = []
        for d in new_deals:
            if d["product_url"] and "profitshare" not in d["product_url"]:
                links_to_gen.append({"name": d["id"], "url": d["product_url"]})

        if links_to_gen:
            link_map = ps_generate_links(links_to_gen)
            for d in new_deals:
                ps_url = link_map.get(d["product_url"], "")
                if ps_url:
                    d["link_afiliat"] = ps_url
                else:
                    # Fallback: use product URL directly (will work but no tracking)
                    d["link_afiliat"] = d["product_url"]
            log.info(f"   ✅ {len(link_map)} linkuri Profitshare generate")
        else:
            log.info("   Niciun link de generat")
    else:
        for d in new_deals:
            d["link_afiliat"] = d["product_url"]

    # Filter: must have image
    with_images = [d for d in new_deals if d.get("imagine_url")]
    without_images = len(new_deals) - len(with_images)
    if without_images:
        log.info(f"   ⚠️  {without_images} produse fără imagine (excluse)")

    # Load existing deals, keep non-scraped ones
    deals_path = DATA_DIR / "deals.json"
    existing = []
    if deals_path.exists():
        existing = json.loads(deals_path.read_text(encoding="utf-8"))

    # Keep manually added deals, replace scraped ones
    manual_deals = [d for d in existing if not any(
        d["id"].startswith(p) for p in ["emag-", "fashiondays-", "elefant-", "evomag-", "ps-", "feed-"]
    )]

    # Merge
    final = manual_deals + with_images

    # Sort by discount descending
    final.sort(key=lambda d: d.get("procent_reducere", 0), reverse=True)

    # Save
    deals_path.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")

    elapsed = round(time.time() - start, 1)
    log.info(f"\n{'─' * 50}")
    log.info(f"✅ Scraping finalizat în {elapsed}s")
    log.info(f"   📦 Produse noi scraped: {len(with_images)}")
    log.info(f"   📁 Total deals.json: {len(final)}")
    log.info(f"   🏪 Magazine: eMAG, FashionDays, Elefant, evoMAG")
    log.info(f"{'─' * 50}")


if __name__ == "__main__":
    main()
