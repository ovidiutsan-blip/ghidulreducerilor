"""Per-merchant agents for ghidulreducerilor.ro.

Each merchant has its own module with logic specific to that platform:
- Gomag (hiris) -> Gomag CDN + og:image
- Custom PHP (alecoair, hotpick) -> data-src scanning
- CloudFlare-protected (mathaus) -> Playwright with stealth
- PS feed (vegis, novodoors) -> feed + og:image fallback
- Proprietary (streamstore, watch24, emag) -> platform-specific logic

Orchestrator runs them sequentially and merges into data/deals.json.
"""
