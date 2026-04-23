"""Vegis agent — magazin produse naturale/bio, CDN cdn.vegis.ro.

Platforma: custom PHP cu CDN propriu cdn.vegis.ro.
Imagini: https://cdn.vegis.ro/images/products/img_YYYYMMDDHHII/{id}/full/{slug}.png

Agentul:
1. fix_broken_images: scrape og:image de pe paginile produs vegis.ro.
2. fetch_deals: TODO via PS feed (adv_id vegis).
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

# Placeholder cunoscut vegis — imagine categorie generica
VEGIS_PLACEHOLDER = "lazy-loader.gif"


class VegisAgent(MerchantAgent):
    slug = "vegis"
    name = "Vegis (produse naturale/bio)"
    default_category = "beauty"

    def _is_placeholder(self, url: str) -> bool:
        return not url or VEGIS_PLACEHOLDER in url or "cdn.vegis.ro/assets" in url

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
            # Accept numai imagini de pe cdn.vegis.ro sau vegis.ro
            if "vegis.ro" not in img:
                return None
            if self._is_placeholder(img):
                return None
            return img
        except Exception:
            return None

    def fix_broken_images(self, broken_deals: list[dict]) -> dict[str, str]:
        """Returneaza {deal_id: new_image_url} pentru fiecare deal reparat."""
        mine = [d for d in broken_deals if d.get("magazin") == self.slug]
        if not mine:
            return {}
        results: dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = {
                ex.submit(self._fetch_og_image, d.get("product_url", "")): d.get("id")
                for d in mine if d.get("product_url")
            }
            for fut in as_completed(futures):
                did = futures[fut]
                img = fut.result()
                if img and did:
                    results[did] = img
            time.sleep(0.1)
        return results

    def fetch_deals(self) -> list[Deal]:
        """Full refresh — TODO via PS feed vegis."""
        return []
