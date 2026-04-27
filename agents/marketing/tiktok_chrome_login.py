import subprocess, sys, time
from pathlib import Path

PROFILE = r"C:\dev\ghidulreducerilor.ro\agents\marketing\tiktok_browser_profile"
CHROME  = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

Path(PROFILE).mkdir(parents=True, exist_ok=True)

print("[INFO] Deschid Chrome la TikTok login...")
print("[INFO] Profile dir:", PROFILE)

proc = subprocess.Popen([
    CHROME,
    f"--user-data-dir={PROFILE}",
    "--new-window",
    "--no-first-run",
    "--no-default-browser-check",
    "https://www.tiktok.com/login"
])

print()
print("="*55)
print("CREEAZA CONT TIKTOK:")
print("  1. Click 'Use phone or email'")
print("  2. Alege 'Email'")
print("  3. Email: contact@ghidulreducerilor.ro")
print("  4. Seteaza parola")
print("  5. Verifica email (vine in Gmail ca forward)")
print()
print("Apasa ENTER cand esti logat pe TikTok...")
input()

print("[OK] Sesiune salvata in:", PROFILE)
print("[OK] Inchid Chrome...")
proc.terminate()
print("[DONE] Setup complet!")
