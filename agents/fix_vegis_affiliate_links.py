#!/usr/bin/env python3
"""Fix one-time: reimpacheteaza linkurile brute vegis.ro in deeplink Profitshare.

Context: 101 deal-uri vegis (id `vegis-{hash}`, din scraperul vechi) au
`link_afiliat` = URL brut vegis.ro => zero comision. vegis E pe Profitshare;
deal-urile din feed (id `ps-vegis-...`) folosesc deeplink-ul:
    https://app.profitshare.ro/lps/djp/kd8/?redirect=<product_url encodat>

Scriptul deriva prefixul din deal-urile vegis care DEJA au link profitshare
corect (nu hardcodeaza codul), apoi il aplica celor brute. Idempotent.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DEALS = ROOT / "data" / "deals.json"

PREFIX_RE = re.compile(r"^(https://app\.profitshare\.ro/lps/[^/]+/[^/]+/\?redirect=)")


def main():
    raw = json.loads(DEALS.read_text(encoding="utf-8"))
    arr = raw if isinstance(raw, list) else raw.get("deals", [])

    # 1) deriva prefixul din primul deal vegis cu link profitshare valid
    prefix = None
    for d in arr:
        if d.get("magazin") == "vegis":
            m = PREFIX_RE.match(d.get("link_afiliat", ""))
            if m:
                prefix = m.group(1)
                break
    if not prefix:
        print("EROARE: nu am gasit niciun deal vegis cu link Profitshare de referinta.")
        return
    print(f"Prefix derivat: {prefix}")

    # 2) impacheteaza brutele
    fixed = 0
    for d in arr:
        if d.get("magazin") != "vegis":
            continue
        link = d.get("link_afiliat", "") or ""
        if "profitshare" in link:
            continue  # deja corect
        product_url = d.get("product_url") or d.get("url") or ""
        if "vegis.ro" not in product_url:
            continue
        new_link = prefix + quote(product_url, safe="")
        d["link_afiliat"] = new_link
        # sincronizeaza campurile legacy daca exista
        if "affiliate_url" in d:
            d["affiliate_url"] = new_link
        fixed += 1

    if fixed == 0:
        print("Nimic de reparat (toate deja corecte).")
        return

    DEALS.write_text(
        json.dumps(arr if isinstance(raw, list) else {**raw, "deals": arr},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"OK: {fixed} linkuri vegis reimpachetate in deeplink Profitshare.")


if __name__ == "__main__":
    main()
