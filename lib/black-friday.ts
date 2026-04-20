// Sprint C — Black Friday permanent hub
// Pagina /black-friday este evergreen, dar datele sezoniere se refresh la 1 iulie și 1 octombrie.
// Refresh procedure: update BF_CURRENT.targetDate, add entry in BF_HISTORY, review participatingStores.

export type BFStore = {
  slug: string
  nume: string
  logoEmoji: string
  culoare: string
  wave: 'early' | 'global' | 'both'
  notaScurta: string
  discountTipic: string
}

export type BFHistoryEntry = {
  an: number
  dataBF: string // ISO
  durata: string
  highlights: string
}

export type BFFaq = { q: string; a: string }

export type BFPrepStep = {
  titlu: string
  descriere: string
  icon: string
}

export const BF_CURRENT = {
  an: 2026,
  // Data estimată eMAG Black Friday 2026 (tradiție: prima vineri din noiembrie)
  earlyBFDate: '2026-11-06', // Vineri 6 noiembrie 2026
  earlyBFEndDate: '2026-11-08', // Duminică 8 noiembrie 2026
  // Black Friday global (urmează Thanksgiving US — vineri după ultima joi din noiembrie)
  globalBFDate: '2026-11-27', // Vineri 27 noiembrie 2026
  globalBFEndDate: '2026-11-30', // Luni Cyber Monday
  lastUpdated: '2026-04-20',
}

export const BF_HISTORY: BFHistoryEntry[] = [
  {
    an: 2025,
    dataBF: '2025-11-07',
    durata: '3 zile (vineri-duminică)',
    highlights:
      'eMAG a raportat comenzi de peste 750 milioane lei în primele 8 ore, cu vârf pe electronice mari (TV, frigidere, laptopuri). Fashion Days și Answear au avut promoții paralele cu reduceri până la -70%.',
  },
  {
    an: 2024,
    dataBF: '2024-11-08',
    durata: '3 zile (vineri-duminică)',
    highlights:
      'Ediție record pentru eMAG: peste 1 milion de tranzacții în primele 24h. Notino și Sephora au introdus pentru prima dată reduceri complete pe parfumurile premium (Chanel, Dior) cu până la -50%. Categorii vârf: electrocasnice mari, smartphone, parfumerie.',
  },
  {
    an: 2023,
    dataBF: '2023-11-10',
    durata: '3 zile (vineri-duminică)',
    highlights:
      'Primul an cu „BF extins" pe Altex și eMAG (7 zile cu pre-reduceri). Inflația a redus ticketul mediu cu ~12% față de 2022, dar volumul tranzacțiilor a crescut cu 8%. Cele mai bune discount-uri: electrocasnice încorporabile (-55%) și smart TV OLED (-40%).',
  },
]

export const BF_STORES: BFStore[] = [
  {
    slug: 'emag',
    nume: 'eMAG',
    logoEmoji: '🛒',
    culoare: '#F7E636',
    wave: 'early',
    notaScurta: 'Liderul Black Friday în România — deschide campania prima vineri din noiembrie cu stoc limitat pe electronice mari.',
    discountTipic: '-20% până la -60%',
  },
  {
    slug: 'fashiondays',
    nume: 'Fashion Days',
    logoEmoji: '👗',
    culoare: '#EC407A',
    wave: 'early',
    notaScurta: 'Parte din grupul eMAG, deschide Black Friday simultan cu eMAG. 2.000+ branduri, reduceri flash orare în prima zi.',
    discountTipic: '-30% până la -70%',
  },
  {
    slug: 'notino',
    nume: 'Notino',
    logoEmoji: '💄',
    culoare: '#D81B60',
    wave: 'global',
    notaScurta: 'Se aliniază la Black Friday global (ultimul weekend din noiembrie). Cele mai mari reduceri ale anului la parfumuri premium și testere.',
    discountTipic: '-25% până la -60%',
  },
  {
    slug: 'answear',
    nume: 'Answear',
    logoEmoji: '👔',
    culoare: '#000000',
    wave: 'both',
    notaScurta: 'Două valuri: pre-BF în prima săptămână din noiembrie, apoi BF principal pe 27 noiembrie cu Cyber Monday pe 30 noiembrie.',
    discountTipic: '-30% până la -65%',
  },
  {
    slug: 'drmax',
    nume: 'Dr.Max',
    logoEmoji: '💊',
    culoare: '#0277BD',
    wave: 'both',
    notaScurta: 'Reduceri pe suplimente și cosmetică dermato toată luna noiembrie, cu vârfuri pe 6 și 27 noiembrie.',
    discountTipic: '-15% până la -40%',
  },
  {
    slug: 'libris',
    nume: 'Libris',
    logoEmoji: '📚',
    culoare: '#5D4037',
    wave: 'early',
    notaScurta: 'BF devine „Festivalul Cărții" pentru Libris — reduceri până la -80% pe stoc epuizat și -50% pe noutăți editoriale.',
    discountTipic: '-40% până la -80%',
  },
  {
    slug: 'elefant',
    nume: 'Elefant',
    logoEmoji: '🐘',
    culoare: '#7B1FA2',
    wave: 'early',
    notaScurta: 'Cărți, jucării, jocuri și papetărie la reduceri masive. Prima zi e cea mai competitivă — stocurile mici dispar rapid.',
    discountTipic: '-30% până la -75%',
  },
  {
    slug: 'vegis',
    nume: 'Vegis',
    logoEmoji: '🌿',
    culoare: '#2E7D32',
    wave: 'early',
    notaScurta: 'Destocare pe suplimente cu termen apropiat (dar încă valabil 6-12 luni) — aici găsești multivitamine premium la -50%.',
    discountTipic: '-20% până la -50%',
  },
  {
    slug: 'mathaus',
    nume: 'MatHaus',
    logoEmoji: '🔨',
    culoare: '#F57C00',
    wave: 'early',
    notaScurta: 'Reduceri pe materiale de construcții, scule electrice și gresie/faianță — util pentru renovări programate primăvara.',
    discountTipic: '-15% până la -40%',
  },
  {
    slug: 'fornello',
    nume: 'Fornello',
    logoEmoji: '🔥',
    culoare: '#FF5722',
    wave: 'early',
    notaScurta: 'Centrale termice, boilere și panouri solare cu reduceri mari — ideal dacă planifici o investiție majoră înainte de iarnă.',
    discountTipic: '-10% până la -30%',
  },
]

export const BF_PREP_STEPS: BFPrepStep[] = [
  {
    titlu: 'Fă-ți lista cu 2-3 săptămâni înainte',
    descriere:
      'Stabilește exact ce vrei să cumperi — nu te uita la ofertele generale, știi deja modelele (ex. „Samsung TV 55 QLED Q70D" nu „un TV mare"). Scrie prețul curent din magazinele principale pe 15 octombrie, 1 noiembrie și în ziua BF. Așa vezi dacă reducerea e reală sau cosmetică.',
    icon: '📝',
  },
  {
    titlu: 'Verifică istoricul de preț cu extensii gratuite',
    descriere:
      'Instalează extensia PriceSpy sau Altex-Price-History (extensie Chrome) pe produsul dorit. Dacă prețul din BF e mai mare decât minimul istoric din ultimele 6 luni, reducerea e iluzorie. Un TV care a costat 2.500 lei în iulie și e „redus de la 3.500 la 2.700 lei" de BF nu e o afacere.',
    icon: '📊',
  },
  {
    titlu: 'Setează alerte pe GhidulReducerilor.ro',
    descriere:
      'Abonează-te la alertele noastre pe categoriile care te interesează. Primești notificare în momentul în care un produs prioritar pentru tine intră în promoție — nu trebuie să stai cu telefonul în mână la 8 dimineața pe 6 noiembrie.',
    icon: '🔔',
  },
  {
    titlu: 'Pregătește checkout-ul în avans',
    descriere:
      'Salvează cardul și adresa în toate magazinele unde ai comenzi prioritare. Testează login-ul cu o săptămână înainte (resetează parola dacă e nevoie). Asigură-te că ai un al doilea card pregătit, pentru că primul card poate fi refuzat temporar de banca ta ca „tranzacție suspectă" în weekendul BF.',
    icon: '💳',
  },
]

export const BF_FAQ: BFFaq[] = [
  {
    q: 'Când începe Black Friday 2026 în România?',
    a: `În România există două valuri Black Friday. Primul (BF „românesc", deschis de eMAG) începe probabil vineri, 6 noiembrie 2026, dimineața la ora 8:00, și durează până duminică 8 noiembrie. Al doilea (BF „global", cu Notino, Answear, brand-uri internaționale) începe vineri 27 noiembrie 2026 și continuă până luni 30 noiembrie (Cyber Monday). Calendarul exact se confirmă în prima săptămână din octombrie 2026 — actualizăm pagina imediat ce eMAG anunță oficial data.`,
  },
  {
    q: 'Ce magazine participă la Black Friday 2026?',
    a: `Peste 90% dintre magazinele online mari din România participă la Black Friday. Partenerii verificați de noi pentru 2026 sunt eMAG, Fashion Days, Notino, Answear, Dr.Max, Libris, Elefant, Vegis, MatHaus și Fornello. Pe pagina de mai sus găsești pentru fiecare detalii despre ce val de BF prinde (early vs. global), discount-ul tipic și strategia recomandată. Adăugăm noi parteneri pe măsură ce se aprobă în rețelele de afiliere.`,
  },
  {
    q: 'Sunt reducerile de Black Friday reale sau sunt prețuri umflate înainte?',
    a: `Depinde de magazin. Magazinele mari (eMAG, Fashion Days, Notino) sunt monitorizate de ANPC și riscă amenzi dacă umflă prețurile cu 30+ zile înainte. În practică, 70-80% dintre ofertele de top sunt reduceri reale față de prețul mediu din ultimele 3 luni. Restul sunt „reduceri optice" — prețul de pornire e inventat. Regula de aur: verifică mereu istoricul de preț cu extensii gratuite și nu cumpăra doar pentru că vezi procentul mare.`,
  },
  {
    q: 'Ce să NU cumperi de Black Friday?',
    a: `Evită: (1) electronice lansate în ultimele 2-3 luni — reducerea reală e mică și în ianuarie scad oricum; (2) produse cu „stoc limitat de 5 bucăți" care expiră în 10 minute — de regulă e truc psihologic, stocul se resetează; (3) bundle-uri cu accesorii impuse (ex. TV + soundbar + montaj) unde accesoriile cresc prețul cu 30%; (4) cadouri generice pe care le-ai lua „pentru că sunt ieftine" — economia falsă e când cumperi lucruri de care nu ai nevoie. Cumpără doar ce aveai deja pe listă.`,
  },
  {
    q: 'Cum funcționează returnul la comenzile de Black Friday?',
    a: `Legea consumatorului (OUG 34/2014) garantează 14 zile calendaristice pentru retur fără motiv la cumpărăturile online — aceeași regulă se aplică și de Black Friday, chiar dacă produsul a fost „la ofertă". Majoritatea magazinelor mari (eMAG, Fashion Days, Answear) oferă voluntar 30 de zile de retur gratuit. Excepție: produse personalizate, alimentare, cosmetice desigilate. Păstrează eticheta și ambalajul original până te decizi — unele magazine refuză returul fără ambalaj intact.`,
  },
  {
    q: 'Pot folosi coduri promoționale peste reducerile de Black Friday?',
    a: `La majoritatea magazinelor, nu — codurile promoționale standard sunt dezactivate în timpul BF pentru a nu cumula cu reducerea deja aplicată. Excepții frecvente: Notino acceptă codul pe prețul final redus (discount cumulat), iar Answear rulează adesea coduri specifice BF (ex. BF2026 pentru -10% adițional pe selecții). Verifică la fiecare magazin secțiunea „Coduri Black Friday" sau newsletter-ul primit cu 1-2 zile înainte.`,
  },
  {
    q: 'Black Friday vs. reducerile din ianuarie — când e mai bine să cumpăr?',
    a: `Depinde de categorie. Electronice mari (TV, laptopuri, electrocasnice): Black Friday câștigă — în ianuarie stocurile sunt mici și producătorii își mențin prețurile înainte de noile lansări. Haine și fashion: ianuarie câștigă — e sezon încheiat, magazinele vor să scape de stocul de iarnă cu reduceri de -70%. Parfumuri și beauty: egale — ambele perioade au campanii puternice. Mobilă și amenajări: Black Friday are uneori oferte mai bune, dar piața e mai puțin competitivă decât la electronice.`,
  },
]

export function getParticipatingStoresByWave(wave: 'early' | 'global' | 'both'): BFStore[] {
  return BF_STORES.filter(s => s.wave === wave || s.wave === 'both')
}

export function getAllParticipatingStores(): BFStore[] {
  return BF_STORES
}
