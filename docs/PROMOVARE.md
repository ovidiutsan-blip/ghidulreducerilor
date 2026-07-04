# Plan de promovare faceless — ghidulreducerilor.ro

> Actualizat: 2026-07-04. Toată promovarea e „faceless": conținut de brand generat
> automat din `data/deals.json`, fără prezență personală pe cameră.

## 1. Starea canalelor

| Canal | Stare | Cadență | Mecanism |
|---|---|---|---|
| **Facebook** (pagină) | 🟢 LIVE | 3×/zi (09:23, 14:23 L-V, 20:23 RO) | `social-media.yml` → `scripts/social_media_poster.py` |
| **Instagram** @ghidulreducerilor.ro | 🟢 LIVE | 3×/zi, aceleași ore | același script (fix 04.07: polling container + retry) |
| **Telegram** @ghidulreducerilor | 🟢 LIVE | 5 deals/zi, dimineața | `agents/marketing/telegram_agent.py` |
| **Newsletter** (Brevo) | 🟢 LIVE | vineri | `newsletter.yml` |
| **Blog SEO** | 🟢 LIVE | articol auto/săptămână | `weekly-blog.yml` → `scripts/generate_weekly_blog.py` |
| **Google/Bing indexare** | 🟢 LIVE | zilnic după pipeline | sitemap + IndexNow (`scripts/indexnow_ping.py`) + GSC verificat |
| **Grupuri Facebook** | 🟡 SEMI | zilnic pe email | orchestratorul trimite posturi gata de copiat (Brevo digest) |
| **Pinterest** | 🔴 ADORMIT | — | agent gata scris, cere cont + login local (vezi §3) |
| **TikTok** | 🔴 ADORMIT | — | agent gata scris (carduri 9:16 + upload), cere login local (vezi §4) |

## 2. Principii (nu le schimba fără motiv)

- Fiecare post duce la `/out/{deal-id}` (link afiliat monetizat) sau la o pagină de magazin.
- Doar deals verificate live (validatorul respinge notoolerror/404) — niciodată link mort în social.
- Cron-urile stau la minutul `:23` — la `:00` GitHub întârzie/sare rulările.
- Sesiunea de postare se derivă din `github.event.schedule`, nu din ora curentă.

## 3. Activare Pinterest (recomandat #1 — trafic evergreen pe nișa deals/casă)

Pinterest e cel mai potrivit canal faceless pentru acest site: pin-urile trăiesc luni de zile,
nișa casă/grădină/beauty performează, iar `sameAs` din schema Organization deja declară contul.

Pași (o singură dată, ~20 min, cere contul tău):
1. Creează cont **business** `pinterest.com/ghidulreducerilor`.
2. Revendică domeniul ghidulreducerilor.ro (Settings → Claimed accounts — meta tag în `app/layout.tsx`).
3. Creează board-urile din `BOARD_MAP` (`agents/marketing/pinterest_agent.py`).
4. Local: `python agents/marketing/pinterest_agent.py --setup` apoi `--login` (o dată).
5. Programează zilnic în Task Scheduler: `python agents/marketing/pinterest_agent.py --run` (3-5 pin-uri/zi).

## 4. Activare TikTok (recomandat #2 — reach organic, zero buget)

Agentul generează carduri foto 9:16 (Pillow, branding site) și le urcă drept photo-post/carusel.
1. Local: `python agents/marketing/tiktok_agent.py --login` (o dată, cont @ghidulreducerilor).
2. Test: `--dry-run` (generează cardurile în `data/marketing/tiktok_cards/` fără upload).
3. Programează zilnic: `--run` (max 3 posturi/zi, min 30% reducere).

## 5. Idei următoare (neimplementate)

- **YouTube Shorts faceless**: video 15s din cardurile TikTok (imagine + zoom + text overlay) — cere pipeline de randare video.
- **Grupuri FB automatizat**: interzis de ToS Meta — rămâne semi-manual din digestul zilnic.
- **Google Discover**: articolele săptămânale + imagini mari (≥1200px) în blog cresc șansa de includere.
- Dacă Pinterest/TikTok nu se activează, scoate-le din `sameAs` (`app/layout.tsx`) ca să nu declari conturi inexistente.

## 6. Monitorizare

- Rulările: `gh run list --workflow=social-media.yml`.
- Performanță click-uri: `agents/marketing/performance_agent.py` (raport în digestul zilnic).
- GA4 e live în producție din 04.07; GSC verificat — de submis sitemap-ul o dată, manual.
