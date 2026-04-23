"""Mathaus agent — magazin scule/unelte, protejat CloudFlare.

Platforma: Magento/custom cu CloudFlare WAF — blocheaza requests() simplu.
Solutie: Playwright headless Chromium (browser real = bypass CF challenge).

Imagini: https://mathaus.ro/media/catalog/product/{a}/{b}/{slug}.jpg
  sau profitsmart.ro (= broken, trebuie fixed)

Agentul:
1. fix_broken_images: Playwright scrape og:image/img src pe mathaus.ro.
2. fetch_deals: TODO via PS feed mathaus.

Prerequisit:
  pip install playwright
  python -m playwright install chromium
"""
from __future__ import annotations
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from .base import MerchantAgent, Deal

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

OG_RE = re.compile(
    r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']'
    r'|content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
    re.I,
)

MATHAUS_HOSTS = ("mathaus.ro", "media.mathaus.ro")


def _try_playwright(url: str) -> Optional[str]:
    """Deschide URL in Chromium headless si extrage imaginea produsului."""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            ctx = browser.new_context(
                user_agent=UA,
                viewport={"width": 1280, "height": 800},
                locale="ro-RO",
            )
            page = ctx.new_page()
            # Blocheaza resurse inutile (accelereaza)
            page.route("**/*.{woff,woff2,ttf,mp4,svg}", lambda r: r.abort())
            try:
                page.goto(url, timeout=25000, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)  # CF challenge poate dura 1-2s
            except PWTimeout:
                browser.close()
                return None

            html = page.content()
            browser.close()

        # og:image
        m = OG_RE.search(html)
        if m:
            img = (m.group(1) or m.group(2) or "").strip()
            if img and any(h in img for h in MATHAUS_HOSTS):
                return img

        # Fallback: prima imagine din media/catalog/product
        imgs = re.findall(
            r'https?://(?:mathaus\.ro|media\.mathaus\.ro)/media/catalog/product/'
            r'[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)',
            html, re.I,
        )
        imgs_unique = list(dict.fromkeys(imgs))
        # Prefera imagini full-size (fara /cache/ sau /thumbnail/)
        for img in imgs_unique:
            if "/cache/" not in img and "/thumbnail/" not in img:
                return img
        if imgs_unique:
            return imgs_unique[0]

        return None
    except Exception:
        return None


class MathausAgent(MerchantAgent):
    slug = "mathaus"
    name = "Mathaus (scule/unelte)"
    default_category = "casa-gradina"

    def fix_broken_images(self, broken_deals: list[dict]) -> dict[str, str]:
        mine = [d for d in broken_deals if d.get("magazin") == self.slug]
        if not mine:
            return {}
        results: dict[str, str] = {}
        # CloudFlare = nu parallelizam agresiv; max 3 browsere simultan
        with ThreadPoolExecutor(max_workers=3) as ex:
            futures = {
                ex.submit(_try_playwright, d.get("product_url", "")): d.get("id")
                for d in mine if d.get("product_url")
            }
            for fut in as_completed(futures):
                did = futures[fut]
                img = fut.result()
                if img and did:
                    results[did] = img
                time.sleep(0.3)  # polite delay intre browsere
        return results

    def fetch_deals(self) -> list[Deal]:
        """Full refresh — TODO via PS feed mathaus (adv cu CloudFlare = Playwright necesar)."""
        return []
