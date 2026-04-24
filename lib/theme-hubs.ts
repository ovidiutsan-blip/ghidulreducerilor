// Theme-based category hubs (Sprint A3)
// Distinct from lib/categories.ts (which maps to deal.categorie tech chips).
// These are editorial landing pages that group stores by vertical market.

export type ThemeFaqItem = { q: string; a: string }

export type ThemeHub = {
  slug: string
  label: string
  title: string
  description: string
  emoji: string
  color: string // hex, for accent
  heroIntro: string // 1-2 paragraph editorial intro (~150-200 words)
  storeSlugs: string[] // stores to feature (must match stores.json slug)
  dealCategories: string[] // deal.categorie values that legitimately belong to this hub; used to filter topDeals grid. Empty array = no topDeals (empty state shown).
  faq: ThemeFaqItem[]
  tips: string[] // bullet tips for savvy shoppers
}

export const THEME_HUBS: ThemeHub[] = [
  {
    slug: 'fashion',
    label: 'Fashion',
    title: 'Reduceri Fashion Online — Haine, Încălțăminte, Accesorii',
    description:
      'Cele mai bune reduceri la haine, încălțăminte și accesorii din magazinele online din România. Colecții actualizate, branduri verificate, retur gratuit.',
    emoji: '👗',
    color: '#EC407A',
    heroIntro:
      'Moda online din România este dominată de câteva platforme mari care lansează campanii de reduceri aproape săptămânal. Dacă știi unde să te uiți și când, poți găsi haine de firmă la jumătate de preț sau accesorii premium cu 60-70% discount, fără să cobori din calitate.\n\nPe GhidulReducerilor.ro adunăm cele mai bune oferte fashion de la magazinele partenere — Fashion Days (parte din grupul eMAG, peste 2.000 de branduri), Answear (peste 400 de branduri premium ca Tommy Hilfiger, Calvin Klein, Guess) și eMAG (colecții sezoniere și branduri proprii). Fiecare ofertă este verificată de echipă, are procentul real de reducere afișat clar și link afiliat direct către produs — așa că plătești exact prețul de pe site, fără comisioane ascunse.',
    storeSlugs: ['emag', 'watch24'],
    dealCategories: ['ceasuri', 'smartwatch'],
    faq: [
      {
        q: 'Când apar cele mai mari reduceri la haine online?',
        a: 'Cele mai consistente campanii de fashion sunt în perioadele de "sezon încheiat" — sfârșit de august (colecția vară) și sfârșit de februarie (colecția iarnă) — plus Black Friday (noiembrie), Cyber Monday, și reducerile de Paște și Crăciun. În afara acestor vârfuri, Fashion Days și Answear rulează oferte flash săptămânale cu 30-50% reducere la selecții rotative.',
      },
      {
        q: 'Pot returna hainele cumpărate online dacă nu-mi vin bine?',
        a: 'Da, în România legea garantează 14 zile calendaristice pentru retur fără motiv la cumpărăturile online. Fashion Days oferă 30 de zile de retur gratuit prin easybox sau curier, iar Answear oferă 30 de zile retur gratuit la comenzi de peste 300 lei. Hainele trebuie să fie cu etichete, neuzate, și păstrate în ambalajul original.',
      },
      {
        q: 'Codurile promoționale fashion se pot combina cu reducerile afișate?',
        a: 'Depinde de magazin. Fashion Days permite de obicei combinarea unui singur cod promoțional cu reducerile deja afișate pe produs. Answear aplică codul pe prețul final (deja redus), deci obții un discount cumulat. La eMAG, codurile promo se aplică doar la produsele vândute direct de eMAG, nu și la partenerii Marketplace.',
      },
      {
        q: 'Ce branduri premium au prețuri mai bune pe Answear față de magazinele oficiale?',
        a: 'Tommy Hilfiger, Calvin Klein, Guess, Lacoste, Levi\'s și Pepe Jeans au adesea pe Answear prețuri cu 20-40% mai mici decât în magazinele proprii de brand, mai ales la colecțiile din sezoanele trecute. Recomand să setezi alertă pe modelul dorit și să aștepți o campanie flash.',
      },
      {
        q: 'Cât durează livrarea la comenzile fashion?',
        a: 'Fashion Days livrează în 24-48h prin easybox sau curier (gratuit peste 150 lei). Answear livrează prin Fan Courier în 1-3 zile (gratuit peste 300 lei). La eMAG, livrarea easybox e de obicei a doua zi pentru produsele din stocul propriu.',
      },
    ],
    tips: [
      'Setează alertă email pe produsele preferate — primești notificare când scad sub pragul tău',
      'Verifică ambele magazine (Fashion Days + Answear) — același brand poate avea prețuri diferite',
      'Campaniile "Outlet" sau "Last Sizes" au cele mai mari reduceri (până la -80%)',
      'Folosește filtrul de mărime la început pentru a nu pierde timp cu produse epuizate',
    ],
  },
  {
    slug: 'beauty',
    label: 'Beauty & Cosmetice',
    title: 'Reduceri Cosmetice și Parfumuri — Branduri de Lux la Preț Real',
    description:
      'Reduceri verificate la parfumuri, cosmetice și produse de îngrijire de la Notino, eMAG și alte magazine de beauty din România. Autenticitate garantată.',
    emoji: '💄',
    color: '#D81B60',
    heroIntro:
      'Piața de beauty și cosmetice din România a explodat în ultimii ani datorită magazinelor specializate care aduc parfumuri și produse premium la prețuri cu 30-50% sub cele din duty-free sau magazinele fizice de brand. Notino este liderul incontestabil — peste 85.000 de produse, inclusiv branduri de lux precum Chanel, Dior, Lancôme, YSL și Paco Rabanne, cu garanție de autenticitate 100%.\n\nPe GhidulReducerilor.ro monitorizăm zilnic campaniile Notino și alte surse de beauty, selectăm doar ofertele cu discount real (nu "reduceri" pe prețuri umflate artificial) și afișăm procentul exact de economisit. Majoritatea ofertelor vin însoțite și de coduri promoționale suplimentare care se aplică la checkout — uneori ajungi la -65% față de prețul de listă.',
    storeSlugs: ['hiris'],
    dealCategories: ['beauty'],
    faq: [
      {
        q: 'Parfumurile de pe Notino sunt originale?',
        a: 'Da. Notino operează oficial în peste 20 de țări europene și este distribuitor autorizat pentru majoritatea brandurilor de lux. Fiecare parfum vine cu factură, garanție de autenticitate și poate fi returnat în 14 zile dacă ai dubii. Notino NU vinde replici sau tester-e neoficiale.',
      },
      {
        q: 'Când are Notino cele mai mari reduceri?',
        a: 'Notino rulează 3 tipuri de campanii mari: (1) Black Friday / Cyber Monday cu reduceri până la -60%, (2) Sezon încheiat (ianuarie și iulie) cu destocare pe colecții limited edition, și (3) "Ziua Parfumului" și Valentine\'s Day cu coduri promoționale specifice. În afara acestor perioade, mereu găsești oferte flash cu 20-40% reducere pe selecții rotative.',
      },
      {
        q: 'Ce înseamnă "Tester" în oferta Notino și e o reducere reală?',
        a: 'Testerele sunt parfumuri identice cu produsele de vânzare, dar ambalate în cutii simple (fără ambalajul premium de cadou). Conțin exact același parfum, la același volum, dar costă cu 30-50% mai puțin. Dacă nu cumperi parfumul pentru cadou, testerele sunt cea mai bună economie la branduri de lux.',
      },
      {
        q: 'Se poate returna un parfum după ce a fost deschis?',
        a: 'Conform legii, produsele cosmetice sigilate se pot returna fără motiv în 14 zile. Dacă ai desigilat sau folosit parfumul, returnarea depinde de politica magazinului. Notino acceptă retur chiar și pe produse testate, dacă sunt cel puțin 90% pline și în ambalajul original — verifică întotdeauna politica la momentul comenzii.',
      },
      {
        q: 'Există diferențe de preț mari între Notino și Douglas / Sephora?',
        a: 'Da, adesea da. Notino are o marjă mai mică pe parfumuri (2-8%) față de lanțurile fizice (30-50%), deci același parfum Chanel poate costa cu 100-300 lei mai puțin pe Notino decât în Douglas. Avantajul magazinelor fizice rămâne testarea — dar dacă știi deja mirosul, Notino câștigă la preț.',
      },
    ],
    tips: [
      'Abonează-te la newsletter-ul Notino — primești coduri exclusive de 10-15% săptămânal',
      'Caută colecțiile "Set cadou" — conțin 2-3 produse la prețul unuia',
      'Mărimile mai mici (30ml, 50ml) au adesea preț pe ml mai bun decât 100ml la testere',
      'Verifică data de expirare (batch code) — parfumurile au 3-5 ani de la producție',
    ],
  },
  {
    slug: 'farmacie-sanatate',
    label: 'Farmacie & Sănătate',
    title: 'Reduceri Farmacie Online — Suplimente, Medicamente OTC, Cosmetice Dermato',
    description:
      'Oferte verificate la suplimente alimentare, medicamente fără prescripție, produse naturiste și cosmetice dermato de la Dr.Max, Vegis și alți parteneri.',
    emoji: '💊',
    color: '#0277BD',
    heroIntro:
      'Farmacia online a devenit una dintre cele mai rapide modalități de a accesa suplimente, cosmetice dermato și produse OTC la prețuri semnificativ mai mici decât în farmacia din colț. Dr.Max — cea mai mare rețea de farmacii din Europa Centrală și de Est — și Vegis — specializat în produse naturiste și bio — sunt cei doi parteneri principali cu care lucrăm la GhidulReducerilor.ro.\n\nOfertele pe care le afișăm sunt verificate zilnic și au procent real de reducere — unele suplimente ajung la -40% față de prețul de listă, iar campaniile lunare (ex. "Luna Imunității" sau "Ziua Vitaminei C") cumulează reduceri până la -50% pe categorii întregi. Toate produsele sunt autentice, provin din stocul farmaceutic oficial și sunt însoțite de factură — fără riscuri de contrafaceri, cum se pot întâmpla pe marketplace-uri necontrolate.',
    storeSlugs: [],
    dealCategories: ['suplimente-bio'],
    faq: [
      {
        q: 'Se pot cumpăra medicamente cu prescripție online?',
        a: 'În România, medicamentele cu prescripție medicală NU se pot vinde online — indiferent de farmacia online. Doar medicamentele OTC (over-the-counter, fără prescripție), suplimentele alimentare, cosmeticele și dispozitivele medicale se pot comanda. Dr.Max și Vegis respectă strict această reglementare.',
      },
      {
        q: 'Suplimentele de pe Vegis și Dr.Max sunt originale?',
        a: 'Da. Ambele magazine sunt distribuitori autorizați pentru branduri verificate — Solgar, Secom, Herbagetica, Weleda, Doppelherz, Centrum, Naturavit etc. Produsele vin cu lot de fabricație, dată de expirare și factură fiscală. Dr.Max are și certificare ANMDMR ca farmacie autorizată.',
      },
      {
        q: 'Care sunt avantajele Dr.Max față de o farmacie locală?',
        a: 'Prețurile pe Dr.Max.ro sunt adesea cu 15-30% mai mici decât în farmaciile fizice pentru aceleași produse (mai ales la suplimente și cosmetice dermato). Plus: ridicare gratuită din orice farmacie Dr.Max din țară, livrare la domiciliu, și campanii exclusive online cum ar fi "Zi de Naștere Dr.Max" cu -40% pe anumite categorii.',
      },
      {
        q: 'Ce sunt produsele bio/eco de pe Vegis și de ce sunt mai scumpe?',
        a: 'Produsele bio (cosmetice, alimente, suplimente) respectă standardele ecologice europene — fără pesticide, fără aditivi sintetici, fără ingrediente GMO. Procesul de certificare e costisitor pentru producători, ceea ce crește prețul cu 20-40%. Vegis are periodic campanii "Luna Bio" cu reduceri de 25-35% care fac aceste produse accesibile.',
      },
      {
        q: 'Cât durează livrarea la farmacie online?',
        a: 'Dr.Max livrează în 24h prin curier la orașele mari și în 48-72h în restul țării. Ridicarea din farmacie e disponibilă după 2-4h de la comandă. Vegis livrează în 1-2 zile lucrătoare prin Fan Courier sau Cargus, gratuit la comenzi peste 199 lei.',
      },
    ],
    tips: [
      'Înainte de Black Friday, fă lista de suplimente consumate lunar și cumpără stoc pe 6 luni',
      'Multivitaminele generice (Naturavit, Walmark) oferă același profil nutrițional ca branduri de lux la -70% preț',
      'Dr.Max are campanii "1+1" pe selecții de produse — de obicei produse cu data apropiată, dar perfect valabile',
      'Verifică data de expirare înainte de comandă — magazinele sunt obligate să o afișeze',
    ],
  },
  {
    slug: 'carti',
    label: 'Cărți & Ebook',
    title: 'Reduceri Cărți Online — Libris, Elefant, eMAG Books',
    description:
      'Oferte verificate la cărți în limba română și engleză, beletristică, manuale, cărți pentru copii și ebook-uri. Livrare rapidă și retur gratuit.',
    emoji: '📚',
    color: '#5D4037',
    heroIntro:
      'Cumpărarea de cărți online a depășit de mult magazinele fizice — Libris, Elefant și eMAG dețin împreună peste 80% din piață, cu cataloage ce depășesc 1,5 milioane de titluri. Prețurile sunt de regulă cu 20-40% mai mici decât în librăriile tradiționale, iar campaniile periodice (Târgul Gaudeamus, Bookfest online, Back to School) scad prețurile suplimentar cu 30-50%.\n\nLa GhidulReducerilor.ro monitorizăm constant cele trei platforme și afișăm ofertele cu discount real — nu "reduceri" calculate de la prețuri umflate. Libris are cel mai mare catalog (peste 1 milion de titluri), Elefant are cele mai bune prețuri pe beletristică și cărți străine, iar eMAG combină cărți cu bundle-uri de ebook readers și accesorii. Toate au retur gratuit 30 de zile și livrare prin easybox sau curier.',
    storeSlugs: [],
    dealCategories: [],
    faq: [
      {
        q: 'Care magazin are cele mai ieftine cărți?',
        a: 'Pentru beletristică și titluri noi, Elefant are adesea prețuri cu 5-15% mai mici decât Libris, dar Libris acoperă mai multe titluri de nișă (filosofie, științe tehnice, cărți în engleză). La campaniile mari (Bookfest, Black Friday), ambele ajung la -50% pe selecții mari. eMAG are prețuri competitive doar la bestseller-uri și cărți pentru copii.',
      },
      {
        q: 'Se pot returna cărțile cumpărate online?',
        a: 'Da, legea garantează 14 zile retur fără motiv. Libris și Elefant oferă 30 de zile retur gratuit dacă cartea nu a fost citită (fără urme de folosire). eMAG respectă tot 30 de zile. Cărțile trebuie să fie în starea originală, fără pagini marcate sau rupte.',
      },
      {
        q: 'Există campanii de reduceri la cărțile școlare?',
        a: 'Da, în perioada iulie-septembrie toate cele trei magazine rulează campanii "Back to School" cu reduceri de 20-40% la manuale, caiete, auxiliare didactice. Libris și Elefant au și pachete pe clase (ex. "Clasa a V-a — Pachet complet") cu discount suplimentar de 10-15% față de cumpărare individuală.',
      },
      {
        q: 'Cărțile în limba engleză sunt mai ieftine pe Libris sau pe Amazon?',
        a: 'Depinde de titlu. Pentru bestseller-uri internaționale (Stephen King, Brandon Sanderson), Amazon UK/DE are prețuri mai mici dar costurile de livrare transportau diferența. Libris import-ează direct de la edituri (Penguin, HarperCollins) și are adesea prețuri comparabile, fără taxe vamale. Pentru cărți academice sau de nișă, Libris câștigă constant.',
      },
      {
        q: 'Ce diferență e între carte tipărită și ebook?',
        a: 'Ebook-ul e de obicei cu 30-50% mai ieftin decât cartea tipărită, e instant disponibil (fără așteptare de livrare), și poate fi citit pe Kindle, telefon sau tabletă. Dezavantajul: nu poate fi împrumutat, revândut sau păstrat în bibliotecă fizică. Dacă citești 5+ cărți/an, un Kindle (200-400 lei) se amortizează rapid din economiile pe ebook-uri.',
      },
    ],
    tips: [
      'Așteaptă Bookfest (mai-iunie) și Gaudeamus (noiembrie) pentru cele mai mari reduceri',
      'Pachetele "Box set" (trilogii, serii complete) au discount 40-60% față de cumpărare individuală',
      'Abonează-te la newsletter-ul Libris — primești cod de 10% lunar',
      'eMAG are bundle-uri Kindle + 3 ebook-uri gratuite care economisesc 150-200 lei',
    ],
  },
  {
    slug: 'casa-gradina',
    label: 'Casă & Grădină',
    title: 'Reduceri Casă și Grădină — Materiale Construcții, Mobilier, Instalații',
    description:
      'Oferte verificate la materiale de construcții, instalații termice și sanitare, mobilier de grădină și produse DIY de la MatHaus, Fornello și eMAG.',
    emoji: '🏠',
    color: '#F57C00',
    heroIntro:
      'Renovarea casei sau amenajarea grădinii pot costa un salariu întreg — sau pot costa cu 30% mai puțin dacă știi când și de unde să cumperi. MatHaus (specializat în materiale de construcții și amenajări DIY), Fornello (instalații termice, sanitare, calorifere, centrale, panouri solare) și eMAG (mobilier, unelte, electrocasnice) acoperă împreună toată gama de nevoi.\n\nLa GhidulReducerilor.ro urmărim campaniile sezoniere (primăvară-vară pentru grădină, toamnă-iarnă pentru instalații termice) și identificăm ofertele cu discount real. MatHaus are reduceri cumulate la cantități mari (ex. -10% la comenzi peste 2.000 lei pe lânga reducerile individuale), iar Fornello oferă adesea pachete centrală + calorifere + montaj cu discount de 15-20%. Livrarea e gratuită la multe produse voluminoase (centrale termice, panouri solare) și toate produsele au garanție legală + garanție de producător.',
    storeSlugs: ['alecoair', 'case-smart', 'fornello', 'hotpick', 'mathaus', 'novodoors', 'scule365', 'techstar'],
    dealCategories: ['casa-gradina'],
    faq: [
      {
        q: 'Când sunt cele mai mari reduceri la materiale de construcții?',
        a: 'Campaniile cele mai bune la materiale sunt toamna târzie (octombrie-noiembrie — destocare pre-iarnă) și primăvara devreme (februarie-martie — promoții pre-sezon). MatHaus are "Zilele Bricolajului" cu -30-40% pe gresie, faianță, vopsea. Black Friday aduce reduceri punctuale dar nu la fel de consistente ca sezonul specific.',
      },
      {
        q: 'Fornello oferă montaj pentru centralele termice?',
        a: 'Fornello oferă pachete "echipament + montaj" prin parteneri autorizați în majoritatea orașelor mari. Prețul montajului variază între 800-2.000 lei în funcție de complexitate. Avantajul pachetului: prețul e redus cu 10-15% față de cumpărare + montaj separat, și primești garanție pe ambele (inclusiv pe manopera).',
      },
      {
        q: 'Ce materiale DIY au cele mai mari discount-uri?',
        a: 'Vopselele, gresia, faianța și parchetul laminat au cel mai mare potențial de reducere (până la -50%) datorită concurenței mari între branduri. Uneltele electrice (Bosch, Makita, DeWalt) au reduceri mai mici (-15-25%) dar constante în campaniile MatHaus și eMAG. Produsele brand private (ex. vopsea MatHaus Home) au preț permanent cu 30-40% sub branduri premium.',
      },
      {
        q: 'Cum calculez corect câtă gresie/faianță îmi trebuie?',
        a: 'Măsoară suprafața în m² (lungime x lățime), adună 10% pentru tăieri și deșeuri, plus 5% rezervă pentru reparații ulterioare (dacă se sparge o placă). Deci pentru 20 m² comandă ~23 m². Pachetele Mathaus sunt de obicei 1.5 m² / cutie — împarte suprafața la 1.5 și rotunjește în sus.',
      },
      {
        q: 'Livrarea e gratuită pentru materialele grele?',
        a: 'MatHaus oferă livrare gratuită la comenzi peste 500 lei în București și 1.000 lei în restul țării pentru produse standard. Pentru paleți de gresie/faianță sau saci de ciment peste 500 kg, există taxă de livrare specială (100-300 lei) și opțiune de ridicare de la depozit. Fornello oferă livrare gratuită la centralele termice peste 3.500 lei.',
      },
    ],
    tips: [
      'Pentru renovări mari, cere ofertă personalizată pe email — obții adesea -5-10% extra față de prețul online',
      'Vopselele albe standard (alb gresie, alb mat) au rotație rapidă și prețuri mai mici decât culorile speciale',
      'La gresie/faianță verifică nuanța (cod lot) — plăcile din loturi diferite pot avea diferențe ușoare de culoare',
      'Uneltele cu baterii — cumpără platforma (ex. Bosch 18V) și apoi doar acumulatorii; economisești 300-500 lei pe scule',
    ],
  },
  {
    slug: 'electronice',
    label: 'Electronice & Software',
    title: 'Reduceri Electronice și Software — Licențe Adobe, Autodesk, Microsoft',
    description:
      'Reduceri verificate la licențe software profesional (Adobe Creative Cloud, Autodesk AutoCAD, Microsoft Office, Rhino) și electronice de consum. Prețuri reale sub MSRP.',
    emoji: '💻',
    color: '#512DA8',
    heroIntro:
      'Software-ul profesional e una dintre categoriile cele mai scumpe pentru freelanceri, arhitecți, designeri și studenți — o licență Adobe Creative Cloud poate costa 2.500+ lei/an la preț întreg, iar Autodesk AutoCAD trece de 7.000 lei. Dar există alternative legale la prețuri dramatic mai mici: reselleri autorizați precum StreamStore distribuie licențe originale (perpetue sau anuale) cu discount-uri structurale de 10-67% față de MSRP — nu oferte flash, ci prețuri permanente justificate prin volum de distribuție.\n\nPe GhidulReducerilor.ro selectăm doar reselleri verificați cu parteneriat oficial cu producătorii (Adobe, Autodesk, Microsoft, McNeel Rhino, V-Ray, Parallels). Fiecare licență vine cu cheie de activare directă de la producător, factură fiscală românească și suport oficial. Categoria include și electronice de consum (eMAG) pentru laptop-uri, periferice și componente IT cu reduceri în campanii.',
    storeSlugs: ['emag', 'forit', 'streamstore'],
    dealCategories: ['electronice'],
    faq: [
      {
        q: 'Licențele software de la reselleri sunt legale și originale?',
        a: 'Da, dacă magazinul e reseller autorizat. StreamStore, de exemplu, distribuie licențe directe de la Adobe, Autodesk, Microsoft — primești cheie originală care se activează oficial pe site-ul producătorului. Suportul, update-urile și cloud storage sunt incluse exact ca la licența cumpărată direct. Evită reseller-i necunoscuți din afara UE care vând la prețuri "too good to be true" — adesea sunt licențe de volum furate sau chei revocate.',
      },
      {
        q: 'Ce diferență e între licență perpetuă și abonament?',
        a: 'Licența perpetuă (ex. Autodesk AutoCAD LT perpetual) o cumperi o dată și o folosești pe viață, dar nu primești update-uri majore gratuite. Abonamentul (Creative Cloud, Microsoft 365) te costă lunar/anual dar ai mereu cea mai nouă versiune plus cloud storage și suport. Pentru uz profesional continuu, abonamentul e mai avantajos. Pentru utilizare ocazională sau proiecte specifice, licența perpetuă economisește mai mult pe termen lung.',
      },
      {
        q: 'Pot folosi licența pe mai multe calculatoare?',
        a: 'Depinde de tip. Licențele Adobe Creative Cloud permit instalare pe 2 dispozitive ale aceluiași utilizator (nu concomitent). Autodesk oferă licențe single-user (1 user, multiple PC-uri) sau network (multi-user, servere de licențe). Microsoft 365 Personal permite până la 5 dispozitive. Citește mereu termenii de licențiere la cumpărare — transferul pe un alt calculator se face prin dezactivare + reactivare, nu copiere simplă.',
      },
      {
        q: 'Software-ul educațional (student / academic) e cu reducere?',
        a: 'Da, toate marile companii (Adobe, Autodesk, Microsoft, JetBrains) oferă versiuni educaționale cu 60-80% reducere față de preț comercial, dacă dovedești statutul de student sau profesor. Licențele educaționale nu pot fi folosite comercial (pentru proiecte plătite). La terminarea studiilor, trebuie să migrezi la licență comercială. StreamStore și alți reselleri distribuie și licențe educaționale autorizate.',
      },
      {
        q: 'Merită să cumpăr componente PC individuale sau laptop gata făcut?',
        a: 'Pentru gaming și workstation profesional, construirea unui PC custom oferă +20-40% performanță la același buget comparativ cu laptop-uri pre-built. Pentru mobilitate și simplitate, laptopurile din campanii eMAG/Altex au prețuri bune, mai ales la sfârșit de an când se destochează modelele vechi. Compară mereu prețul individual al CPU+GPU+RAM+SSD vs laptop înainte să decizi.',
      },
    ],
    tips: [
      'Pentru licențe software mari (Adobe, Autodesk), abonamentul anual e cu 20% mai ieftin decât lunar cumulat',
      'Verifică programul de upgrade: unele licențe perpetue primesc upgrade la versiunea nouă cu -50% timp de 12 luni',
      'Licențele educaționale necesită verificare identitate — pregătește legitimația de student înainte de comandă',
      'La componente PC, urmărește prețul pe PCPartPicker România — arată istoricul și alertează când scade sub pragul tău',
    ],
  },
]

export function getThemeHubBySlug(slug: string): ThemeHub | undefined {
  return THEME_HUBS.find(t => t.slug === slug)
}

export function getAllThemeHubSlugs(): string[] {
  return THEME_HUBS.map(t => t.slug)
}
