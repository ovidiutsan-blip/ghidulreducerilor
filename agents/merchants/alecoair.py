"""Alecoair agent — magazin aparate climatizare/purificare aer.

Platforma: custom PHP (alecoair.ro). NU expune og:image.
Imagini produs: https://alecoair.ro/assets/produse/{filename}.jpg  (full-size)
               https://alecoair.ro/assets/produse/thumbs/{filename}_thumb.jpg (thumbnail - exclus)

Bug cunoscut: scraperul PS a capturat placeholder-ul de categorie
  https://alecoair.ro/assets/category/aparate_de_masura_1.jpg
  in loc de imaginea reala a produsului (toti 45 de deal-uri).

Strategie: scrape prima imagine src=/assets/produse/ (fara /thumbs/) din pagina produs.

Agentul:
1. fix_broken_images: detecteaza placeholder si extrage imaginea reala.
2. fetch_deals: TODO via PS feed alecoair.
"""
from __future__ import annotations
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from .base import MerchantAgent, Deal

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"

# Placeholder-uri cunoscute alecoair
ALECOAIR_PLACEHOLDERS = (
    "assets/category/",
    "no-image",
    "default.",
    "placeholder",
)

# Pattern: /assets/produse/ dar NU /thumbs/
_PRODUSE_RE = re.compile(
    r'(?:src|data-src)=["\']'
    r'(https?://alecoair\.ro/assets/produse/(?!thumbs/)[^"\'<>\s]+\.(?:jpg|jpeg|png|webp))'
    r'["\']',
    re.I,
)


class AlecoAirAgent(MerchantAgent):
    slug = "alecoair"
    name = "AlecoAir (aparate clima/purificare)"
    default_category = "casa-gradina"

    def _is_placeholder(self, url: str) -> bool:
        if not url:
            return True
        url_lower = url.lower()
        return any(p in url_lower for p in ALECOAIR_PLACEHOLDERS)

    def _fetch_product_image(self, product_url: str) -> str | None:
        try:
            r = requests.get(
                product_url,
                headers={"User-Agent": UA, "Accept": "text/html"},
                timeout=15, allow_redirects=True,
            )
            if not r.ok:
                return None
            # Prima imagine reala (non-thumb) din /assets/produse/
            matches = _PRODUSE_RE.findall(r.text)
            if not matches:
                return None
            img = matches[0].strip()
            if self._is_placeholder(img):
                return None
            return img
        except Exception:
            return None

    def fix_broken_images(self, broken_deals: list[dict]) -> dict[str, str]:
        """Repara imaginile placeholder cu imaginea reala din pagina produs."""
        mine = [d for d in broken_deals if d.get("magazin") == self.slug]
        if not mine:
            return {}
        results: dict[str, str] = {}
        # Concurrency moderata — site fara rate-limiting evident
        with ThreadPoolExecutor(max_workers=6) as ex:
            futures = {
                ex.submit(self._fetch_product_image, d.get("product_url", "")): d.get("id")
                for d in mine if d.get("product_url")
            }
            for fut in as_completed(futures):
                did = futures[fut]
                img = fut.result()
                if img and did:
                    results[did] = img
            time.sleep(0.1)
        return results

    def get_broken_deals(self, all_deals: list[dict]) -> list[dict]:
        """Extinde definitia 'broken' sa includa si placeholder-ul de categorie."""
        return [
            d for d in all_deals
            if d.get("magazin") == self.slug
            and (
                "profitsmart.ro" in (d.get("image") or "")
                or not d.get("image")
                or self._is_placeholder(d.get("image") or "")
            )
        ]

    def fetch_deals(self) -> list[Deal]:
        """Full refresh — TODO via PS feed alecoair."""
        return []
