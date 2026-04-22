/**
 * Store Guides — editorial ghiduri per magazin.
 * Fiecare ghid e un document unic cu 600-1000 cuvinte ce acoperă:
 * intro, când sunt reducerile majore, cum folosești un cod promo,
 * livrare & retur, metode de plată, tips, FAQ.
 *
 * Folosit de app/ghiduri/[magazin]/page.tsx pentru SSG.
 */

export type GuideSection = {
  heading: string
  body: string
}

export type StoreGuide = {
  slug: string            // slug folosit în URL: /ghiduri/[slug]
  storeSlug: string       // map la stores.json
  title: string           // H1 pagină
  metaTitle: string       // <title>
  metaDescription: string // meta description (~155 char)
  intro: string           // 200-300 cuvinte editorial lead
  sections: GuideSection[]
  tips: string[]
  faq: { q: string; a: string }[]
  lastUpdated: string     // YYYY-MM-DD
}

export const STORE_GUIDES: StoreGuide[] = [
  {
    slug: 'notino',
    storeSlug: 'notino',
    title: 'Ghid Notino — Cum cumperi parfumuri originale cu reducere',
    metaTitle: 'Ghid Notino 2026 — Reduceri, Coduri Promo si Tips',
    metaDescription: 'Ghid complet Notino 2026: când sunt cele mai mari reduceri, cum folosești codurile promo, livrare, retur 14 zile și autenticitate 100%.',
    intro: 'Notino este cel mai mare retailer online de parfumuri și cosmetice din Europa Centrală și de Est, cu peste 85.000 de produse de la branduri de lux precum Chanel, Dior, Lancôme, Yves Saint Laurent, Paco Rabanne sau Versace. Pentru cumpărători din România, Notino combină garanția autenticității cu prețuri care deseori bat piața locală cu 20-40%, mai ales la parfumuri tester și la edițiile limitate. În acest ghid găsești tot ce trebuie să știi ca să cumperi inteligent de pe Notino în 2026: când se fac cele mai bune reduceri, cum folosești un cod promo fără să pierzi alte discount-uri, ce să verifici înainte să plasezi comanda, cum funcționează returul și de ce preocuparea legitimă legată de autenticitate nu e o problemă reală la Notino.',
    sections: [
      {
        heading: 'Când sunt cele mai mari reduceri pe Notino',
        body: 'Notino are campanii de reduceri aproape non-stop, dar intervalele cu cele mai bune oferte sunt ușor de anticipat. Black Friday (ultima vineri din noiembrie) aduce reduceri reale de până la 70% pe parfumuri și seturi cadou, iar stocurile dispar rapid — merită să pui în wishlist brandurile preferate din octombrie. Campania "Valentine\'s Day" (1-14 februarie) are discount-uri de 25-40% pe parfumuri romantice și seturi cadou. "Ziua Internațională a Femeii" (1-8 martie) aduce reduceri pe cosmetică decorativă (ruj, fond de ten, paletă ochi) cu până la 50%. Vara (iunie-august) Notino rulează campanii "Summer Sale" pe arome proaspete și protecție solară. În plus, ai săptămânal campanii tematice: "Happy Hour" (reduceri scurte de 1-2 zile), "Weekend Deals", "Beauty Days". Abonarea la newsletter îți dă acces cu 24-48h înainte la campaniile majore, iar primul abonament vine cu un cod -10%.'
      },
      {
        heading: 'Cum folosești un cod promo pe Notino',
        body: 'Procesul e standard: adaugi produsele în coș, mergi la "Finalizare comandă", iar în ecranul de plată vezi un câmp "Cod de reducere". Introduci codul, apeși "Aplică" și reducerea se scade din total. Atenție la 3 lucruri: (1) Multe coduri Notino nu se cumulează cu produsele deja reduse — dacă parfumul e deja la -30%, codul de -10% e ignorat sau aplicat doar pe produsele full price; (2) Unele coduri au prag minim de comandă (ex. "minim 250 lei"); (3) Codurile pentru "new customers" nu funcționează dacă ai mai comandat vreodată cu același email. Dacă un cod nu funcționează, verifică data de expirare — noi validăm zilnic codurile listate pe GhidulReducerilor.ro, dar Notino uneori le retrage mai devreme decât anunțul inițial.'
      },
      {
        heading: 'Livrare, retur și autenticitate',
        body: 'Livrarea standard Notino în România e 2-4 zile lucrătoare prin FAN Courier, cu cost 14,99 lei, gratuită peste 199 lei. Pentru comenzi urgente există livrare expres (1-2 zile) la 29,99 lei. Returul e de 14 zile de la primire (jumătate față de magazinele românești clasice, care oferă 30 zile) — recomandăm să deschizi coletul cu camera pornită dacă e un parfum scump, pentru dovadă în caz de problemă. Pe autenticitate: Notino e distribuitor oficial european, toate produsele vin cu codul de lot original și pot fi verificate pe checkfresh.com. Pentru testare înainte de achiziție, Notino oferă "samples" (mostre) gratuite la majoritatea comenzilor, iar reviews-urile verificate de clienți sunt filtrate pe "cumpărător verificat".'
      }
    ],
    tips: [
      'Abonează-te la newsletter cu un email secundar — primești 10% reducere la prima comandă',
      'Verifică secțiunea "Outlet" pentru produse la -50% sau mai mult',
      'Nu cumula comenzi — Notino uneori oferă reduceri suplimentare pe comenzi separate mai mici',
      'Pentru parfumuri scumpe, comandă și o mostră gratuită înainte ca să testezi'
    ],
    faq: [
      { q: 'Sunt produsele Notino 100% originale?', a: 'Da. Notino este distribuitor oficial european și colaborează direct cu brandurile. Toate produsele au cod de lot verificabil pe checkfresh.com.' },
      { q: 'Câte zile am pentru retur?', a: 'Notino oferă 14 zile de retur de la data primirii coletului, cu condiția ca produsul să fie nefolosit și în ambalajul original.' },
      { q: 'Pot cumula un cod promo cu produse deja reduse?', a: 'De obicei nu. Majoritatea codurilor Notino nu se aplică pe produse aflate deja în campanie. Citește termenii fiecărui cod.' },
      { q: 'Cât durează livrarea în România?', a: '2-4 zile lucrătoare pentru livrarea standard prin FAN Courier. Expresul ajunge în 1-2 zile.' },
      { q: 'Pot plăti ramburs?', a: 'Da, Notino oferă plată la livrare (ramburs), card online și transfer bancar.' }
    ],
    lastUpdated: '2026-04-20'
  },
  {
    slug: 'answear',
    storeSlug: 'answear',
    title: 'Ghid Answear — Cum cumperi haine branded cu reducere',
    metaTitle: 'Ghid Answear 2026 — Reduceri, Campanii si Tips',
    metaDescription: 'Ghid Answear 2026: când sunt reducerile mari pe Tommy Hilfiger, Calvin Klein, Guess. Cum aplici codurile, livrare gratuită, retur 30 zile.',
    intro: 'Answear.ro este unul dintre puținele magazine online din România care aduce constant branduri internaționale premium și le menține la prețuri competitive. Cu peste 400 de mărci în catalog — de la Tommy Hilfiger, Calvin Klein și Guess, până la Lacoste, Armani și Levi\'s — Answear acoperă aproape toată piața de fashion branded pentru adulți și copii. Pentru cumpărătorul din România, avantajul principal e că poți găsi articole oficiale cu 30-60% mai ieftin decât în magazinele fizice, mai ales în timpul campaniilor sezoniere. Acest ghid îți arată când să cumperi de pe Answear, cum să combini reducerile cu codurile promo pentru prețul minim, și la ce să fii atent înainte să plasezi comanda — în special la mărimi, care diferă vizibil între brandurile europene și americane.',
    sections: [
      {
        heading: 'Când sunt cele mai bune campanii pe Answear',
        body: 'Answear are un calendar de reduceri destul de predictibil. Sfârșitul sezonului e momentul-cheie: campania "End of Season Sale" de la sfârșit de ianuarie și sfârșit de iulie aduce reduceri de 40-70% pe colecțiile precedente. Black Friday (noiembrie) e intens, cu reduceri reale la brandurile premium, dar stocurile se epuizează rapid la mărimile populare (M-L). Campaniile "-20% extra la o mulțime de produse" sau "3 la preț de 2" sunt frecvente între sezoane. În plus, Answear Club (programul de fidelitate gratuit) îți dă acces cu 12h înainte la reducerile mari și oferă puncte pe fiecare comandă, care se transformă în cupoane.'
      },
      {
        heading: 'Cum folosești un cod promo pe Answear',
        body: 'La checkout, există o secțiune "Cod de reducere" imediat sub listă produse. Introduci codul, apeși "Aplică" și vezi noul total. Answear permite un singur cod per comandă, iar multe nu se aplică peste reduceri existente. Codurile "-15% la prima comandă" se activează doar cu un cont nou (email diferit, adresă diferită). Codurile "Answear Club" apar automat în contul tău dacă ești înscris. Dacă cumperi mai multe produse, uneori e mai ieftin să faci două comenzi separate — odată cu codul de "primă comandă" pe unul din emailuri, odată fără — decât o singură comandă mare.'
      },
      {
        heading: 'Livrare, retur și mărimi',
        body: 'Livrarea e gratuită pentru comenzi peste 300 lei prin curier FAN sau easybox, altfel 14,99 lei. Ajunge în 2-3 zile lucrătoare. Returul e 30 de zile gratuit — primești etichetă prepaid prin email după ce inițiezi returul în contul tău. Mare atenție la mărimi: brandurile americane (Tommy, Calvin Klein, Levi\'s) marchează talia în inches (28, 30, 32), iar echivalentul europeano-românesc diferă. Ghidul de mărimi Answear e corect pentru majoritatea, dar verifică și reviews-urile clienților — sunt foarte utile pentru "fits small/large". Pentru pantofi, mărimile italiene (Armani, Guess) sunt de regulă 1 număr mai mari decât cele românești.'
      }
    ],
    tips: [
      'Înscrie-te gratuit în Answear Club pentru -10% la prima comandă și puncte la fiecare achiziție',
      'Filtrează după "Reduceri" în meniul de sus pentru a vedea doar produsele cu discount',
      'Verifică tabelul de mărimi pe pagina produsului — diferă semnificativ între branduri',
      'La sfârșit de sezon (ianuarie și iulie) sunt cele mai mari reduceri pe colecțiile trecute'
    ],
    faq: [
      { q: 'De la ce sumă livrarea e gratuită pe Answear?', a: 'Livrarea e gratuită pentru comenzi peste 300 lei prin curier FAN sau easybox.' },
      { q: 'Câte zile am pentru retur?', a: '30 de zile de la primirea coletului, cu retur gratuit prin curier pe baza etichetei prepaid.' },
      { q: 'Sunt produsele Answear originale?', a: 'Da, Answear colaborează direct cu distribuitorii oficiali ai brandurilor din catalog.' },
      { q: 'Cum aflu că un cod promo e valid?', a: 'Introdu-l la checkout și vezi dacă total-ul se actualizează. Noi validăm zilnic codurile listate pe GhidulReducerilor.ro.' },
      { q: 'Există Answear Club și merită?', a: 'Da, e gratuit. Oferă -10% la prima comandă, acces cu 12h înainte la campanii și puncte convertibile în cupoane.' }
    ],
    lastUpdated: '2026-04-20'
  },
  {
    slug: 'drmax',
    storeSlug: 'drmax',
    title: 'Ghid Dr.Max — Cum cumperi suplimente și cosmetică dermato cu reducere',
    metaTitle: 'Ghid Dr.Max 2026 — Reduceri Farmacie Online',
    metaDescription: 'Ghid Dr.Max 2026: când sunt cele mai mari reduceri pe suplimente, cosmetică dermato, medicamente OTC. Coduri promo, livrare, ridicare din farmacie.',
    intro: 'Dr.Max este cea mai mare rețea de farmacii din Europa Centrală și de Est, cu peste 2.000 de puncte fizice și un magazin online dezvoltat care servește și România. Pentru cumpărătorul român, Dr.Max combină trei avantaje greu de găsit în altă parte: prețuri competitive la medicamentele fără prescripție (OTC), o selecție solidă de cosmetică dermato (La Roche-Posay, Vichy, Avène, Bioderma) și opțiunea de ridicare gratuită din farmacia fizică. Acest ghid explică cum să profiți de campaniile Dr.Max, cum să combini un cod promo cu reducerile existente (unde se permite), și când merită să comanzi online vs. să mergi fizic în farmacie.',
    sections: [
      {
        heading: 'Când sunt cele mai bune reduceri pe Dr.Max',
        body: 'Dr.Max rulează constant campanii de tip "2+1 gratis" sau "-30% la al doilea produs" pe suplimente alimentare, vitamine și cosmetică. "Luna imunității" (octombrie-noiembrie) are reduceri mari pe vitamina C, D și zinc. "Season of beauty" (primăvară) aduce discount-uri pe dermato-cosmetică. Black Friday e relevant pentru Dr.Max: reduceri reale de 30-50% pe electronice medicale (tensiometre, glucometre, cântare inteligente), termometre și produse de cadou. În plus, clubul Dr.Max îți dă un 10% permanent la produsele non-promoționale, plus puncte care se schimbă în vouchere.'
      },
      {
        heading: 'Cum cumperi inteligent de pe Dr.Max',
        body: 'Primul pas — verifică dacă produsul e listat și în farmacia fizică din apropiere. Ridicarea din farmacie e gratuită și rapidă (disponibilă de obicei în aceeași zi), iar prețul online e același ca cel afișat la checkout. Pentru rețete, Dr.Max acceptă doar prescripții electronice (e-rețetă) — nu trimite poze sau scanări la produsele cu Rx. Pentru suplimente și OTC, nu e nevoie de rețetă. Cardul de fidelitate Dr.Max îl activezi online gratuit și începi imediat să strângi puncte. La suplimente scumpe (Solgar, Secom), merită să verifici și Vegis.ro care uneori are prețuri mai bune — comparativă rapidă pe GhidulReducerilor.ro.'
      },
      {
        heading: 'Livrare și retur',
        body: 'Livrarea standard Dr.Max la adresă costă 19,90 lei prin curier, gratuită peste 199 lei. Ridicarea din farmacie e mereu gratuită, indiferent de sumă — recomand această opțiune pentru comenzile mici. Returul e 14 zile pentru produsele nedeschise (legal minim, mai puțin generos decât alte magazine). Pentru medicamente și suplimente, returul e limitat pe motive sanitare — citește termenii pe fiecare produs. Comenzile online pot fi anulate gratuit înainte de procesare (aprox. 30 min-1h după plasare).'
      }
    ],
    tips: [
      'Ridică din farmacie când poți — livrarea e gratuită, produsul te așteaptă în aceeași zi',
      'Înscrie-te în Clubul Dr.Max pentru -10% permanent la produsele non-promoționale',
      'Verifică prețul și pe Vegis sau eMAG înainte de a comanda suplimente scumpe',
      'Pentru cosmetică dermato, vezi secțiunea "Outlet" pentru produse aproape de termen, la -40-60%'
    ],
    faq: [
      { q: 'Pot cumpăra medicamente cu prescripție de pe Dr.Max online?', a: 'Da, dar doar cu rețetă electronică (e-rețetă). Nu sunt acceptate poze sau scanări ale rețetelor fizice.' },
      { q: 'Ridicarea din farmacie este gratuită?', a: 'Da, ridicarea din orice farmacie Dr.Max e gratuită, indiferent de valoarea comenzii.' },
      { q: 'Cât durează livrarea la domiciliu?', a: '1-3 zile lucrătoare prin curier, cu cost 19,90 lei (gratuită peste 199 lei).' },
      { q: 'Pot returna medicamente sau suplimente?', a: 'Doar produsele nedeschise și în ambalajul original, în 14 zile. Unele categorii sanitare au excepții.' },
      { q: 'Clubul Dr.Max e gratuit?', a: 'Da, e gratuit. Oferă -10% la produse non-promoționale și puncte care se schimbă în vouchere.' }
    ],
    lastUpdated: '2026-04-20'
  },
  {
    slug: 'fashiondays',
    storeSlug: 'fashiondays',
    title: 'Ghid Fashion Days — Cum profiți de reducerile flash',
    metaTitle: 'Ghid Fashion Days 2026 — Campanii Flash si Tips',
    metaDescription: 'Ghid Fashion Days 2026: cum funcționează campaniile flash, când sunt reducerile până la -80%, livrare gratuită easybox, retur 30 zile.',
    intro: 'Fashion Days este cel mai mare retailer fashion online din România, parte din grupul eMAG. Modelul de business e diferit de al competitorilor clasici: Fashion Days rulează "campanii flash" pe durate scurte (3-7 zile) cu reduceri agresive de 50-80%, pe branduri selectate. Stocurile sunt limitate, iar produsele dispar în câteva ore la mărimile populare. Acest ghid îți explică cum funcționează calendarul de campanii, cum să nu ratezi oferte bune, cum folosești integrarea cu Genius și avantajele livrării prin easybox-urile eMAG.',
    sections: [
      {
        heading: 'Cum funcționează campaniile flash pe Fashion Days',
        body: 'Spre deosebire de un magazin clasic, Fashion Days organizează zilnic 10-30 de "campanii" noi — fiecare fiind o selecție de produse de la un brand sau categorie, disponibile la reducere pentru 3-7 zile. De luni dimineață primești newsletter-ul cu noile campanii ale săptămânii. Cele mai bune oferte sunt la începutul campaniei — după 24-48h, mărimile populare (M, L pentru haine; 38-42 pentru pantofi) dispar. La finalul campaniei, produsele rămase se întorc în "outlet permanent" la prețuri și mai mici. Strategie: verifică seara de duminică/luni dimineață și ia decizia rapid. Aplicația mobilă Fashion Days are notificări push pentru brandurile din wishlist.'
      },
      {
        heading: 'Livrare gratuită și Genius',
        body: 'Fashion Days folosește infrastructura eMAG: livrare easybox la 12,99 lei sau gratuită peste 150 lei, livrare la domiciliu 19,99 lei. Abonamentul Genius (de la eMAG, 29 lei/lună sau 249 lei/an) îți dă livrare gratuită nelimitată pe Fashion Days, eMAG și Tazz — merită dacă faci minim 1-2 comenzi pe lună. Ridicarea prin showroom-urile Fashion Days din București și Cluj e gratuită. Returul e 30 zile gratuit, cu etichetă prepaid generată din contul tău.'
      },
      {
        heading: 'Secretele outlet-ului permanent',
        body: 'Mulți cumpărători nu știu că Fashion Days are o secțiune "Outlet" cu produse la -60-80% din toate campaniile expirate. Accesezi din meniu → "Reduceri" → filtru "Outlet". Aici găsești frecvent haine branded (Adidas, Puma, Nike, Tommy) la 50-100 lei. Dezavantajul: mărimile sunt incomplete — dacă porți o mărime populară (M pentru bărbați, 38 pentru femei), vei găsi greu. Avantajul real e pentru mărimile "marginale" (XS, XL, XXL), care sunt bine acoperite. Filtrează direct după mărime ca să nu pierzi timp.'
      }
    ],
    tips: [
      'Verifică campaniile luni dimineață — cele mai bune produse dispar în 24-48h',
      'Adaugă brandurile preferate în wishlist pentru notificări push cu campanii noi',
      'Genius (abonament eMAG) îți dă livrare gratuită nelimitată pe Fashion Days',
      'Secțiunea "Outlet" are produse la -60-80% dar cu stoc limitat la mărimi populare'
    ],
    faq: [
      { q: 'Câte zile durează o campanie pe Fashion Days?', a: 'De obicei 3-7 zile, cu stocuri limitate. Mărimile populare dispar de regulă în 24-48h de la start.' },
      { q: 'Ce primesc dacă am Genius eMAG?', a: 'Livrare gratuită nelimitată pe Fashion Days, eMAG și Tazz, plus acces anticipat la anumite oferte.' },
      { q: 'Fashion Days are showroom fizic?', a: 'Da, în București și Cluj. Ridicarea din showroom e gratuită.' },
      { q: 'Câte zile am pentru retur?', a: '30 de zile gratuit, cu etichetă prepaid din contul tău.' },
      { q: 'Sunt produsele originale pe Fashion Days?', a: 'Da, Fashion Days e distribuitor oficial pentru brandurile din catalog (Adidas, Nike, Puma, Tommy, Guess etc.).' }
    ],
    lastUpdated: '2026-04-20'
  },
  {
    slug: 'libris',
    storeSlug: 'libris',
    title: 'Ghid Libris — Cum cumperi cărți cu reducere',
    metaTitle: 'Ghid Libris 2026 — Reduceri, Campanii si Newsletter',
    metaDescription: 'Ghid Libris 2026: calendar reduceri, cum folosești codurile promo, livrare easybox gratuită, retur 30 zile, secțiunea de cărți la 5 lei.',
    intro: 'Libris.ro este cel mai mare retailer online de cărți din România, cu peste 1 milion de titluri în română și engleză. Pentru cititori, Libris e o resursă zilnică datorită politicii agresive de reduceri — aproape niciun titlu nu se vinde la "preț de copertă", iar discount-urile medii sunt 25-45%. Catalogul include nu doar ficțiune și non-ficțiune, ci și manuale școlare, cărți pentru copii, jocuri educative și papetărie. Acest ghid îți arată cum să profiți de campaniile Libris, cum găsești "chilipirurile" la 5-15 lei, și cum abonamentul la newsletter îți aduce cele mai bune coduri promo.',
    sections: [
      {
        heading: 'Campaniile cheie de la Libris',
        body: 'Libris are un calendar constant de campanii: "Bookfest Online" (mai-iunie, corelat cu Bookfest) cu -30-50% pe întregul catalog; "Back to School" (august-septembrie) cu reduceri pe manuale, ghiozdane și papetărie; "Noaptea Cărților" (octombrie, eveniment anual) cu oferte flash și cărți la 5-15 lei; Black Friday (noiembrie) cu reduceri pe topul vânzărilor; campania "Cadouri de Crăciun" (decembrie) pentru cărți-cadou și seturi. Între campanii, Libris rulează săptămânal "Oferta săptămânii" (un titlu la -60-70%), "Weekend Sale" și "5+1 Gratis" pe anumite categorii. Abonarea la newsletter îți aduce un cod de -10% pentru prima comandă și notificări despre oferte flash.'
      },
      {
        heading: 'Cărți la 5 lei, 10 lei, 15 lei',
        body: 'Secțiunea "Cărți de la 5 lei" (în meniul principal → "Reduceri") conține titluri de stoc vechi — multe sunt cărți foarte bune care nu s-au mai cerut. Filtrează după categorie (ficțiune, business, autoajutor) pentru a găsi titluri relevante. La 10-15 lei găsești și autori contemporani. Recomandare: ia avantaj la finalul sezonului (ianuarie, iulie) când Libris face loc pentru noile apariții — atunci apar "chilipirurile" cele mai bune. Verifică și "Pachete" — seturi tematice (3-5 cărți pe un domeniu) la prețuri cu 40-60% mai mici decât suma individuală.'
      },
      {
        heading: 'Livrare, ridicare și abonament Libris Plus',
        body: 'Libris livrează prin FAN Courier (cost 14,99 lei) sau easybox (11,99 lei), gratuită peste 149 lei. Există și ridicare din showroom-ul Libris (Brașov) — gratuită. Abonamentul Libris Plus (49 lei/an) îți dă livrare gratuită nelimitată plus acces anticipat la campanii — merită dacă cumperi minim 5-6 cărți pe an. Returul e 30 de zile gratuit. Cărțile vin împachetate profesional, cu riscul de daune pe transport foarte mic.'
      }
    ],
    tips: [
      'Abonează-te la newsletter — primești -10% la prima comandă și notificări despre oferte flash',
      'Verifică "Noaptea Cărților" (octombrie) pentru titluri la 5-15 lei',
      'Caută "Pachete" tematice pentru reduceri de 40-60% pe seturi de 3-5 cărți',
      'Libris Plus (49 lei/an) merită dacă faci minim 5-6 comenzi pe an'
    ],
    faq: [
      { q: 'De la ce sumă livrarea e gratuită pe Libris?', a: 'Livrarea e gratuită pentru comenzi peste 149 lei prin FAN Courier sau easybox.' },
      { q: 'Cât durează livrarea?', a: '1-3 zile lucrătoare prin FAN Courier, 2-4 zile prin easybox.' },
      { q: 'Cărțile de 5 lei sunt în stare bună?', a: 'Da, sunt cărți noi — doar cu stoc mai vechi. Fără defecte, împachetate profesional.' },
      { q: 'Există abonament tip "Premium" la Libris?', a: 'Da, Libris Plus la 49 lei/an oferă livrare gratuită nelimitată și acces anticipat la campanii.' },
      { q: 'Pot returna o carte dacă nu-mi place?', a: 'Da, 30 de zile retur gratuit cu condiția ca produsul să fie în stare originală.' }
    ],
    lastUpdated: '2026-04-20'
  },
  {
    slug: 'elefant',
    storeSlug: 'elefant',
    title: 'Ghid Elefant — Cum cumperi cărți și produse pentru copii cu reducere',
    metaTitle: 'Ghid Elefant 2026 — Reduceri, Carti, Jucarii',
    metaDescription: 'Ghid Elefant 2026: când sunt reducerile, cum folosești codurile promo, livrare rapidă, retur 30 zile, secțiunea Outlet cu prețuri de stock.',
    intro: 'Elefant.ro este printre cei mai mari retaileri online din România pentru cărți, filme, jocuri, produse pentru copii și muzică, cu peste 500.000 de articole în catalog. Poziționarea sa diferă de Libris: Elefant pune accent pe diversitate (nu doar cărți, ci și jucării educative, DVD-uri, discuri vinil, produse pentru bebeluși) și pe reducerile agresive din "Outlet". Pentru familii cu copii mici și pentru colecționari (filme și muzică), Elefant e aproape imbatabil la raportul preț-diversitate. Acest ghid îți arată când sunt cele mai bune reduceri, cum folosești cupoanele, și de ce merită să verifici regulat secțiunea Outlet.',
    sections: [
      {
        heading: 'Campanii majore pe Elefant',
        body: 'Elefant rulează 3-4 campanii majore pe an care se remarcă: "Zilele Elefant" (martie și septembrie) cu -30-60% pe întreg catalogul timp de 4-5 zile; "Back to School" (august) cu reduceri pe manuale, rechizite și jucării educative; "Black Friday" (noiembrie) cu reduceri agresive pe cărți de top, jucării populare și electronice mici; "Crăciun Cadou" (decembrie) cu seturi-cadou și livrare express. Între campanii, "Oferta zilei" și "Oferta săptămânii" aduc 1-3 produse la -50-70%. Clubul Elefant (gratuit) îți dă 5% permanent la toate comenzile și puncte de fidelitate convertibile.'
      },
      {
        heading: 'De ce merită secțiunea Outlet',
        body: 'Outlet-ul Elefant (Meniu → "Reduceri" → "Outlet") e una din cele mai subestimate resurse. Conține produse cu stock "în lichidare" — cărți, jucării, filme — la 30-70% din prețul original. Diferența față de Libris e că Elefant are aici și jucării branded (Lego mici, Playmobil, Mattel), filme pe DVD/Blu-ray și discuri vinil la prețuri de sub 20 lei. Pentru părinții de copii mici, este o sursă bună de cadouri ieftine și cărți de povești. Filtrează după categorie și verifică recenziile — calitatea e identică cu produsele la preț întreg, diferă doar rotația stocului.'
      },
      {
        heading: 'Livrare, retur și puncte Elefant',
        body: 'Livrarea Elefant e prin curier (14,99 lei) sau locker (11,99 lei), gratuită peste 199 lei. Există ridicare din showroom-ul din București (gratuită). Retur 30 zile gratuit cu etichetă prepaid. Punctele de fidelitate (1 punct = 1 leu cheltuit) se acumulează în "Clubul Elefant" — la 50 de puncte primești un voucher de 5 lei, la 100 puncte → 12 lei. Nu e o economie dramatică, dar pentru cumpărători frecvenți (5-10 comenzi/an), vouchere-le cumulează repede.'
      }
    ],
    tips: [
      'Înscrie-te în Clubul Elefant (gratuit) pentru -5% permanent și puncte de fidelitate',
      'Verifică Outlet-ul pentru jucării branded, filme și discuri vinil sub 20 lei',
      'Campaniile "Zilele Elefant" (martie și septembrie) sunt cele mai agresive — verifică newsletter-ul',
      'La Black Friday, pune cărțile de top în wishlist cu o zi înainte — epuizarea e rapidă'
    ],
    faq: [
      { q: 'Cât durează livrarea pe Elefant?', a: '1-3 zile lucrătoare prin curier sau locker.' },
      { q: 'De la ce sumă livrarea e gratuită?', a: 'Peste 199 lei.' },
      { q: 'Clubul Elefant este gratuit?', a: 'Da. Oferă -5% permanent și puncte de fidelitate (1 punct = 1 leu cheltuit).' },
      { q: 'Pot returna o carte sau o jucărie?', a: 'Da, 30 de zile retur gratuit cu etichetă prepaid.' },
      { q: 'Elefant are showroom fizic?', a: 'Da, în București. Ridicarea de acolo e gratuită.' }
    ],
    lastUpdated: '2026-04-20'
  },
  {
    slug: 'vegis',
    storeSlug: 'vegis',
    title: 'Ghid Vegis — Cum cumperi suplimente și produse bio cu reducere',
    metaTitle: 'Ghid Vegis 2026 — Suplimente si Cosmetice Bio',
    metaDescription: 'Ghid Vegis 2026: campanii sezoniere pe suplimente (Secom, Solgar), cosmetica bio (Weleda), livrare rapidă, consultanță farmaciști.',
    intro: 'Vegis.ro este cea mai mare platformă online specializată în produse naturiste, suplimente alimentare și cosmetică bio din România. Catalogul cu peste 20.000 de produse include branduri premium ca Solgar, Secom, Herbagetica, Weleda, Lavera și Dr. Hauschka. Ceea ce diferențiază Vegis de Dr.Max sau eMAG este expertiza: multe pagini produs au recomandări scrise de farmaciști și nutriționiști, iar suportul pe chat oferă consiliere gratuită. Acest ghid îți arată când sunt reducerile, cum să combini produse în pachete la preț mai mic, și de ce merită să compari cu Dr.Max înainte de comandă.',
    sections: [
      {
        heading: 'Calendar de reduceri pe Vegis',
        body: 'Vegis are o cadență diferită de Dr.Max: campaniile sunt mai puține dar mai intense. "Zilele Secom" (trimestrial) aduc -30% pe toate produsele Secom timp de 5 zile. "Luna Solgar" (de obicei martie și noiembrie) are reduceri la premium-ul american. Black Friday și Crăciunul sunt "Mari Reduceri" cu -20-40% pe întregul catalog. Între campanii, Vegis rulează "Ofertă a săptămânii" pe câte un produs-vedetă, plus "Pachete sezoniere" (imunitate, detox, slăbire) la 15-25% mai ieftin decât suma individuală. Abonarea la newsletter e esențială — primești notificări cu 24-48h înainte de campanii.'
      },
      {
        heading: 'Pachetele Vegis — sursă subestimată de economii',
        body: 'Diferența majoră dintre Vegis și alte farmacii online e că Vegis construiește "pachete tematice" — grupuri de 2-5 produse pentru o problemă specifică (imunitate, probleme articulare, slăbire, energie). Prețul unui pachet e de regulă 15-25% mai mic decât suma produselor individuale. În plus, sunt deja filtrate de farmaciști, deci nu îți bați capul cu compatibilitatea. Pentru cumpărători fideli, există "Club Vegis" cu puncte și reduceri suplimentare — se activează după 3 comenzi.'
      },
      {
        heading: 'Livrare și consiliere',
        body: 'Livrarea Vegis e 1-3 zile lucrătoare prin FAN Courier (14,99 lei) sau easybox (11,99 lei), gratuită peste 150 lei. Consilierea gratuită pe chat e disponibilă zilnic 9-21 și merită folosită pentru suplimente scumpe — farmaciștii te ajută să eviți duplicări inutile (ex. combinația greșită de omega-3 cu anticoagulante). Returul e 14 zile, cu excepțiile uzuale pentru produse sanitare deschise. Pentru scoaterea din eroare: Vegis nu e farmacie în sens strict legal — deci nu poți comanda medicamente Rx, doar OTC, suplimente, cosmetică și alimente funcționale.'
      }
    ],
    tips: [
      'Abonează-te la newsletter pentru notificări cu 24-48h înainte de campaniile Secom/Solgar',
      'Verifică "Pachetele" tematice — economie de 15-25% vs. produse individuale',
      'Folosește chat-ul de consiliere gratuit înainte să comanzi suplimente scumpe',
      'Compară prețurile cu Dr.Max pentru același produs — uneori diferența e 10-20%'
    ],
    faq: [
      { q: 'Vegis este farmacie?', a: 'Este un magazin specializat în suplimente, produse naturiste și cosmetica bio, nu o farmacie clasică. Nu poate elibera medicamente Rx.' },
      { q: 'Pot primi consiliere gratuită?', a: 'Da, pe chat 9-21 zilnic, oferită de farmaciști și nutriționiști.' },
      { q: 'De la ce sumă livrarea e gratuită?', a: 'Peste 150 lei.' },
      { q: 'Câte zile am pentru retur?', a: '14 zile pentru produse nedeschise în ambalaj original.' },
      { q: 'Sunt produsele originale?', a: 'Da, Vegis lucrează direct cu distribuitorii oficiali ai brandurilor din catalog (Solgar, Secom, Weleda etc.).' }
    ],
    lastUpdated: '2026-04-20'
  },
  {
    slug: 'mathaus',
    storeSlug: 'mathaus',
    title: 'Ghid MatHaus — Cum cumperi materiale de construcții și bricolaj cu reducere',
    metaTitle: 'Ghid MatHaus 2026 — Materiale Constructii si Bricolaj',
    metaDescription: 'Ghid MatHaus 2026: când sunt reducerile pe materiale de construcții, livrare mare volum, tips pentru renovări la preț mic.',
    intro: 'MatHaus.ro este unul dintre cele mai mari magazine online de materiale de construcții, amenajări interioare și bricolaj din România. Catalogul acoperă tot ce îți trebuie pentru un proiect DIY sau renovare completă: vopsele, gresie, faianță, instalații sanitare, scule electrice, iluminat, mobilier de grădină. Pentru cumpărătorul atent la buget, MatHaus poate aduce economii semnificative față de Dedeman sau Leroy Merlin, mai ales la campaniile majore. Acest ghid îți explică calendarul reducerilor, cum funcționează livrarea de volume mari, și ce să verifici înainte de o comandă mare pentru renovare.',
    sections: [
      {
        heading: 'Când sunt reducerile mari pe MatHaus',
        body: 'MatHaus urmează sezonul construcțiilor: "Primăvara renovărilor" (martie-aprilie) are -20-40% pe vopsele, gresie, faianță și scule; "Vara amenajărilor" (iunie-iulie) reduce prețurile la mobilier grădină, pavaj, instalații irigație; "Back to Home" (septembrie) este pentru iluminat și amenajări interioare; "Black Friday" (noiembrie) — reduceri agresive pe scule electrice și centrale termice (stoc limitat, se epuizează rapid). Campaniile flash "Doar 48h" apar de 2-3 ori pe lună pe câte o categorie. Newsletter-ul MatHaus e esențial pentru a prinde flash-urile.'
      },
      {
        heading: 'Livrare pentru volume mari',
        body: 'MatHaus are două tipuri de livrare. Pentru produse mici (scule de mână, țevi mici, accesorii), livrarea e prin curier standard (14,99 lei, gratuită peste 199 lei), în 1-3 zile. Pentru produse mari (gresie, faianță, ușă, centrală termică, mobilier grădină), livrarea se face prin curier dedicat cu cost calculat pe dimensiune și distanță (între 49 și 299 lei, depinde de județ). Pentru produsele voluminoase, merită să verifici dacă magazinul MatHaus are punct fizic în orașul tău — ridicarea e gratuită. Pentru un șantier, comandă pe categorii separate ca să ai termene de livrare realiste.'
      },
      {
        heading: 'Tips pentru renovări la preț mic',
        body: 'Pentru o renovare, MatHaus poate deveni scump rapid dacă nu planifici. Trei reguli: (1) Fă-ți lista completă înainte de comandă, cu suprafețe și cantități — cere ajutor pe chat pentru calcule; (2) Comandă gresia/faianța cu 10% surplus pentru tăieri și spargeri — MatHaus acceptă retur de gresie neutilizată 14 zile de la livrare; (3) Pentru vopsea, nu cumpăra "doze de probă" separate — ia direct 2-3 l din culoarea finală (e mai ieftin per mp). Verifică și secțiunea "Stoc Limitat" — produse cu defecte minore (etichete rupte, ambalaj avariat) la -30-50%.'
      }
    ],
    tips: [
      'Abonează-te la newsletter pentru flash-urile "Doar 48h" pe scule și vopsele',
      'Pentru gresie, comandă cu 10% surplus — returul e acceptat pe cantitățile neutilizate',
      'Verifică dacă ai punct MatHaus fizic în oraș — ridicarea e gratuită pentru volume mari',
      'Secțiunea "Stoc Limitat" are produse cu defecte minore la -30-50%'
    ],
    faq: [
      { q: 'Cât costă livrarea pentru produse mari (gresie, centrală)?', a: 'Între 49 și 299 lei, depinde de județ și volumul produsului. Calculul se face la checkout.' },
      { q: 'Pot ridica gratuit dintr-un punct MatHaus?', a: 'Da, dacă ai punct fizic în orașul tău. Lista punctelor e pe site la secțiunea "Ridicare din magazin".' },
      { q: 'Câte zile am pentru retur?', a: '14 zile pentru produse nedeschise. Pentru gresie și faianță, se acceptă returul cantităților neutilizate.' },
      { q: 'MatHaus are consiliere tehnică?', a: 'Da, pe chat în program (9-18) sau prin telefon. Merită pentru calcul de cantități la renovare.' },
      { q: 'Când sunt cele mai mari reduceri?', a: 'Primăvara (martie-aprilie), vara (iunie-iulie) și Black Friday (noiembrie) — MatHaus urmează sezonul construcțiilor.' }
    ],
    lastUpdated: '2026-04-20'
  }
]

export function getStoreGuideBySlug(slug: string): StoreGuide | undefined {
  return STORE_GUIDES.find(g => g.slug === slug)
}

export function getAllStoreGuideSlugs(): string[] {
  return STORE_GUIDES.map(g => g.slug)
}
