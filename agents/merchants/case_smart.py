"""Case-smart agent — platforma WordPress/WooCommerce.

Imaginile sunt pe case-smart.ro/wp-content/uploads/{year}/{month}/{filename}.jpg
og:image expune URL-ul full-size; listarea afiseaza thumbnail -400x400.
"""
from __future__ import annotations
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from .base import MerchantAgent, Deal

OG = re.compile(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', re.I)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"


class CaseSmartAgent(MerchantAgent):
    slug = "case-smart"
    name = "Case-smart (domotica/smart home)"
    default_category = "casa-gradina"

    def _fetch_og_image(self, product_url: str) -> str | None:
        try:
            r = requests.get(product_url, headers={"User-Agent": UA}, timeout=15, allow_redirects=True)
            if not r.ok: return None
            m = OG.search(r.text)
            if not m: return None
            img = m.group(1).strip()
            # Accept only case-smart.ro images (exclude social share hotlinks)
            if "case-smart.ro" not in img: return None
            return img
        except Exception:
            return None

    def fix_broken_images(self, broken_deals: list[dict]) -> dict[str, str]:
        mine = [d for d in broken_deals if d.get("magazin") == self.slug]
        if not mine: return {}
        results: dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=6) as ex:
            futures = {ex.submit(self._fetch_og_image, d.get("product_url", "")): d.get("id") for d in mine if d.get("product_url")}
            for fut in as_completed(futures):
                did = futures[fut]
                img = fut.result()
                if img and did: results[did] = img
        return results

    def fetch_deals(self) -> list[Deal]:
        return []  # TODO: PS feed refresh (adv_id 111470)
