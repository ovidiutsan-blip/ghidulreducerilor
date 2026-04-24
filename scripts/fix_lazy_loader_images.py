#!/usr/bin/env python3
"""
fix_lazy_loader_images.py
Găsește toate produsele vegis cu imagine_url = lazy-loader.gif
și înlocuiește cu OG image scraped de pe pagina produsului.
"""
import json, re, time, sys
from pathlib import Path
from datetime import datetime, timezone
import urllib.request

ROOT = Path(__file__).parent.parent
DEALS = ROOT / 'data' / 'deals.json'
LAZY_URL = 'lazy-loader.gif'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'ro-RO,ro;q=0.9,en;q=0.8',
}


def fetch_og_image(url: str, timeout: int = 8) -> str | None:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read(80_000).decode('utf-8', errors='ignore')
        # og:image
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html)
        if m:
            return m.group(1).strip()
        # fallback: og:image cu ordinea atributelor inversată
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html)
        if m:
            img = m.group(1).strip()
            if img and 'lazy' not in img.lower():
                return img
        return None
    except Exception as e:
        return None


def main():
    dry_run = '--dry-run' in sys.argv
    data = json.loads(DEALS.read_text(encoding='utf-8'))

    bad = [d for d in data if LAZY_URL in (d.get('imagine_url') or '')]
    print(f'Produse cu lazy-loader: {len(bad)}')
    if dry_run:
        print('[DRY RUN] Nu se modifică nimic.')

    fixed = 0
    failed = 0
    for i, deal in enumerate(bad):
        url = deal.get('product_url') or deal.get('link_afiliat') or deal.get('url') or ''
        if not url:
            print(f'  [{i+1}/{len(bad)}] {deal["id"]} — no product_url, skip')
            failed += 1
            continue

        og = fetch_og_image(url)
        if og and 'lazy' not in og.lower() and og.startswith('http'):
            print(f'  [{i+1}/{len(bad)}] {deal["id"]} OK {og[:80]}')
            if not dry_run:
                # Actualizează în lista principală
                for d in data:
                    if d['id'] == deal['id']:
                        d['imagine_url'] = og
                        d['image'] = og
                        d['image_fixed_at'] = datetime.now(timezone.utc).isoformat()
                        d['image_fix_source'] = 'fix-lazy-loader'
                        break
            fixed += 1
        else:
            print(f'  [{i+1}/{len(bad)}] {deal["id"]} FAIL og={og!r:.60}')
            failed += 1

        time.sleep(0.3)  # politicos cu serverul

    if not dry_run and fixed > 0:
        DEALS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'\nSalvat deals.json -- {fixed} fixate, {failed} esuate.')
    else:
        print(f'\n[DRY RUN] {fixed} ar fi fixate, {failed} ar esua.')


if __name__ == '__main__':
    main()
