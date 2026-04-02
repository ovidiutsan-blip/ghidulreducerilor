#!/usr/bin/env python3
"""
GhidulReducerilor.ro — Social Media Poster
Generează și postează conținut pe Facebook, Instagram, TikTok.

Utilizare:
  python scripts/social_media_poster.py --platform facebook --type deal
  python scripts/social_media_poster.py --platform all --type top_deals
  python scripts/social_media_poster.py --session morning
"""

import json
import os
import sys
import logging
import argparse
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("Instalează requests: pip install requests")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/social_media.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('social_media')

ROOT = Path(__file__).parent.parent
CONFIG_DIR = ROOT / 'config'
DATA_DIR = ROOT / 'data'

sys.path.insert(0, str(Path(__file__).parent))
from utils import normalize_deal  # noqa: E402

# API Keys din env
FB_PAGE_ID = os.environ.get('FB_PAGE_ID', '')
FB_ACCESS_TOKEN = os.environ.get('FB_ACCESS_TOKEN', '')
IG_USER_ID = os.environ.get('IG_USER_ID', '')
IG_ACCESS_TOKEN = os.environ.get('IG_ACCESS_TOKEN', '')


def load_deals() -> list:
    """Încarcă ofertele active (normalizate EN+RO)."""
    with open(DATA_DIR / 'deals.json', 'r', encoding='utf-8') as f:
        return [normalize_deal(d) for d in json.load(f)]


def load_codes() -> list:
    """Încarcă codurile promoționale."""
    codes_path = DATA_DIR / 'codes.json'
    if codes_path.exists():
        with open(codes_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def load_social_config() -> dict:
    """Încarcă configurația social media."""
    with open(CONFIG_DIR / 'social_media.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def get_top_deals(deals: list, n: int = 5) -> list:
    """Returnează cele mai bune n oferte."""
    active = [d for d in deals if d.get('is_active', True)]
    return sorted(active, key=lambda d: (
        d.get('score', 5),
        d.get('discount_percent', 0)
    ), reverse=True)[:n]


def get_hashtags(config: dict, platform: str, category: str = 'general') -> str:
    """Generează string cu hashtag-uri pentru platformă."""
    platform_config = config['platforme'].get(platform, {})
    hashtag_sets = platform_config.get('hashtag_sets', {})

    general = hashtag_sets.get('general', [])
    category_tags = hashtag_sets.get(category, [])

    all_tags = list(set(general + category_tags))
    random.shuffle(all_tags)

    # Limită hashtag-uri per platformă
    max_tags = platform_config.get('hashtag_uri_per_post', 10)
    return ' '.join(all_tags[:max_tags])


def generate_facebook_post(deal: dict, config: dict, post_type: str = 'deal_simplu') -> str:
    """Generează textul unui post Facebook."""
    fb_config = config['platforme']['facebook']
    template = fb_config['template_posturi'].get(post_type, '')

    title = deal.get('title', 'Produs în reducere')
    discount = deal.get('discount_percent', 0)
    store = deal.get('store', deal.get('magazine_name', ''))
    price_new = deal.get('price', deal.get('newPrice', 0))
    price_old = deal.get('originalPrice', deal.get('original_price', 0))
    link = deal.get('affiliate_url') or deal.get('url', 'https://ghidulreducerilor.ro')

    magazine_hashtag = store.lower().replace(' ', '').replace('.', '').replace('-', '')

    post_text = template \
        .replace('{procent}', str(discount)) \
        .replace('{produs}', title[:50]) \
        .replace('{pret_vechi}', str(price_old)) \
        .replace('{pret_nou}', str(price_new)) \
        .replace('{magazin}', store) \
        .replace('{magazin_hashtag}', magazine_hashtag)

    return f"{post_text}\n\n👉 {link}"


def generate_facebook_top_deals_post(deals: list, config: dict) -> str:
    """Generează post cu top deals pentru Facebook."""
    fb_config = config['platforme']['facebook']
    template = fb_config['template_posturi'].get('top_deals', '')

    top = get_top_deals(deals, 5)
    now = datetime.now()
    data_ro = now.strftime('%d.%m.%Y')

    lista_deals = ''
    for i, deal in enumerate(top, 1):
        title = deal.get('title', 'Produs')[:40]
        discount = deal.get('discount_percent', 0)
        price_new = deal.get('price', deal.get('newPrice', ''))
        lista_deals += f"{i}. {title} — -{discount}% → {price_new} RON\n"

    post_text = template \
        .replace('{numar}', str(len(top))) \
        .replace('{data}', data_ro) \
        .replace('{lista_deals}', lista_deals)

    return post_text


def generate_instagram_caption(deal: dict, config: dict) -> str:
    """Generează caption Instagram pentru un deal."""
    title = deal.get('title', 'Produs în reducere')
    discount = deal.get('discount_percent', 0)
    store = deal.get('store', deal.get('magazine_name', ''))
    price_new = deal.get('price', deal.get('newPrice', 0))
    price_old = deal.get('originalPrice', deal.get('original_price', 0))

    # Detectează categoria pentru hashtag-uri
    categories = deal.get('categories', [])
    category = 'general'
    if any(c in ['fashion', 'imbracaminte', 'haine'] for c in [str(c).lower() for c in categories]):
        category = 'fashion'
    elif any(c in ['tech', 'electronice', 'laptop', 'telefon'] for c in [str(c).lower() for c in categories]):
        category = 'tech'
    elif any(c in ['beauty', 'cosmetice', 'parfum'] for c in [str(c).lower() for c in categories]):
        category = 'beauty'
    elif any(c in ['sport', 'fitness'] for c in [str(c).lower() for c in categories]):
        category = 'sport'

    caption = f"""🔥 -{discount}% la {title[:50]}!

💰 {price_old} RON → {price_new} RON
🏪 {store}

👉 Link în bio sau ghidulreducerilor.ro

{get_hashtags(config, 'instagram', category)}"""

    return caption


def generate_tiktok_title(deal: dict, config: dict) -> str:
    """Generează titlu TikTok pentru un deal."""
    tiktok_config = config['platforme']['tiktok']
    templates = tiktok_config.get('template_titluri', [])
    template = random.choice(templates)

    title = deal.get('title', 'produs')
    store = deal.get('store', deal.get('magazine_name', ''))
    price_new = deal.get('price', deal.get('newPrice', 0))
    price_old = deal.get('originalPrice', deal.get('original_price', 0))
    economy = round(float(price_old or 0) - float(price_new or 0), 0) if price_old and price_new else 0

    return template \
        .replace('{magazin}', store) \
        .replace('{produs}', title[:30]) \
        .replace('{pret_vechi}', str(price_old)) \
        .replace('{pret_nou}', str(price_new)) \
        .replace('{suma}', str(int(economy)))


def post_to_facebook(message: str, link: Optional[str] = None) -> bool:
    """Postează pe pagina Facebook via Graph API."""
    if not FB_ACCESS_TOKEN or not FB_PAGE_ID:
        logger.error("FB_ACCESS_TOKEN sau FB_PAGE_ID lipsesc!")
        return False

    url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/feed"

    data = {'message': message, 'access_token': FB_ACCESS_TOKEN}
    if link:
        data['link'] = link

    try:
        response = requests.post(url, data=data, timeout=30)
        if response.status_code == 200:
            post_id = response.json().get('id', 'unknown')
            logger.info(f"Post Facebook publicat: {post_id}")
            return True
        else:
            logger.error(f"Eroare Facebook API: {response.status_code} — {response.text[:200]}")
            return False
    except requests.RequestException as e:
        logger.error(f"Eroare conexiune Facebook: {e}")
        return False


def post_to_instagram(caption: str, image_url: str) -> bool:
    """
    Postează pe Instagram Business via Graph API.
    Necesită imagine URL public accesibil.
    """
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        logger.error("IG_ACCESS_TOKEN sau IG_USER_ID lipsesc!")
        return False

    # Pas 1: Creează container media
    container_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media"
    container_data = {
        'image_url': image_url,
        'caption': caption,
        'access_token': IG_ACCESS_TOKEN
    }

    try:
        container_response = requests.post(container_url, data=container_data, timeout=30)
        if container_response.status_code != 200:
            logger.error(f"Eroare creare container Instagram: {container_response.text[:200]}")
            return False

        container_id = container_response.json().get('id')

        # Pas 2: Publică media
        publish_url = f"https://graph.facebook.com/v18.0/{IG_USER_ID}/media_publish"
        publish_data = {
            'creation_id': container_id,
            'access_token': IG_ACCESS_TOKEN
        }

        publish_response = requests.post(publish_url, data=publish_data, timeout=30)
        if publish_response.status_code == 200:
            media_id = publish_response.json().get('id', 'unknown')
            logger.info(f"Post Instagram publicat: {media_id}")
            return True
        else:
            logger.error(f"Eroare publicare Instagram: {publish_response.text[:200]}")
            return False

    except requests.RequestException as e:
        logger.error(f"Eroare conexiune Instagram: {e}")
        return False


def generate_tiktok_script(deal: dict) -> str:
    """
    Generează scriptul video pentru TikTok (text pentru creator).
    TikTok nu are API public pentru postare automată — scriptul e generat manual.
    """
    title = deal.get('title', 'Produs')
    discount = deal.get('discount_percent', 0)
    store = deal.get('store', deal.get('magazine_name', ''))
    price_new = deal.get('price', deal.get('newPrice', 0))
    price_old = deal.get('originalPrice', deal.get('original_price', 0))
    link = deal.get('affiliate_url') or deal.get('url', 'https://ghidulreducerilor.ro')

    return f"""
=== SCRIPT TIKTOK ===
Durata: 30-60 secunde

[0-3s] Hook: Am găsit reducere de -{discount}% la {store}!

[3-15s] Demo produs:
- Arată produsul: {title}
- Preț vechi: {price_old} RON
- Preț nou: {price_new} RON

[15-25s] Validare autentică:
- Verificăm dacă e reducere reală
- Compară cu prețul din ultimele 30 de zile

[25-30s] CTA:
- Link în bio sau caută ghidulreducerilor.ro
- {link}

Caption: {title[:80]} -redus cu {discount}%! 🔥
Hashtag-uri: #reduceri #oferte #{store.lower().replace(' ','')} #ghidulreducerilor
===================
"""


def run_session(session: str, config: dict, deals: list, dry_run: bool = False):
    """Rulează sesiunea de postare (morning/afternoon/evening)."""
    logger.info(f"=== Sesiune social media: {session} ===")
    top_deals = get_top_deals(deals, 10)

    if not top_deals:
        logger.warning("Nu există oferte active pentru postare!")
        return

    # Alege deal-ul zilei sau random din top 5
    deal_of_session = random.choice(top_deals[:5])

    results = {'facebook': False, 'instagram': False, 'tiktok_script': False}

    # Facebook
    fb_config = config['platforme'].get('facebook', {})
    if fb_config.get('activ', False):
        if session == 'morning':
            # Morning: top deals list
            fb_text = generate_facebook_top_deals_post(deals, config)
            fb_link = 'https://ghidulreducerilor.ro'
        else:
            # Alte sesiuni: deal individual
            fb_text = generate_facebook_post(deal_of_session, config)
            fb_link = deal_of_session.get('affiliate_url') or deal_of_session.get('url')

        if dry_run:
            logger.info(f"[DRY RUN] Facebook post:\n{fb_text[:300]}...")
            results['facebook'] = True
        else:
            results['facebook'] = post_to_facebook(fb_text, fb_link)

    # Instagram
    ig_config = config['platforme'].get('instagram', {})
    if ig_config.get('activ', False):
        ig_caption = generate_instagram_caption(deal_of_session, config)
        ig_image = deal_of_session.get('image', '')

        if ig_image:
            if dry_run:
                logger.info(f"[DRY RUN] Instagram caption:\n{ig_caption[:300]}...")
                results['instagram'] = True
            else:
                results['instagram'] = post_to_instagram(ig_caption, ig_image)
        else:
            logger.warning(f"Deal fără imagine, skip Instagram: {deal_of_session.get('title')}")

    # TikTok (script generat, nu postare automată)
    tiktok_config = config['platforme'].get('tiktok', {})
    if tiktok_config.get('activ', False) and session in ['morning', 'evening']:
        tiktok_deal = random.choice(top_deals[:3])
        script = generate_tiktok_script(tiktok_deal)
        title = generate_tiktok_title(tiktok_deal, config)

        script_path = ROOT / 'data' / f"tiktok_script_{session}_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(f"Titlu: {title}\n\n{script}")

        logger.info(f"Script TikTok generat: {script_path}")
        results['tiktok_script'] = True

    logger.info(f"Rezultate sesiune {session}: {results}")
    return results


def main():
    parser = argparse.ArgumentParser(description='GhidulReducerilor Social Media Poster')
    parser.add_argument('--platform', choices=['facebook', 'instagram', 'tiktok', 'all'], default='all')
    parser.add_argument('--type', choices=['deal', 'top_deals', 'code'], default='top_deals')
    parser.add_argument('--session', choices=['morning', 'afternoon', 'evening', 'early_morning'], default='morning')
    parser.add_argument('--dry-run', action='store_true', help='Generează dar nu postează')
    args = parser.parse_args()

    logger.info(f"=== Social Media Poster — {args.platform} / {args.session} ===")

    deals = load_deals()
    config = load_social_config()

    run_session(args.session, config, deals, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
