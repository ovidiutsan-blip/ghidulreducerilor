"""StreamStore agent — platforma Gomag, CDN gomagcdn.ro.

Magazin de licente software (Adobe, Autodesk, Microsoft). Platforma Gomag
expune imaginile pe CDN-ul gomagcdn.ro in formatul:
  https://gomagcdn.ro/domains2/streamstore.ro/files/product/{size}/{slug}-{id}.{ext}

unde size in {large, medium, small, thumbnail} si ext in {jpg, png, webp}.

Agentul:
1. fix_broken_images: pentru fiecare deal streamstore cu imagine broken, face GET
   la product page si extrage <meta property="og:image"> (care e pe gomagcdn.ro).
2. fetch_deals: TODO pentru full refresh via PS feed (reuse ps_feed_to_deals logic).
"""
from __future__ import annotations
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

from .base import MerchantAgent, Deal, now_iso


OG_IMAGE = re.compile(
    r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
    re.I,
)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"


class StreamStoreAgent(MerchantAgent):
    slug = "streamstore"
    name = "StreamStore (licente software)"
    default_category = "electronice"

    BASE_CDN = "https://gomagcdn.ro/domains2/streamstore.ro/files/product"

    def _fetch_og_image(self, product_url: str) -> str | None:
        try:
            r = requests.get(
                product_url,
                headers={"User-Agent": UA, "Accept": "text/html"},
                timeout=15, allow_redirects=True,
            )
            if not r.ok:
                return None
            m = OG_IMAGE.search(r.text)
            if not m:
                return None
            img = m.group(1).strip()
            # Gomag returneaza URL absolut pe gomagcdn.ro — accepta doar asta
            if "gomagcdn.ro" not in img:
                return None
            return img
        except Exception:
            return None

    def fix_broken_images(self, broken_deals: list[dict]) -> dict[str, str]:
        """Returns {deal_id: new_image_url} for every successfully fixed deal."""
        streamstore_only = [d for d in broken_deals if d.get("magazin") == self.slug]
        if not streamstore_only:
            return {}

        results: dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=6) as ex:
            futures = {
                ex.submit(self._fetch_og_image, d.get("product_url", "")): d.get("id")
                for d in streamstore_only if d.get("product_url")
            }
            for fut in as_completed(futures):
                did = futures[fut]
                img = fut.result()
                if img and did:
                    results[did] = img
            time.sleep(0.1)  # politeness
        return results

    def fetch_deals(self) -> list[Deal]:
        """Full refresh — delegates to PS feed (streamstore e advertiser 166230)."""
        # Momentan refolosim ps_feed_to_deals pentru full refresh.
        # In viitor, aici vom face scrape direct pe categoriile streamstore.ro.
        return []
