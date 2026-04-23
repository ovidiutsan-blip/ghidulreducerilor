"""Hotpick agent — magazin electrocasnice/gadgeturi, platforma OpenCart/Gomag-hybrid.

Platforma: probabil OpenCart cu CDN intern.
Imagini: https://hotpick.ro/image/cache/img/jpg/catalog/gomag/{slug}-{W}x{H}.webp

Agentul:
1. fix_broken_images: scrape og:image de pe hotpick.ro.
2. fetch_deals: TODO via PS feed hotpick.
"""
from __future__ import annotations
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from .base import MerchantAgent, Deal, now_iso

OG = re.compile(
    r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
    re.I,
)
OG_REV = re.compile(
    r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
    re.I,
)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"


class HotpickAgent(MerchantAgent):
    slug = "hotpick"
    name = "Hotpick (electrocasnice/gadgeturi)"
    default_category = "electronice"

    def _fetch_og_image(self, product_url: str) -> str | None:
        try:
            r = requests.get(
                product_url,
                headers={"User-Agent": UA, "Accept": "text/html"},
                timeout=15, allow_redirects=True,
            )
            if not r.ok:
                return None
            m = OG.search(r.text) or OG_REV.search(r.text)
            if not m:
                return None
            img = m.group(1).strip()
            # Accept numai imagini de pe hotpick.ro
            if "hotpick.ro" not in img:
                return None
            return img
        except Exception:
            return None

    def fix_broken_images(self, broken_deals: list[dict]) -> dict[str, str]:
        mine = [d for d in broken_deals if d.get("magazin") == self.slug]
        if not mine:
            return {}
        results: dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {
                ex.submit(self._fetch_og_image, d.get("product_url", "")): d.get("id")
                for d in mine if d.get("product_url")
            }
            for fut in as_completed(futures):
                did = futures[fut]
                img = fut.result()
                if img and did:
                    results[did] = img
        return results

    def fetch_deals(self) -> list[Deal]:
        """Full refresh — TODO via PS feed hotpick."""
        return []
