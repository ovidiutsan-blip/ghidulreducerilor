"""
Processor Agent — Filtrează, deduplică și rankează ofertele
Citește din /data/raw/YYYY-MM-DD.json, scrie în /data/processed/YYYY-MM-DD.json
"""

import json
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Configurare filtrare
MIN_DISCOUNT_PERCENT = 20
MAX_PRICE = 50000  # RON — exclude produse nerezonabile
MIN_PRICE = 10     # RON — exclude articole prea ieftine
MAX_OFFERS_PER_STORE = 12
MAX_TOTAL_OFFERS = 50

# Ponderi scoring
WEIGHT_DISCOUNT = 0.4
WEIGHT_POPULARITY = 0.3
WEIGHT_COMMISSION = 0.3

# Comisioane medii estimate per magazin (pentru scoring)
STORE_COMMISSION = {
    "emag": 5,
    "fashion-days": 3,
    "fashiondays": 3,
    "vexio": 2,
    "libris": 8,
    "fornello": 2,
    "forit": 2,
    "elefant": 5,
    "evomag": 2,
    "notino": 8,
    "answear": 9,
    "decathlon": 4,
    "drmax": 6,
    "pcgarage": 1,
    "cel": 3,
}


def normalize_title(title):
    """Normalizează titlul pentru deduplicare."""
    title = title.lower().strip()
    title = re.sub(r"[^a-z0-9\s]", "", title)
    title = re.sub(r"\s+", " ", title)
    return title


def calculate_score(offer):
    """Calculează scorul unei oferte: (reducere% * 0.4) + (popularitate * 0.3) + (comision * 0.3)"""
    discount_score = min(offer["procent_reducere"] / 100, 1.0)

    # Popularitate estimată pe baza prețului (produsele cu preț mediu au cerere mai mare)
    price = offer["pret_redus"]
    if 100 <= price <= 2000:
        popularity_score = 0.8
    elif 50 <= price <= 5000:
        popularity_score = 0.5
    else:
        popularity_score = 0.3

    commission = STORE_COMMISSION.get(offer["magazin"], 5) / 20  # Normalizat la 0-1

    score = (
        discount_score * WEIGHT_DISCOUNT
        + popularity_score * WEIGHT_POPULARITY
        + commission * WEIGHT_COMMISSION
    )
    return round(score, 4)


def deduplicate(offers):
    """Elimină produse cu titluri foarte similare."""
    seen_titles = {}
    unique = []

    for offer in offers:
        normalized = normalize_title(offer["titlu"])
        # Verifică dacă un titlu similar există deja (primele 5 cuvinte)
        key_words = " ".join(normalized.split()[:5])
        if key_words in seen_titles:
            # Păstrează oferta cu reducere mai mare
            existing_idx = seen_titles[key_words]
            if offer["procent_reducere"] > unique[existing_idx]["procent_reducere"]:
                unique[existing_idx] = offer
            continue
        seen_titles[key_words] = len(unique)
        unique.append(offer)

    return unique


def filter_offers(offers):
    """Filtrează ofertele după criterii de calitate."""
    filtered = []
    for offer in offers:
        if offer["procent_reducere"] < MIN_DISCOUNT_PERCENT:
            continue
        if offer["pret_redus"] < MIN_PRICE or offer["pret_redus"] > MAX_PRICE:
            continue
        if not offer.get("titlu") or len(offer["titlu"]) < 5:
            continue
        if not offer.get("link_afiliat"):
            continue
        if not offer.get("activ", True):
            continue
        filtered.append(offer)
    return filtered


def rank_and_limit(offers):
    """Adaugă scor, sortează și limitează numărul de oferte."""
    for offer in offers:
        offer["_score"] = calculate_score(offer)

    # Sortare descrescătoare după scor
    offers.sort(key=lambda x: x["_score"], reverse=True)

    # Limitare per magazin
    store_counts = {}
    limited = []
    for offer in offers:
        store = offer["magazin"]
        store_counts[store] = store_counts.get(store, 0) + 1
        if store_counts[store] <= MAX_OFFERS_PER_STORE:
            limited.append(offer)

    # Limitare totală
    limited = limited[:MAX_TOTAL_OFFERS]

    # Elimină câmpul temporar _score
    for offer in limited:
        offer.pop("_score", None)

    return limited


def run():
    """Punct principal de intrare."""
    today = datetime.now().strftime("%Y-%m-%d")
    raw_file = RAW_DIR / f"{today}.json"
    output_file = PROCESSED_DIR / f"{today}.json"

    print(f"[PROCESSOR] Start — {today}")

    if not raw_file.exists():
        print(f"[PROCESSOR] Fișier raw inexistent: {raw_file}")
        # Fallback: caută cel mai recent raw file
        raw_files = sorted(RAW_DIR.glob("*.json"), reverse=True)
        if raw_files:
            raw_file = raw_files[0]
            print(f"[PROCESSOR] Folosesc ultimul raw disponibil: {raw_file}")
        else:
            print("[PROCESSOR] Nu există date raw. Oprire.")
            return []

    with open(raw_file, "r", encoding="utf-8") as f:
        raw_offers = json.load(f)

    print(f"[PROCESSOR] Oferte brute: {len(raw_offers)}")

    # Pipeline de procesare
    offers = filter_offers(raw_offers)
    print(f"[PROCESSOR] După filtrare: {len(offers)}")

    offers = deduplicate(offers)
    print(f"[PROCESSOR] După deduplicare: {len(offers)}")

    offers = rank_and_limit(offers)
    print(f"[PROCESSOR] Final (rankate + limitate): {len(offers)}")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)

    print(f"[PROCESSOR] Salvate în {output_file}")
    return offers


if __name__ == "__main__":
    run()
