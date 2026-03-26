# GhidulReducerilor.ro

Site de reduceri și coduri promoționale din România, monetizat prin afiliere Profitshare.ro.

## Tehnologie

- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS
- **Date:** Fișiere JSON statice (`data/`)
- **Email:** API Brevo (fostul Sendinblue)
- **Deploy:** Vercel (gratuit)

## Setup rapid

```bash
# 1. Instalează dependențele
npm install

# 2. Copiază fișierul de configurare
cp .env.example .env.local

# 3. Editează .env.local cu datele tale (Profitshare ID, Brevo API key)

# 4. Pornește serverul de development
npm run dev
```

Site-ul va fi disponibil la `http://localhost:3000`.

## Cum adaugi o reducere nouă

1. Deschide `data/deals.json`
2. Adaugă un obiect nou la final:

```json
{
  "id": "emag-005",
  "magazin": "emag",
  "titlu": "Numele produsului",
  "imagine_url": "https://link-imagine.jpg",
  "pret_original": 999.00,
  "pret_redus": 699.00,
  "procent_reducere": 30,
  "link_afiliat": "https://www.profitshare.ro/l/XXXX?affiliate_id=YOUR_ID",
  "categorie": "electronice",
  "data_adaugare": "2026-03-26",
  "activ": true
}
```

3. Salvează fișierul și push pe GitHub → Vercel rebuild-uiește automat

## Cum adaugi un cod promoțional

1. Deschide `data/codes.json`
2. Adaugă un obiect nou:

```json
{
  "id": "code-emag-003",
  "magazin": "emag",
  "cod": "CODUL",
  "descriere": "Descriere reducere",
  "valoare": "10%",
  "tip": "procent",
  "data_expirare": "2026-12-31",
  "link_afiliat": "https://www.profitshare.ro/l/XXXX?affiliate_id=YOUR_ID",
  "verificat": true
}
```

## Cum adaugi un magazin nou

1. Adaugă magazinul în `data/stores.json`
2. Adaugă produse/coduri în `deals.json` / `codes.json` cu același `magazin` slug
3. Paginile `/reduceri/[slug]` și `/coduri-promo/[slug]` se generează automat

## Deploy pe Vercel

1. Creează cont pe [vercel.com](https://vercel.com)
2. Conectează repository-ul GitHub
3. Adaugă variabilele de mediu din `.env.example` în Settings > Environment Variables
4. Deploy automat la fiecare push pe `main`

## Structura proiectului

```
app/                    → Pagini Next.js (App Router)
  layout.tsx            → Layout global (navbar + footer)
  page.tsx              → Homepage
  reduceri/[magazin]/   → Pagini per magazin
  coduri-promo/[magazin]/ → Pagini coduri promo
  api/subscribe/        → API endpoint pentru Brevo
components/             → Componente React reutilizabile
data/                   → JSON-uri cu reduceri, coduri, magazine
lib/                    → Utilități (formatare prețuri, date, etc.)
public/                 → Assets statice (manifest, icons)
```
