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
| **Pinterest** @ovidiutsan | 🟡 ACTIV manual | seed 04.07: 3 board-uri + 3 pin-uri | domeniu revendicat; pt. zilnic: agent local (vezi §3) |
| **TikTok** | 🔴 INEXISTENT | — | contul @ghidulreducerilor NU există; scos din sameAs (vezi §4) |

## 2. Principii (nu le schimba fără motiv)

- Fiecare post duce la `/out/{deal-id}` (link afiliat monetizat) sau la o pagină de magazin.
- Doar deals verificate live (validatorul respinge notoolerror/404) — niciodată link mort în social.
- Cron-urile stau la minutul `:23` — la `:00` GitHub întârzie/sare rulările.
- Sesiunea de postare se derivă din `github.event.schedule`, nu din ora curentă.

## 3. Pinterest — stare 04.07.2026 (setup făcut)

Cont business existent: **GhidulReducerilor.ro / @ovidiutsan** (`pinterest.com/ovidiutsan`).
Făcut pe 04.07: domeniul ghidulreducerilor.ro **revendicat** (meta `p:domain_verify` în
`app/layout.tsx`), 4 board-uri create + 4 pin-uri seed publicate (carduri 2:3 din
`public/pins/`):
- „Casă și Grădină — Reduceri", „Oferte Zilei — România", „Sănătate & Farmacie — Oferte",
  „Electronice — Reduceri România"
- numele corespund exact `BOARD_MAP` din `agents/marketing/pinterest_agent.py`; toate cele
  5 categorii reale din `deals.json` (casa-gradina, promotii, farmacie-sanatate, electronice,
  suplimente-bio) mapează acum pe board-uri care EXISTĂ pe cont

Pentru postare ZILNICĂ automată rămâne un pas local (agentul are browser profile propriu):
1. `python agents/marketing/pinterest_agent.py --setup` apoi `--login` (o dată).
2. Task Scheduler zilnic: `python agents/marketing/pinterest_agent.py --run` (3-5 pin-uri/zi).

## 4. TikTok — contul NU există (verificat 04.07.2026)

`tiktok.com/@ghidulreducerilor` returnează "Couldn't find this account" → scos din `sameAs`.
Crearea contului cere acțiunea proprietarului (verificare email/telefon). Dacă îl creezi:
1. Re-adaugă URL-ul în `sameAs` (`app/layout.tsx`).
2. `python agents/marketing/tiktok_agent.py --login` o dată, apoi `--run` zilnic
   (generează carduri 9:16 și le urcă drept photo-post; max 3/zi, min 30% reducere).

## 5. Idei următoare (neimplementate)

- **YouTube Shorts faceless**: video 15s din cardurile TikTok (imagine + zoom + text overlay) — cere pipeline de randare video.
- **Grupuri FB automatizat**: interzis de ToS Meta — rămâne semi-manual din digestul zilnic.
- **Google Discover**: articolele săptămânale + imagini mari (≥1200px) în blog cresc șansa de includere.
- Dacă Pinterest/TikTok nu se activează, scoate-le din `sameAs` (`app/layout.tsx`) ca să nu declari conturi inexistente.

## 6. Monitorizare

- Rulările: `gh run list --workflow=social-media.yml`.
- Performanță click-uri: `agents/marketing/performance_agent.py` (raport în digestul zilnic).
- GA4 e live în producție din 04.07; GSC verificat — de submis sitemap-ul o dată, manual.
