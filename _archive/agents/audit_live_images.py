"""Live-probe every image URL in deals.json. Flag anything that doesn't return HTTP 200 with image content-type."""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from collections import Counter

BASE = Path(__file__).resolve().parent.parent
with open(BASE/"data"/"deals.json", encoding="utf-8") as f:
    deals = json.load(f)

print(f"total deals: {len(deals)}")

def probe(idx_deal):
    idx, d = idx_deal
    img = d.get("image") or d.get("imagine_url","")
    if not img:
        return (idx, d.get("id"), d.get("magazin"), None, "NO_IMG", "")
    req = urllib.request.Request(img, headers={"User-Agent":"Mozilla/5.0 GhidulReducerilorBot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            code = r.status
            ct = r.headers.get("Content-Type","")
            if code != 200 or not ct.startswith("image/"):
                return (idx, d.get("id"), d.get("magazin"), code, ct, img)
            return None
    except Exception as e:
        return (idx, d.get("id"), d.get("magazin"), None, type(e).__name__, img)

bad = []
with ThreadPoolExecutor(max_workers=16) as ex:
    futures = {ex.submit(probe, (i, d)): i for i, d in enumerate(deals)}
    done = 0
    for fut in as_completed(futures):
        r = fut.result()
        done += 1
        if r: bad.append(r)
        if done % 50 == 0:
            print(f"  probed {done}/{len(deals)} | bad so far: {len(bad)}")

print(f"\n=== BAD IMAGES: {len(bad)} / {len(deals)} ===\n")
by_mag = Counter(b[2] for b in bad)
print("by magazin:")
for m, c in by_mag.most_common():
    print(f"  {c:>4}  {m}")

by_err = Counter(f"{b[3]}|{b[4][:30]}" for b in bad)
print("\nby error type:")
for e, c in by_err.most_common():
    print(f"  {c:>4}  {e}")

print("\nsample 10 bad (id | status | url[:80]):")
for b in bad[:10]:
    print(f"  {b[1]:<35} | {b[3]}/{b[4][:20]} | {b[5][:80]}")

# Save list for fix script
out = BASE / "logs" / "bad_images.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps([{"idx":b[0],"id":b[1],"magazin":b[2],"status":b[3],"error":b[4],"url":b[5]} for b in bad], indent=2), encoding="utf-8")
print(f"\nwrote {out}")
