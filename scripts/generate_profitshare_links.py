"""
Generare linkuri de afiliere Profitshare prin API
==================================================
Citește deals.json și codes.json, generează link-uri de tracking
prin Profitshare API (POST /affiliate-links/), apoi actualizează fișierele.

Necesită variabile de mediu:
  PROFITSHARE_API_USER  — din dashboard Profitshare > Setări cont
  PROFITSHARE_API_KEY   — tot de acolo

Magazinele pe Profitshare: emag, fashion-days, vexio, libris, fornello, forit, pcgarage
"""

import json
import hmac
import hashlib
import os
import sys
import time
from datetime import datetime
from urllib.parse import urlencode, quote
import http.client

# --- Config ---
API_HOST = "api.profitshare.ro"
API_USER = os.environ.get("PROFITSHARE_API_USER", "")
API_KEY = os.environ.get("PROFITSHARE_API_KEY", "")

# Magazine pe Profitshare (restul sunt pe 2Performant)
PROFITSHARE_STORES = {"emag", "fashion-days", "vexio", "libris", "fornello", "forit", "pcgarage"}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEALS_PATH = os.path.join(BASE_DIR, "data", "deals.json")
CODES_PATH = os.path.join(BASE_DIR, "data", "codes.json")


def make_auth_header(method: str, endpoint: str, query_string: str = "") -> dict:
    """Construiește headerele de autentificare Profitshare"""
    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

    signature_string = f"{method}{endpoint}?{query_string}/{API_USER}{date}"
    auth = hmac.new(
        API_KEY.encode("utf-8"),
        signature_string.encode("utf-8"),
        hashlib.sha1
    ).hexdigest()

    return {
        "Date": date,
        "X-PS-Client": API_USER,
        "X-PS-Accept": "json",
        "X-PS-Auth": auth,
        "Content-Type": "application/x-www-form-urlencoded",
    }


def generate_links(links_data: list[dict]) -> list[dict]:
    """
    Trimite linkuri spre Profitshare API și returnează linkurile de tracking.

    links_data: [{"name": "...", "url": "..."}, ...]
    returns: [{"name": "...", "url": "...", "ps_url": "https://profitshare.ro/l/XXXXX"}, ...]
    """
    # Profitshare API acceptă batch-uri de linkuri
    # Format POST body: 0[name]=X&0[url]=Y&1[name]=Z&1[url]=W
    post_data = {}
    for i, link in enumerate(links_data):
        post_data[f"{i}[name]"] = link["name"]
        post_data[f"{i}[url]"] = link["url"]

    body = urlencode(post_data)
    endpoint = "affiliate-links/"
    headers = make_auth_header("POST", endpoint, "")

    conn = http.client.HTTPSConnection(API_HOST, timeout=30)
    try:
        conn.request("POST", f"/{endpoint}?", body, headers)
        response = conn.getresponse()

        if response.status not in (200, 201):
            print(f"  ❌ API error: {response.status} {response.reason}")
            resp_body = response.read().decode("utf-8")
            print(f"  Response: {resp_body[:500]}")
            return []

        data = json.loads(response.read().decode("utf-8"))
        return data.get("result", [])
    except Exception as e:
        print(f"  ❌ Connection error: {e}")
        return []
    finally:
        conn.close()


def process_deals():
    """Procesează deals.json — generează linkuri Profitshare pentru magazinele eligibile"""
    with open(DEALS_PATH, "r", encoding="utf-8") as f:
        deals = json.load(f)

    # Filtrare doar magazine Profitshare
    ps_deals = [d for d in deals if d["magazin"] in PROFITSHARE_STORES and d["activ"]]

    if not ps_deals:
        print("Nu sunt dealuri active pe Profitshare.")
        return

    print(f"\n📦 Generare linkuri pentru {len(ps_deals)} dealuri...")

    # Trimite in batch-uri de 20 (API limit)
    batch_size = 20
    for batch_start in range(0, len(ps_deals), batch_size):
        batch = ps_deals[batch_start:batch_start + batch_size]

        links_data = []
        for deal in batch:
            # Folosim URL-ul curent (search URL pe magazin) ca destinație
            links_data.append({
                "name": f"deal-{deal['id']}",
                "url": deal["link_afiliat"]
            })

        print(f"  Batch {batch_start // batch_size + 1}: {len(batch)} linkuri...")
        results = generate_links(links_data)

        if not results:
            print("  ⚠️  Nu s-au generat linkuri. Verifică credențialele API.")
            continue

        # Actualizare deals cu ps_url
        for result in results:
            deal_id = result["name"].replace("deal-", "")
            ps_url = result.get("ps_url", "")

            if ps_url:
                # Convertește http:// la https://
                ps_url = ps_url.replace("http://profitshare.ro", "https://profitshare.ro")

                for deal in deals:
                    if deal["id"] == deal_id:
                        deal["link_afiliat"] = ps_url
                        print(f"  ✅ {deal_id}: {ps_url}")
                        break

        # Scurt delay între batch-uri
        if batch_start + batch_size < len(ps_deals):
            time.sleep(1)

    # Salvare
    with open(DEALS_PATH, "w", encoding="utf-8") as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Salvat {DEALS_PATH}")


def process_codes():
    """Procesează codes.json — generează linkuri Profitshare pentru codurile promo"""
    with open(CODES_PATH, "r", encoding="utf-8") as f:
        codes = json.load(f)

    ps_codes = [c for c in codes if c["magazin"] in PROFITSHARE_STORES and c.get("activ", True)]

    if not ps_codes:
        print("Nu sunt coduri promo active pe Profitshare.")
        return

    print(f"\n🏷️  Generare linkuri pentru {len(ps_codes)} coduri promo...")

    links_data = []
    for code in ps_codes:
        links_data.append({
            "name": f"code-{code['id']}",
            "url": code["link_afiliat"]
        })

    results = generate_links(links_data)

    if not results:
        print("  ⚠️  Nu s-au generat linkuri. Verifică credențialele API.")
        return

    for result in results:
        code_id = result["name"].replace("code-", "")
        ps_url = result.get("ps_url", "")

        if ps_url:
            ps_url = ps_url.replace("http://profitshare.ro", "https://profitshare.ro")

            for code in codes:
                if code["id"] == code_id:
                    code["link_afiliat"] = ps_url
                    print(f"  ✅ {code_id}: {ps_url}")
                    break

    with open(CODES_PATH, "w", encoding="utf-8") as f:
        json.dump(codes, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Salvat {CODES_PATH}")


def test_connection():
    """Testează conexiunea la API cu un request GET simplu"""
    print("🔌 Test conexiune Profitshare API...")

    endpoint = "affiliate-advertisers/"
    headers = make_auth_header("GET", endpoint, "")

    conn = http.client.HTTPSConnection(API_HOST, timeout=15)
    try:
        conn.request("GET", f"/{endpoint}?", "", headers)
        response = conn.getresponse()

        if response.status == 200:
            data = json.loads(response.read().decode("utf-8"))
            advertisers = data.get("result", [])
            print(f"  ✅ Conectat! {len(advertisers)} advertiseri activi.")
            if isinstance(advertisers, list):
                for adv in advertisers[:5]:
                    print(f"     - {adv.get('name', 'N/A')} (ID: {adv.get('id', 'N/A')})")
            return True
        else:
            body = response.read().decode("utf-8")
            print(f"  ❌ Eroare {response.status}: {body[:300]}")
            return False
    except Exception as e:
        print(f"  ❌ Eroare conexiune: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    if not API_USER or not API_KEY:
        print("❌ Lipsesc credențialele Profitshare!")
        print()
        print("Setează variabilele de mediu:")
        print("  export PROFITSHARE_API_USER='contul_tau'")
        print("  export PROFITSHARE_API_KEY='cheia_ta_api'")
        print()
        print("Le găsești în dashboard-ul Profitshare > Setări cont > API")
        sys.exit(1)

    print(f"🚀 Profitshare Link Generator")
    print(f"   API User: {API_USER}")
    print(f"   API Key:  {API_KEY[:8]}...")
    print()

    if not test_connection():
        print("\n⚠️  Conexiunea a eșuat. Verifică credențialele.")
        sys.exit(1)

    process_deals()
    process_codes()

    print("\n✨ Gata! Linkurile au fost actualizate.")
    print("   Rulează 'git diff data/' pentru a vedea schimbările.")
