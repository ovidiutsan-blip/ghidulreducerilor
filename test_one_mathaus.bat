@echo off
cd /d "C:\Users\ovidi\OneDrive\Desktop\GHIDULREDUCERILOR.RO"
C:\Python314\python.exe -c "
import json, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

data = json.loads(open('data/deals.json', encoding='utf-8').read())
deal = next(d for d in data if d.get('magazin')=='mathaus' and 'cdn.mathaus.ro' in d.get('imagine_url',''))
purl = deal.get('product_url') or deal.get('link_afiliat') or ''
print('Deal:', deal['id'])
print('Image URL:', deal.get('imagine_url','')[:80])
print('Product URL:', purl[:80])
print()

captured = {}
def on_resp(r):
    if 'cdn.mathaus.ro' in r.url and r.status==200:
        ct = r.headers.get('content-type','')
        if 'image' in ct:
            try:
                b = r.body()
                if len(b)>500:
                    captured[r.url] = b
                    print(f'CAPTURED: {r.url[:70]} ({len(b)//1024}KB)')
            except: pass

with sync_playwright() as p:
    br = p.chromium.launch(headless=True, args=['--no-sandbox'])
    ctx = br.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', viewport={'width':1280,'height':800}, locale='ro-RO')
    ctx.route('**/*.{woff,woff2,ttf,mp4}', lambda r: r.abort())
    pg = ctx.new_page()
    pg.on('response', on_resp)
    try:
        print(f'Navigating to: {purl[:70]}')
        pg.goto(purl, timeout=25000, wait_until='domcontentloaded')
        pg.evaluate('window.scrollTo(0,400)')
        pg.wait_for_timeout(3000)
        print(f'Captured {len(captured)} images from CDN')
        if not captured:
            print('DOM imgs:')
            imgs = pg.evaluate(\"[...document.querySelectorAll('img')].map(i=>({src:i.src,w:i.naturalWidth,h:i.naturalHeight})).filter(i=>i.src&&i.w>0)\")
            for im in imgs[:5]:
                print(' ', im)
    except Exception as e:
        print('ERR:', e)
    finally:
        pg.close()
    br.close()

print('Done. Captured:', list(captured.keys())[:3])
"
echo EXIT_CODE=%ERRORLEVEL%
