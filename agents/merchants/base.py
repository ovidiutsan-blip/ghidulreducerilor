"""Base interface for merchant agents.

Every agent implements `MerchantAgent` with two operations:
1. fetch_deals() -> list[Deal]              # full refresh from source
2. fix_broken_images(deals) -> list[Deal]   # update image for existing deals

The orchestrator runs each agent, applies results to data/deals.json,
and writes a per-agent log into logs/agent-{slug}.log.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass
class Deal:
    """Canonical deal shape. Matches data/deals.json schema."""
    id: str
    slug: str
    magazin: str
    titlu: str
    image: str
    product_url: str
    link_afiliat: str
    pret_original: float
    pret_redus: float
    procent_reducere: int
    categorie: str
    activ: bool = True
    data_adaugare: str = field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
    # Optional metadata
    titlu_original: str | None = None
    descriere: str | None = None
    image_fixed_at: str | None = None
    image_fix_source: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if v is not None}
        # Duplicate fields that the TS consumer reads (legacy aliases)
        d["title"] = self.titlu
        d["store"] = self.magazin
        d["imagine_url"] = self.image
        d["description"] = self.descriere or ""
        d["price"] = self.pret_redus
        d["originalPrice"] = self.pret_original
        d["discount_percent"] = self.procent_reducere
        d["affiliate_url"] = self.link_afiliat
        d["url"] = self.product_url
        d["categories"] = [self.categorie]
        d["is_active"] = self.activ
        # Flatten extra
        extra = d.pop("extra", {})
        d.update(extra)
        return d


@dataclass
class AgentResult:
    """Outcome of one agent run."""
    magazin: str
    deals_added: int = 0
    deals_updated: int = 0
    images_fixed: int = 0
    deals_disabled: int = 0
    errors: list[str] = field(default_factory=list)
    duration_s: float = 0.0

    def summary(self) -> str:
        return (f"[{self.magazin}] +{self.deals_added} new, "
                f"~{self.deals_updated} updated, "
                f"img {self.images_fixed}, "
                f"disabled {self.deals_disabled}, "
                f"err {len(self.errors)}, "
                f"{self.duration_s:.1f}s")


class MerchantAgent(ABC):
    """Abstract base. Each concrete agent implements one or both methods."""

    #: machine-friendly slug (used as magazin field in deals.json)
    slug: str = ""
    #: human-readable name for logs
    name: str = ""
    #: default category (can be overridden per-deal)
    default_category: str = ""

    @abstractmethod
    def fetch_deals(self) -> list[Deal]:
        """Full refresh: pull current deals from source."""
        raise NotImplementedError

    def fix_broken_images(self, broken_deals: list[dict]) -> dict[str, str]:
        """Given list of deal dicts with broken images, return {deal_id: new_image_url}.
        Default: no-op. Agents override with platform-specific image extraction.
        """
        return {}


def now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
