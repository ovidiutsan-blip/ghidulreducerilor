# Ghid Monetizare — Profitshare.ro

## Cum funcționează

1. Utilizatorul vine pe GhidulReducerilor.ro (de pe TikTok, Google, etc.)
2. Vede o reducere și dă click pe "Vezi oferta" sau "Copiază + Cumpără"
3. Este redirecționat pe site-ul magazinului prin link-ul Profitshare
4. Dacă cumpără ceva, tu primești un comision (2-15% din valoarea comenzii)

## Pași pentru a genera linkuri Profitshare

### 1. Creează cont pe Profitshare.ro
- Mergi pe [profitshare.ro](https://www.profitshare.ro) și creează un cont de afiliat
- Completează datele site-ului (ghidulreducerilor.ro)
- Așteaptă aprobarea (1-3 zile lucrătoare)

### 2. Aplică la programele magazinelor
- Din dashboard Profitshare, mergi la "Programe" sau "Advertiseri"
- Aplică la programele eMAG, Altex, Fashion Days, etc.
- Fiecare magazin trebuie să te aprobe individual

### 3. Generează linkuri de afiliere
- După aprobare, mergi la programul magazinului
- Folosește "Generator de linkuri" din dashboard
- Lipește URL-ul produsului sau al paginii de pe site-ul magazinului
- Profitshare generează un link unic de tracking (ex: `https://www.profitshare.ro/l/12345`)
- Copiază acest link și adaugă-l în `data/deals.json` în câmpul `link_afiliat`

### 4. Adaugă ID-ul de afiliat
- Din dashboard Profitshare, copiază ID-ul tău de afiliat
- Adaugă-l în `.env.local`: `NEXT_PUBLIC_PROFITSHARE_AFFILIATE_ID=id-ul-tau`
- Înlocuiește `YOUR_ID` din linkurile placeholder cu ID-ul real

## Comisioane tipice

| Magazin       | Comision mediu | Observații                          |
|---------------|----------------|-------------------------------------|
| eMAG          | 3-8%           | Variază pe categorii                |
| Altex         | 2-6%           | Electrocasnice mai mult, IT mai puțin |
| Fashion Days  | 5-15%          | Fashion are cele mai mari comisioane |

## Tips pentru maximizarea veniturilor

1. **Promovează produse scumpe** — 5% din 5000 lei = 250 lei comision
2. **Fashion are comisioane mari** — Focus pe Fashion Days și branduri de modă
3. **Codurile promo convertesc bine** — Oamenii care caută coduri sunt gata să cumpere
4. **TikTok + Flash deals** — Postează reducerile cu termen limitat pe TikTok pentru urgență
5. **SEO pe long-tail** — "cod promo emag [luna] [an]" are trafic constant

## Tracking și rapoarte

- Dashboard Profitshare arată click-uri, conversii și comisioane
- Comisioanele sunt validate de magazin (30-90 zile)
- Plata se face lunar, după atingerea pragului minim
