# Strategie de promovare GRATUITĂ — Facebook personal + alte canale

**Site:** ghidulreducerilor.ro · **Obiectiv:** trafic gratuit → click pe deal-uri care produc comision.
**Ultima actualizare:** 2026-07-08

---

## 0. Principiul de bază (de ce profilul personal > pagina)

Pagina de Facebook e gâtuită de algoritm: o postare organică ajunge la ~2–5% din fani.
**Profilul personal ajunge la aproape toți prietenii tăi** — de 10–20× mai mult reach gratuit.

Dar are un cost ascuns: dacă spamezi prietenii cu reclame, te dau **mute / unfollow / unfriend**
și pierzi canalul pentru totdeauna. Deci regula de aur:

> **Postezi ca un prieten care a găsit un chilipir, NU ca un magazin care vinde.**

---

## 1. Cele 5 tactici care fac diferența pe profilul personal

| # | Tactica | De ce contează |
|---|---------|----------------|
| 1 | **Link în primul comentariu, nu în postare** | Facebook reduce reach-ul postărilor cu link extern în corp. Postare fără link + link în primul comentariu = reach păstrat. |
| 2 | **Poză nativă a produsului** | Postările cu imagine urcată direct (nu preview de link) primesc de câteva ori mai multă expunere. |
| 3 | **Ton personal, prima persoană** | „Am dat peste asta…" merge; „Reducere -70% la X!" e reclamă și e ignorată. |
| 4 | **Max 2–3 postări/zi, la interval** | Peste asta, prietenii te percep ca spam. Rar și de calitate > des și enervant. |
| 5 | **Răspunzi la comentarii** | Fiecare comentariu/răspuns e semnal pozitiv → algoritmul arată postarea la mai mulți. |

---

## 2. Tool-ul care face munca (generator de postări)

Ai deja scriptul: `agents/marketing/personal_fb_generator.py`.

```bash
# 5 postări gata de copy-paste, doar deal-uri care produc comision, sub 400 lei
python agents/marketing/personal_fb_generator.py --count 5

# alt plafon de preț sau reia de la capat
python agents/marketing/personal_fb_generator.py --count 3 --max-price 250
python agents/marketing/personal_fb_generator.py --reset
```

Rezultatul: `data/marketing/fb_personal_2026-MM-DD.md` cu, pentru fiecare deal:
- textul **POSTARE** (fără link, ton personal, preț verificat)
- textul **PRIMUL COMENTARIU** (cu linkul spre site, cu UTM de tracking)
- URL-ul pozei produsului (o urci manual)

Ce garantează tool-ul:
- **Doar deal-uri care aduc bani** — sare peste linkurile brute evomag.ro / vegis.ro (zero comision).
- **Nu repetă** deal-uri de la o zi la alta (log local `fb_personal_log.json`).
- **Rotește magazinele** ca feed-ul tău să pară variat, nu monoton.
- **Link către SITE, nu link afiliat direct** — construiește brandul, e de încredere pentru prieteni, iar site-ul gestionează afilierea prin `/out/[id]`.

**Rutina zilnică (3 minute):** rulezi scriptul dimineața → deschizi .md → postezi 2 dintre ele la ore diferite, cu poză + link în primul comentariu.

---

## 3. Idei de conținut care NU par reclamă

Alternează formatele ca să nu devii previzibil:

1. **Chilipirul zilei** — un singur produs bun, poză, preț, „merită?". (baza, generată de tool)
2. **Întrebare deschisă** — „Vreau un aspirator vertical bun sub 500 lei, m-am uitat la astea 3, voi ce aveți?" (invită comentarii → reach uriaș).
3. **Sezonier** — acum e vară: aer condiționat, ventilatoare, grădină, plajă, protecție solară. Din categoria ta forte **casă & grădină (678 deal-uri)** ai muniție.
4. **Cadouri** — „Se apropie [ocazie], idei sub 100 lei". Grupuri de idei, nu un singur link.
5. **Story-uri Facebook / Instagram** — efemere (24h), percepute mult mai puțin ca spam. Perfect pentru „chilipir rapid" zilnic. Pui sticker cu link.
6. **Câștig personal** — „Am luat X de aici, sunt super mulțumit" (dacă chiar ai cumpărat). Autenticitatea vinde.
7. **Comparație/economie** — „Ăsta era 320, acum 89. Am verificat prețul minim pe 30 zile, e real." (diferențiere: tu verifici, nu umfli).

---

## 4. Grupuri Facebook — unde share-ul e BINEVENIT (nu spam)

Pe profil ești discret; în grupurile de chilipiruri ești exact ce caută lumea. Reguli:
citește regulamentul fiecărui grup, nu posta același text în 5 grupuri deodată (FB îl marchează
spam), variază, fii activ (comentează la alții), nu doar arunca linkuri.

Tipuri de grupuri de căutat (căutare FB: „reduceri", „chilipiruri", „oferte", + nișă):
- Grupuri generale de reduceri/chilipiruri România (zeci de mii de membri).
- **Grupuri de nișă pe categoria ta forte**: „amenajări casă", „grădinărit", „decorațiuni interioare", „mămici" (produse casă/copii), „bricolaj/scule" (ai scule365).
- Grupuri locale (orașul tău) — comunitate mai caldă, mai puțin saturată.

Ținta realistă: **3–5 grupuri bune** în care ești membru activ > 20 de grupuri în care doar spamezi.

---

## 5. Alte canale gratuite (planul complet, dincolo de FB)

| Canal | Efort | Ce faci | Status |
|-------|-------|---------|--------|
| **FB profil personal** | mic zilnic | 2 postări/zi din generator | ← focusul acum |
| **FB grupuri** | mic | 3–5 grupuri, deal relevant pe nișă | de intrat |
| **Instagram Stories** | mic | chilipir zilnic, sticker link | cont live deja |
| **Telegram** | zero | deja postează automat | ✅ automat |
| **Pinterest** | zero | deja postează automat | ✅ automat |
| **WhatsApp status** | mic | 1 chilipir/zi pe status (nu în grupuri family fără voie) | de pornit |
| **Reddit** (r/Romania, r/cumparaturi) | mediu | NU spam — răspunzi util la „unde găsesc X ieftin", cu link contextual | opțional |
| **Google/SEO** | zero | blog + sitemap automat | ✅ automat |

---

## 6. Plan concret pe o săptămână

| Zi | Profil personal | Grupuri | Story |
|----|-----------------|---------|-------|
| Luni | 1× chilipir (casă) | 1× grup casă | 1× |
| Marți | 1× întrebare deschisă | — | 1× |
| Miercuri | 1× chilipir (sezonier) | 1× grup nișă | 1× |
| Joi | 1× chilipir (scule/beauty) | — | 1× |
| Vineri | 1× „weekend deals" (2-3 produse) | 1× grup general | 1× |
| Sâmbătă | 1× cadou/idee | — | 1× |
| Duminică | pauză / doar story | — | 1× |

Total: ~6 postări profil + 3 grupuri + story zilnic = sub 20 min/zi, 100% gratuit.

---

## 7. Măsurare — vezi dacă merită efortul

Linkurile din generator au deja `?utm_source=facebook&utm_medium=personal`.
În **Google Analytics 4** → Acquisition → Traffic acquisition, filtrezi `facebook / personal`
și vezi câți vizitatori + câte click-uri pe deal-uri au venit din efortul tău.
Dacă un tip de postare aduce mult → faci mai mult din el.

---

## 8. Ce să NU faci (ca să nu strici canalul)

- ❌ Nu automatiza postarea pe profilul personal (interzis de FB → ban de cont).
- ❌ Nu pune linkul afiliat brut direct pe FB (îl marchează / arată neîncredere). Link spre site.
- ❌ Nu posta același text în multe grupuri simultan.
- ❌ Nu umfla reducerile — reputația de „el chiar verifică prețul" e cel mai valoros activ.
- ❌ Nu depăși 2–3 postări/zi pe profil.

---

## Anexă: task de monetizare descoperit (de rezolvat separat)

La analiza deal-urilor am găsit **136 de deal-uri cu link brut (zero comision)**:
- **vegis: 101 deal-uri** cu link `vegis.ro` direct, deși vegis E pe Profitshare (`adv_id 58221`).
  Sunt legacy dinainte de migrarea pe feed-ul PS. Fix: regenerare deeplink Profitshare
  sau dezactivarea celor care nu mai sunt în feed.
- **evomag: 35 deal-uri** cu link `evomag.ro` direct — evomag e „orphan", posibil neafiliat.
  De verificat dacă există pe vreo rețea; dacă nu, de deprioritizat.

Generatorul de FB le evită deja, dar merită rezolvat ca traficul organic de pe site
(unde apar aceste deal-uri) să nu fie irosit.
