"""
tiktok_cdp_login.py - Login TikTok via CDP (Edge cu remote debugging).
Nu foloseste --remote-debugging-pipe (blocat de ZoneAlarm).
"""
import subprocess, sys, time, json
from pathlib import Path

PROFILE = Path(__file__).parent / "tiktok_browser_profile"
EDGE    = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CDP_PORT = 9333  # port diferit de Chrome (9222)

PROFILE.mkdir(parents=True, exist_ok=True)

print("[INFO] Lansez Edge cu remote debugging pe portul", CDP_PORT)
proc = subprocess.Popen([
    EDGE,
    f"--remote-debugging-port={CDP_PORT}",
    f"--user-data-dir={PROFILE}",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-blink-features=AutomationControlled",
    "https://www.tiktok.com/login"
], creationflags=subprocess.CREATE_NEW_CONSOLE)

time.sleep(3)

# Conecteaza Playwright via CDP
try:
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    browser = p.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
    print("[OK] Playwright conectat via CDP!")
    
    print()
    print("="*55)
    print("CREEAZA CONT TIKTOK in browser-ul Edge deschis:")
    print("  1. Click 'Use phone or email' -> Email")  
    print("  2. Email: contact@ghidulreducerilor.ro")
    print("  3. Seteaza parola")
    print("  4. Verifica email-ul (vine in Gmail)")
    print()
    print("Apasa ENTER cand esti logat pe TikTok...")
    input()
    
    # Salveaza cookies
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    cookies = ctx.cookies()
    cookies_path = Path(__file__).parent / "tiktok_cookies.json"
    with open(cookies_path, "w") as f:
        json.dump(cookies, f, indent=2)
    print(f"[OK] {len(cookies)} cookies salvate in {cookies_path}")
    
    browser.disconnect()
    p.stop()
    print("[DONE] Setup complet!")

except Exception as e:
    print(f"[ERR] {e}")
    print("[HINT] Asigura-te ca Edge e deschis si logat pe TikTok")

proc.terminate()
