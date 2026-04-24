#!/usr/bin/env python3
"""
fix_mathaus_playwright.py v3 — context nou per deal (evita cache browser)
"""
import json, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path

REPO = Path(r'C:\Users\ovidi\OneDrive\Desktop\GHIDULREDUCERILOR.RO')
DEALS_PATH = REPO / 'data' / 'deals.json'
IMG_DIR = REPO / 'public' / 'images' / 'mathaus'
IMG_DIR.mkdir(parents=True, exist_ok=True)

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')


def safe_fn(deal_id, ext='jpg'):
    return re.sub(r'[^a-z0-9-]', '', deal_id)[:60] + '.' + ext

def ext_from(url):
    e = url.split('?')[0].rsplit('.', 1)[-1].lower()
    return e if e in ('jpg', 'jpeg', 'png', 'webp') else 'jpg'


def try_get_image(browser, purl, deal_id, img_url):
    """Viziteaza pagina produsului si captureaza imaginea principala."""
    from playwright.sync_api import TimeoutError as PWTimeout

    captured = {}

    def on_resp(r):
        if 'cdn.mathaus.ro' in r.url and r.status == 200:
            ct = r.headers.get('content-type', '')
            if 'image' in ct:
                try:
                    b = r.body()
                    if len(b) > 2000:  # minim 2KB - exclude iconite
                        captured[r.url] = b
                except Exception:
                    pass

    # Context nou per deal = fara cache, cookies proaspete
    ctx = browser.new_context(
        user_agent=UA,
        viewport={'width': 1280, 'height': 800},
        locale='ro-RO',
    )
    ctx.route('**/*.{woff,woff2,ttf,mp4,avi}', lambda r: r.abort())

    page = ctx.new_page()
    page.on('response', on_resp)

    try:
        page.goto(purl, timeout=25000, wait_until='domcontentloaded')
        page.evaluate('window.scrollTo(0, 500)')
        page.wait_for_timeout(3000)

        if captured:
            # Alege imaginea cea mai mare (principala, nu thumbnail)
            best_url = max(captured, key=lambda u: len(captured[u]))
            best_bytes = captured[best_url]
            act_ext = ext_from(best_url)
            fn = safe_fn(deal_id, act_ext)
            (IMG_DIR / fn).write_bytes(best_bytes)
            return f'/images/mathaus/{fn}', len(best_bytes)
        return None, 0

    except PWTimeout:
        print(f'  TIMEOUT')
        return None, 0
    except Exception as e:
        print(f'  ERR: {e}')
        return None, 0
    finally:
        page.close()
        ctx.close()  # Inchide contextul (sterge cache-ul)


def main():
    from playwright.sync_api import sync_playwright

    data = json.loads(DEALS_PATH.read_text(encoding='utf-8'))
    cdn_deals = [d for d in data
                 if d.get('magazin') == 'mathaus'
                 and 'cdn.mathaus.ro' in d.get('imagine_url', '')]
    print(f'De reparat: {len(cdn_deals)} deals')

    fixed, failed = 0, []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled'],
        )

        for i, deal in enumerate(cdn_deals):
            did = deal['id']
            img_url = deal.get('imagine_url', '')
            purl = (deal.get('product_url') or
                    deal.get('link_afiliat') or
                    deal.get('url') or '')

            fn = safe_fn(did, ext_from(img_url))
            dest = IMG_DIR / fn
            if dest.exists() and dest.stat().st_size > 2000:
                print(f'[{i+1}] CACHED {fn}')
                deal['imagine_url'] = f'/images/mathaus/{fn}'
                deal['image'] = f'/images/mathaus/{fn}'
                fixed += 1
                continue

            if not purl:
                print(f'[{i+1}] SKIP no url: {did[:50]}')
                failed.append(did)
                continue

            print(f'[{i+1}/{len(cdn_deals)}] {did[:55]}')
            local_url, size_kb = try_get_image(browser, purl, did, img_url)

            if local_url:
                print(f'  OK {size_kb//1024}KB -> {Path(local_url).name}')
                deal['imagine_url'] = local_url
                deal['image'] = local_url
                fixed += 1
            else:
                print(f'  FAIL')
                failed.append(did)

        browser.close()

    print(f'\nRezultat: {fixed} fixate, {len(failed)} esuate')
    if failed:
        for f in failed:
            print(f'  {f}')

    DEALS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print('deals.json salvat.')
    return fixed, len(failed)


if __name__ == '__main__':
    main()
