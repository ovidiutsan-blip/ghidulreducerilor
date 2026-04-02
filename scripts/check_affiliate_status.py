"""
Script pentru verificarea statusului aplicațiilor de afiliere
Rulează: python scripts/check_affiliate_status.py
"""

import json
import os
from datetime import datetime

STATUS_FILE = os.path.join(os.path.dirname(__file__), "..", "config", "affiliate_status.json")

MAGAZINE = {
    "notino":    {"platform": "2Performant", "url": "https://2performant.com/affiliate-programs/beauty/notino-ro/"},
    "answear":   {"platform": "2Performant", "url": "https://2performant.com/affiliate-programs/fashion/answear-ro/"},
    "decathlon": {"platform": "2Performant", "url": "https://2performant.com/affiliate-programs/sports-outdoors/decathlon-ro/"},
    "cel":       {"platform": "2Performant", "url": "https://2performant.com → caută CEL.ro"},
    "pcgarage":  {"platform": "Profitshare", "url": "https://profitshare.ro/affiliate-programs/it-c/pcgarage"},
    "dr_max":    {"platform": "2Performant", "url": "https://2performant.com → caută Dr Max"},
}

STATUS_ICONS = {
    "neaplicat": "⏳",
    "aplicat":   "📨",
    "aprobat":   "✅",
    "respins":   "❌",
}

def check_and_report():
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status = json.load(f)
    except FileNotFoundError:
        status = {}

    print("\n" + "=" * 65)
    print(f"  STATUS AFILIERE — ghidulreducerilor.ro")
    print(f"  Verificat: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("=" * 65)

    all_approved = True
    for mag, info in MAGAZINE.items():
        entry = status.get(mag, {})
        s = entry.get("status", "neaplicat")
        icon = STATUS_ICONS.get(s, "❓")
        comision = entry.get("comision", "N/A")
        note = entry.get("note", "")

        print(f"\n  {icon} {mag.upper():12} | {info['platform']:14} | {s.upper()}")
        print(f"     Comision: {comision}")
        if entry.get("data_aplicare"):
            print(f"     Aplicat:  {entry['data_aplicare']}")
        if entry.get("data_aprobare"):
            print(f"     Aprobat:  {entry['data_aprobare']}")
        if entry.get("affiliate_id"):
            print(f"     Aff ID:   {entry['affiliate_id']}")
        if s == "neaplicat":
            all_approved = False
            print(f"     → Aplică: {info['url']}")
        if note:
            print(f"     ⚠ {note}")

    print("\n" + "=" * 65)
    if all_approved:
        print("  🎉 Toate programele sunt aprobate!")
    else:
        pending = sum(1 for m in MAGAZINE if status.get(m, {}).get("status", "neaplicat") == "neaplicat")
        print(f"  ⏳ {pending} program(e) neaplicat(e) — actualizează config/affiliate_status.json")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    check_and_report()
