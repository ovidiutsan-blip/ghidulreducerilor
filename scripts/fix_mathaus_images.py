#!/usr/bin/env python3
"""
fix_mathaus_images.py
Descarcă imaginile mathaus local (bypass CloudFlare via urllib cu Referer)
și actualizează deals.json să pointeze la /images/mathaus/xxx.jpg
"""
import json
import sys
import re
import urllib.request
from pathlib import Path

REPO = Path(r'C:\Users\ovidi\OneDrive\Desktop\GHIDULREDUCERILOR.RO')
DEALS_PATH = REPO / 'data' / 'deals.json'
IMG_DIR = REPO / 'public' / 'images' / 'mathaus'
IMG_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'ro-RO,ro;q=0.9,en;q=0.8',
    'Referer': 'https://www.mathaus.ro/',
}


def download_image(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read()
            if len(content) < 500:
                print(f'  SKIP prea mic {len(content)}B')
                return False
            dest.write_bytes(content)
            print(f'  OK {len(content)//1024}KB -> {dest.name}')
            return True
    except Exception as e:
        print(f'  FAIL: {e}')
        return False


def url_to_filename(deal_id: str, img_url: str) -> str:
    ext = img_url.split('?')[0].rsplit('.', 1)[-1].lower()
    if ext not in ('jpg', 'jpeg', 'png', 'webp'):
        ext = 'jpg'
    safe_id = re.sub(r'[^a-z0-9-]', '', deal_id)[:60]
    return f'{safe_id}.{ext}'


def main():
    data = json.loads(DEALS_PATH.read_text(encoding='utf-8'))
    mathaus_deals = [d for d in data if d.get('magazin') == 'mathaus']
    cdn_deals = [d for d in mathaus_deals if 'cdn.mathaus.ro' in d.get('imagine_url', '')]

    print(f'Mathaus deals: {len(mathaus_deals)}, de downloadat: {len(cdn_deals)}')
    print()

    fixed = 0
    failed = []

    for deal in cdn_deals:
        deal_id = deal['id']
        img_url = deal.get('imagine_url', '')
        if not img_url:
            continue

        filename = url_to_filename(deal_id, img_url)
        dest = IMG_DIR / filename
        local_url = f'/images/mathaus/{filename}'

        if dest.exists() and dest.stat().st_size > 500:
            print(f'CACHED: {filename}')
            deal['imagine_url'] = local_url
            deal['image'] = local_url
            fixed += 1
            continue

        print(f'[{fixed+1}/{len(cdn_deals)}] {deal_id[:50]}')
        print(f'  {img_url[:80]}')

        if download_image(img_url, dest):
            deal['imagine_url'] = local_url
            deal['image'] = local_url
            fixed += 1
        else:
            failed.append(deal_id)

    print()
    print(f'Rezultat: {fixed} fixate, {len(failed)} esuate')
    if failed:
        print('Esuate:', failed)

    DEALS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print('deals.json salvat.')
    return fixed, len(failed)


if __name__ == '__main__':
    main()
