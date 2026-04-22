#!/usr/bin/env python3
"""
Reconnaissance 2Performant API feed — verifica daca notino/drmax/answear au product feeds.

Status inițial: scraping-ul pentru notino/drmax/answear se face prin agent_altemagazine.py
(HTML scraping). Scopul acestui script este să verifice dacă 2Performant oferă un XML/JSON
product feed pentru acești 3 advertiseri — caz in care am putea înlocui scraping-ul cu un
API call mai stabil.

Usage:
  1. Obține cheie API de la 2Performant: https://app.2performant.com/users/settings/api
  2. Setează environment variables:
       TWO_PERFORMANT_API_USER=<email>
       TWO_PERFORMANT_API_KEY=<api-key>
  3. Rulează: python scripts/check_2performant_feed.py

Output: status per magazin (has_feed, feed_url, sample_products), salvat in _2p_feed_check.json
"""
import json
import os
import sys
from pathlib import Path

try:
    import requests  # type: ignore
except ImportError:
    print("ERROR: requests library required. Run: pip install requests")
    sys.exit(1)

# Campaign IDs extrași în task #22 — vezi config/affiliate_links.json pentru valori actuale
TARGET_ADVERTISERS = ['notino', 'drmax', 'answear']
API_BASE = 'https://api.2performant.com'


def check_advertiser(session, campaign_id: str, name: str) -> dict:
    """Verifica daca un advertiser are product feed disponibil."""
    result = {
        'name': name,
        'campaign_id': campaign_id,
        'has_feed': False,
        'feed_url': None,
        'sample_products': [],
        'error': None,
    }
    try:
        # Endpoint product-feeds pentru un campaign
        url = f"{API_BASE}/affiliate/campaigns/{campaign_id}/product_feeds"
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            feeds = data.get('product_feeds', []) or data.get('products', [])
            if feeds:
                result['has_feed'] = True
                result['feed_url'] = feeds[0].get('url') if isinstance(feeds[0], dict) else None
                result['sample_products'] = feeds[:3]
        elif resp.status_code == 404:
            result['error'] = 'No product feed endpoint (404)'
        else:
            result['error'] = f'HTTP {resp.status_code}: {resp.text[:200]}'
    except Exception as e:
        result['error'] = f'Exception: {e}'
    return result


def load_campaign_ids() -> dict:
    """Încarcă campaign_id-urile din config/affiliate_links.json"""
    cfg_path = Path(__file__).parent.parent / 'config' / 'affiliate_links.json'
    if not cfg_path.exists():
        return {}
    with open(cfg_path, encoding='utf-8') as f:
        cfg = json.load(f)
    ids = {}
    for name in TARGET_ADVERTISERS:
        ids[name] = cfg.get(name, {}).get('campaign_id', '')
    return ids


def main():
    user = os.environ.get('TWO_PERFORMANT_API_USER')
    key = os.environ.get('TWO_PERFORMANT_API_KEY')
    if not user or not key:
        print("ERROR: lipsesc env vars TWO_PERFORMANT_API_USER + TWO_PERFORMANT_API_KEY.")
        print("       Obtine API credentials de la https://app.2performant.com/users/settings/api")
        sys.exit(1)

    campaign_ids = load_campaign_ids()
    if not campaign_ids:
        print("ERROR: nu am găsit config/affiliate_links.json")
        sys.exit(1)

    session = requests.Session()
    session.headers.update({
        'Accept': 'application/json',
        'X-User-Email': user,
        'X-User-Token': key,
    })

    results = []
    for name, cid in campaign_ids.items():
        if not cid:
            print(f"[SKIP] {name}: no campaign_id in config")
            continue
        print(f"[CHECK] {name} (campaign {cid})...")
        r = check_advertiser(session, cid, name)
        print(f"   has_feed={r['has_feed']}  error={r['error']}")
        results.append(r)

    out = Path(__file__).parent.parent / '_2p_feed_check.json'
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'checked': results}, f, indent=2, ensure_ascii=False)
    print(f"\nOutput salvat la: {out}")

    with_feed = [r for r in results if r['has_feed']]
    if with_feed:
        print(f"\n✅ {len(with_feed)}/{len(results)} advertiseri au product feeds:")
        for r in with_feed:
            print(f"   - {r['name']}: {r['feed_url']}")
        print("\nNext: creează scripts/two_p_feed_to_deals.py pe modelul ps_feed_to_deals.py")
    else:
        print(f"\n⚠️  0/{len(results)} advertiseri au product feeds. Păstrează scraping via agent_altemagazine.py.")


if __name__ == '__main__':
    main()
