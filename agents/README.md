# Agenți ghidulreducerilor.ro

Director cu agenți automați care rulează săptămânal prin GitHub Actions (`.github/workflows/auto-update-weekly.yml`, duminică 02:00 UTC).

## Data audit

**`scripts/audit_full.py`** — auditul complet, 7 check-uri. Rulează prima și ultima dată la fiecare workflow.

Check-uri relevante pentru imagini (îmbunătățite 2026-04-23):

- **CHECK 4 (Images)** — detectează placeholder-uri: Unsplash, placehold.co, `lazy-loader`, `no-image`, `default.jpg`, etc. Găsește orice imagine care "arată bine la HTTP 200" dar e de fapt un GIF de tranziție.
- **CHECK 4b (Image Hosts Whitelist)** — NOU. Parsează `next.config.js remotePatterns` și verifică că toate host-urile de imagini din `data/deals.json` sunt whitelisted. Un host neautorizat înseamnă HTTP 400 la `/_next/image?url=...` — adică card fără imagine pe site.

Rulare manuală:
```bash
python scripts/audit_full.py --skip-links   # rapid
python scripts/audit_full.py                # cu link-checker (15-30s)
```

Exit code: 0 = clean, non-zero = errors.

## Importeri afiliere

| Platformă | Fișier | Frecvență | Output |
|---|---|---|---|
| Profitshare | `agents/ps_feed_to_deals.py` | săptămânal + on-demand | `data/deals.json` (append + dedupe prin `product_url`) |
| 2Performant | `scripts/check_2performant_feed.py` | săptămânal (dacă credențiale) | `data/deals.json` (append) |

Ambele folosesc același format de deal + imagine din feed. Feed-ul Profitshare returnează imagini pe `profitsmart.ro` (whitelisted). Dacă un feed returnează URL direct de pe CDN-ul magazinului (cum e `cdn.vegis.ro`), host-ul trebuie adăugat în `next.config.js → images.remotePatterns`.

## Fix-uri de imagini

Dacă auditul găsește deal-uri cu imagini placeholder sau host-uri ne-whitelisted, opțiunile de recuperare:

1. **Re-fetch din feed** — dacă produsul mai există în Profitshare, `fix_vegis_images.py` (strategie: match prin product_url / part_number / reconstructed-id).
2. **Scrape `og:image`** — dacă produsul NU mai e în feed, `fix_vegis_via_ogimage.py` face HTTP GET pe pagina produsului, extrage `<meta property="og:image">` din HTML. Concurrency 8 threads, fallback sequential retry pentru 403 rate-limit.

Pattern-ul se aplică la orice magazin. Pentru un magazin nou, duplică `fix_vegis_via_ogimage.py` și schimbă filtrul `magazin == "vegis"`.

## Configurarea credențialelor

GitHub Actions → Settings → Secrets and variables → Actions:

- `PROFITSHARE_API_USER` (secret)
- `PROFITSHARE_API_KEY` (secret)
- `PROFITSHARE_AFFILIATE_ID` (variable)
- `TWO_PERFORMANT_API_USER` (secret, OPTIONAL)
- `TWO_PERFORMANT_API_KEY` (secret, OPTIONAL)
- `BREVO_API_KEY` (secret, pentru newsletter)
- `BREVO_LIST_ID` (variable)

Dacă credențialele 2Performant lipsesc, workflow-ul nu eșuează — pur și simplu skip cu warning în log.

## Verificare post-deploy

După un push pe `main`, Vercel face redeploy automat (~45-60s). Pentru smoke-test:

```bash
# HTTP 200 pe imaginile cheie (vegis, profitsmart, etc.)
curl -s -o /dev/null -w "%{http_code}\n" \
  "https://ghidulreducerilor.ro/_next/image?url=<encoded_image_url>&w=640&q=75"

# HTTP 400 = host blocked (next.config.js bug)
# HTTP 404 = host OK, URL-ul nu există pe CDN
# HTTP 200 = OK
```

## Problemele rezolvate 2026-04-23

- 103 deal-uri vegis aveau `image = cdn.vegis.ro/.../lazy-loader.gif` (placeholder). Fix: scrape `og:image` de pe paginile produs.
- `cdn.vegis.ro` nu era whitelisted în `next.config.js` → Next/Image returna HTTP 400. Fix: adăugat la `remotePatterns`.
- `audit_images()` nu detecta `lazy-loader` ca placeholder → îmbunătățit.
- Check nou: `audit_image_hosts()` validează că toate host-urile sunt whitelisted.

## Probleme deschise (detectate de audit)

- 3 magazine "active" fără deal-uri: FashionDays, Elefant.ro, evoMAG (pending aprobare 2P sau feed gol).
- 32 deal-uri novodoors cu IDs duplicate — necesită sprint de-dedup.
