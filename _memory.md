# [GhidulReducerilor.ro](http://GhidulReducerilor.ro) — Memorie sesiuni

## Ultimul commit: 622265f (2026-04-24)

### Commits recente

- `622265f` feat: merchant scan lunar
- `113ccdd` feat: cross-platform dedup PS+2P
- `cb920e4` chore: archive dead code
- `7733c57` feat: deal expiry + image fix + token monitor

### Pipeline auto_update.py

```
Step 0  → check_token_expiry.py (2P pre-flight)
Step 1  → audit_full.py
Step 2  → auto_repair.py
Step 2b → merchants/run.py all --fix-images
Step 3  → ps_feed_to_deals.py (add + expire)
Step 3b → two_performant_to_deals.py (add + expire)
Step 3d → dedup_cross_platform.py  ← adaugat 2026-04-24
Step 3c → generate_profitshare_links.py
Step 4  → link_checker.py
```

### Fișiere cheie

- `agents/ps_feed_to_deals.py` — import PS
- `agents/two_performant_to_deals.py` — import 2P
- `scripts/auto_update.py` — orchestrator principal
- `scripts/dedup_cross_platform.py` — dedup activ-duplicate pe product_url
- `scripts/merchant_scan.py` — discovery lunar merchantii noi
- `scripts/check_token_expiry.py` — monitor token 2P (\~14 zile)
- `agents/ps_merchants.json` — 9 merchantii PS activi
- `agents/2p_merchants.json` — 4 merchantii 2P activi
- `.github/workflows/merchant-scan-monthly.yml` — rulează pe 1 ale lunii

### Fix important (2026-04-24)

`existing_urls` în ambii importeri acum filtrează doar dealuri ACTIVE. Dealurile expirate nu mai blochează re-importul din altă sursă.

### Taskuri viitoare (backlog)

- Push to GitHub (git push origin main)
- Test merchant_scan.py local cu credentiale reale
- Adaugă merchantii noi găsiți de scan în ps/2p_merchants.json
