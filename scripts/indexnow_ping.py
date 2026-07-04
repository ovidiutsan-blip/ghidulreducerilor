#!/usr/bin/env python3
"""
GhidulReducerilor.ro — IndexNow ping
Anunță motoarele de căutare (Bing, Yandex, Seznam, Naver — protocol partajat)
că paginile s-au schimbat, imediat după actualizarea zilnică a ofertelor.
Google nu suportă IndexNow, dar descoperă schimbările prin sitemap.

Rulare: python scripts/indexnow_ping.py
"""

import sys
import xml.etree.ElementTree as ET

import requests

SITE = "https://ghidulreducerilor.ro"
KEY = "2fbe74572bd296845e920501e42623f6"  # public/{KEY} — cheie publică prin design
SITEMAP_URL = f"{SITE}/sitemap.xml"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
TIMEOUT = 20


def get_sitemap_urls() -> list[str]:
    r = requests.get(SITEMAP_URL, timeout=TIMEOUT)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text.strip() for loc in root.findall(".//sm:loc", ns) if loc.text]


def ping(urls: list[str]) -> int:
    payload = {
        "host": SITE.removeprefix("https://"),
        "key": KEY,
        "keyLocation": f"{SITE}/{KEY}",
        "urlList": urls[:10000],  # limita protocolului
    }
    r = requests.post(INDEXNOW_ENDPOINT, json=payload, timeout=TIMEOUT,
                      headers={"Content-Type": "application/json; charset=utf-8"})
    return r.status_code


def main() -> int:
    try:
        urls = get_sitemap_urls()
    except Exception as e:
        print(f"[indexnow] Eroare la citirea sitemap-ului: {e}")
        return 1

    if not urls:
        print("[indexnow] Sitemap gol — nimic de trimis")
        return 0

    try:
        status = ping(urls)
    except Exception as e:
        print(f"[indexnow] Eroare la ping: {e}")
        return 1

    # 200 = OK, 202 = acceptat (validarea cheii urmează async)
    if status in (200, 202):
        print(f"[indexnow] OK ({status}) — {len(urls)} URL-uri trimise")
        return 0
    print(f"[indexnow] Răspuns neașteptat: HTTP {status}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
