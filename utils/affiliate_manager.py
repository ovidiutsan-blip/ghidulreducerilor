"""
Affiliate Link Manager — ghidulreducerilor.ro
Gestionează linkurile de afiliere pentru 2Performant și Profitshare
"""

import json
import os
from urllib.parse import urlencode

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "affiliate_links.json")


class AffiliateManager:
    def __init__(self):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def get_2performant_link(self, affiliate_id: str, campaign_id: str, target_url: str) -> str:
        """Generează link de tracking 2Performant"""
        params = {
            "aff_id": affiliate_id,
            "campaign_id": campaign_id,
            "aff_click_id": "",
            "redirect": target_url
        }
        base = "https://event.2performant.com/events/click"
        return f"{base}?{urlencode(params)}"

    def get_profitshare_link(self, campaign_id: str, target_url: str) -> str:
        """Generează link de tracking Profitshare"""
        params = {
            "campaign_id": campaign_id,
            "redirect": target_url
        }
        base = "https://event.profitshare.ro/click"
        return f"{base}?{urlencode(params)}"

    def get_link(self, magazine: str, subcategorie: str = None) -> str:
        """Returnează link-ul de afiliere pentru un magazin și subcategorie"""
        if magazine not in self.config:
            raise ValueError(f"Magazin necunoscut: {magazine}")

        mag = self.config[magazine]

        if subcategorie and subcategorie in mag.get("subcategories", {}):
            return mag["subcategories"][subcategorie]

        return mag.get("base_url", "#")

    def is_approved(self, magazine: str) -> bool:
        """Verifică dacă un magazin are ID-uri de afiliere completate"""
        mag = self.config.get(magazine, {})
        return mag.get("affiliate_id", "COMPLETEAZĂ_DUPĂ_APROBARE") != "COMPLETEAZĂ_DUPĂ_APROBARE"


if __name__ == "__main__":
    manager = AffiliateManager()
    for mag in ["notino", "answear", "decathlon", "cel", "pcgarage", "dr_max"]:
        approved = manager.is_approved(mag)
        print(f"{mag:15} — {'✅ Aprobat' if approved else '⏳ În așteptare'}")
