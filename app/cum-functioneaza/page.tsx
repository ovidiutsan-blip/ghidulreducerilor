import { Metadata } from 'next'
import Link from 'next/link'
import Breadcrumb from '@/components/Breadcrumb'
import { Search, Copy, ShoppingCart, Wallet, HelpCircle } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Cum funcționează GhidulReducerilor.ro — ghid pas cu pas + FAQ',
  description:
    'Cum folosești codurile de reducere și deal-urile de pe GhidulReducerilor.ro în 4 pași simpli. FAQ cu răspunsuri la întrebările frecvente despre coduri promoționale, afiliere și economii.',
  alternates: { canonical: '/cum-functioneaza' },
  openGraph: {
    title: 'Cum funcționează GhidulReducerilor.ro',
    description:
      'Ghid pas cu pas cum să folosești codurile de reducere și deal-urile noastre. Plus FAQ.',
    url: 'https://ghidulreducerilor.ro/cum-functioneaza',
    type: 'article',
  },
}

type FaqItem = { q: string; a: string }

const FAQ: FaqItem[] = [
  {
    q: 'Ce este un cod de reducere și de unde vin?',
    a: 'Un cod de reducere (numit și cod promoțional, cupon sau voucher) este o secvență scurtă de litere și cifre pe care o introduci la checkout pentru a primi o reducere sau un beneficiu suplimentar. Codurile vin direct de la magazine ca parte din campaniile lor de marketing (promoții sezoniere, lansări de produse, oferte pentru clienți noi) și le publicăm pe GhidulReducerilor.ro pe măsură ce le verificăm.',
  },
  {
    q: 'Este gratuit să folosesc site-ul?',
    a: 'Da, absolut gratuit. Nu îți cerem cont, card sau vreo plată pentru a vedea sau folosi codurile. Ne finanțăm exclusiv din comisioanele de afiliere pe care le primim de la magazine atunci când cumperi prin link-urile noastre — dar asta nu îți crește prețul cu nimic. Plătești exact ca și cum ai fi intrat direct pe site-ul magazinului.',
  },
  {
    q: 'Codurile chiar funcționează sau sunt expirate?',
    a: 'Toate codurile publicate sunt verificate înainte de a fi adăugate. În plus, pipeline-ul nostru zilnic re-verifică codurile active și le dezactivează pe cele expirate. Dacă totuși întâlnești un cod care nu funcționează, scrie-ne — îl investigăm și îl actualizăm rapid.',
  },
  {
    q: 'Câte reduceri pot obține cu un cod?',
    a: 'Depinde de magazin și campanie. Unele coduri oferă procent (ex: -10%), altele sumă fixă (ex: 50 lei reducere), iar altele beneficii (transport gratuit, cadou la comandă). Pe fiecare cupon scrie exact ce obții — citește descrierea înainte de a-l folosi. În general, reducerile medii sunt între 5% și 25%, cu vârfuri la 40-60% în Black Friday.',
  },
  {
    q: 'Pot folosi mai multe coduri la aceeași comandă?',
    a: 'De regulă NU — majoritatea magazinelor permit un singur cod per comandă. Unele magazine permit totuși să combini un cod promoțional cu reducerea automată a unui produs deja aflat la ofertă. Dacă ai două coduri valide, încearcă-le pe rând și alege-l pe cel care îți dă reducerea mai mare.',
  },
  {
    q: 'Codurile au expirare?',
    a: 'Da, aproape toate codurile au o dată de expirare (uneori vizibilă direct pe cupon). Încearcă să-l folosești cât mai repede după ce îl găsești. De asemenea, unele coduri au limită de utilizări totale — când se epuizează, magazinul le dezactivează chiar dacă data de expirare nu a trecut încă.',
  },
  {
    q: 'De ce nu văd toate magazinele din România aici?',
    a: 'Adăugăm doar magazine la care avem parteneriat activ prin rețelele de afiliere (Profitshare.ro și 2Performant.ro). Extindem lista continuu pe măsură ce suntem aprobați la programe noi. Dacă lipsește un magazin pe care vrei să-l vezi aici, scrie-ne și-l punem pe lista de priorități.',
  },
  {
    q: 'Ce diferență e între un „cod promo" și un „deal"?',
    a: 'Un cod promo e o secvență alfanumerică pe care o introduci la checkout. Un „deal" (sau „ofertă") e un produs pe care magazinul îl are deja la preț redus — nu ai nevoie de cod, doar dai click pe link-ul nostru și prețul este deja redus automat în coșul tău. Ambele sunt modalități valide de a economisi; doar mecanica e diferită.',
  },
  {
    q: 'Cum mă asigur că primesc reducerea înainte de a plasa comanda?',
    a: 'Verifică întotdeauna totalul din coș ÎNAINTE de a finaliza plata. Dacă aplici un cod și reducerea nu apare, nu continua comanda — încearcă un cod alternativ sau contactează suportul magazinului. Screenshot-ul prețului inițial plus cel al prețului redus e o dovadă utilă în caz de reclamație.',
  },
  {
    q: 'Ce fac dacă găsesc un cod care nu e pe site?',
    a: 'Trimite-ne cod-ul și magazinul și-l verificăm. Dacă e valid, îl adăugăm pe site cu credit pentru tine (dacă vrei). Suntem deschiși la contribuții — comunitatea e mai eficientă decât orice pipeline automatizat.',
  },
]

const STEPS = [
  {
    icon: Search,
    title: 'Caută magazinul sau categoria',
    desc: 'Folosește bara de căutare, meniul de magazine sau categoriile de pe homepage pentru a găsi reducerile care te interesează. Poți filtra după tip (coduri promo vs. deal-uri) și după magazinul preferat.',
  },
  {
    icon: Copy,
    title: 'Copiază codul sau click pe deal',
    desc: 'Pentru coduri: apasă butonul „Copiază cod" — îl salvăm automat în clipboard. Pentru deal-uri: apasă „Vezi oferta" și te redirectăm direct pe pagina produsului redus pe site-ul magazinului.',
  },
  {
    icon: ShoppingCart,
    title: 'Aplică codul la checkout',
    desc: 'Adaugă produsele în coș pe site-ul magazinului, iar la finalizarea comenzii lipește codul în câmpul „Cod promoțional" sau „Voucher". Verifică ca reducerea să apară în totalul comenzii înainte să plătești.',
  },
  {
    icon: Wallet,
    title: 'Finalizează și economisești',
    desc: 'Plasează comanda. Reducerea se aplică automat asupra prețului final. Nu există costuri suplimentare pentru tine — plătești exact prețul redus. Noi primim comision de la magazin, plătit din partea lor.',
  },
]

export default function CumFunctioneazaPage() {
  const faqSchema = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: FAQ.map(({ q, a }) => ({
      '@type': 'Question',
      name: q,
      acceptedAnswer: {
        '@type': 'Answer',
        text: a,
      },
    })),
  }

  const howToSchema = {
    '@context': 'https://schema.org',
    '@type': 'HowTo',
    name: 'Cum folosești un cod de reducere de pe GhidulReducerilor.ro',
    description:
      'Ghid pas cu pas cum să cauți, copiezi și aplici un cod de reducere pentru a economisi la cumpărăturile online în România.',
    step: STEPS.map((s, i) => ({
      '@type': 'HowToStep',
      position: i + 1,
      name: s.title,
      text: s.desc,
    })),
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Breadcrumb items={[{ label: 'Cum funcționează' }]} />

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(howToSchema) }}
      />

      <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-neutral-900 mb-4">
        Cum funcționează GhidulReducerilor.ro
      </h1>
      <p className="text-lg text-neutral-600 mb-10 leading-relaxed">
        Pe scurt: te ajutăm să economisești la cumpărăturile online din România. Cauți magazinul,
        copiezi codul, aplici la checkout — și plătești mai puțin. Mai jos sunt cei 4 pași detaliat
        și răspunsuri la cele mai frecvente întrebări.
      </p>

      {/* 4 pași */}
      <section aria-labelledby="cei-4-pasi" className="mb-12">
        <h2 id="cei-4-pasi" className="font-display font-bold text-2xl text-neutral-900 mb-6">
          Cei 4 pași simpli
        </h2>
        <ol className="space-y-5">
          {STEPS.map((s, i) => {
            const Icon = s.icon
            return (
              <li
                key={i}
                className="flex gap-4 p-5 rounded-2xl border border-neutral-200 bg-white"
              >
                <div className="shrink-0 w-12 h-12 bg-brand-red/10 text-brand-red rounded-xl flex items-center justify-center">
                  <Icon className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg text-neutral-900 mb-1">
                    <span className="text-brand-red mr-2">{i + 1}.</span>
                    {s.title}
                  </h3>
                  <p className="text-neutral-600 leading-relaxed">{s.desc}</p>
                </div>
              </li>
            )
          })}
        </ol>
      </section>

      {/* FAQ */}
      <section aria-labelledby="faq" className="mb-12">
        <h2
          id="faq"
          className="font-display font-bold text-2xl text-neutral-900 mb-6 flex items-center gap-2"
        >
          <HelpCircle className="w-6 h-6 text-brand-red" />
          Întrebări frecvente (FAQ)
        </h2>
        <div className="divide-y divide-neutral-200 border border-neutral-200 rounded-2xl bg-white">
          {FAQ.map((item, i) => (
            <details key={i} className="group p-5 [&_summary]:cursor-pointer">
              <summary className="flex items-start justify-between gap-4 font-semibold text-neutral-900 list-none">
                <span className="leading-relaxed">{item.q}</span>
                <span
                  aria-hidden="true"
                  className="shrink-0 text-brand-red text-xl leading-none group-open:rotate-45 transition-transform"
                >
                  +
                </span>
              </summary>
              <p className="mt-3 text-neutral-600 leading-relaxed">{item.a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="rounded-2xl bg-gradient-to-br from-brand-red/5 to-brand-red/0 border border-brand-red/20 p-6 sm:p-8 text-center">
        <h2 className="font-display font-bold text-xl text-neutral-900 mb-2">
          Gata să economisești?
        </h2>
        <p className="text-neutral-600 mb-5">
          Explorează cele mai populare magazine și găsește cupoane active chiar acum.
        </p>
        <div className="flex flex-wrap gap-3 justify-center">
          <Link
            href="/"
            className="inline-flex items-center gap-2 bg-brand-red hover:bg-brand-red-dark text-white font-semibold px-5 py-3 rounded-xl transition-colors"
          >
            Vezi toate magazinele
          </Link>
          <Link
            href="/blog"
            className="inline-flex items-center gap-2 bg-white hover:bg-neutral-50 text-neutral-900 font-semibold px-5 py-3 rounded-xl border border-neutral-300 transition-colors"
          >
            Citește blogul
          </Link>
        </div>
      </section>
    </div>
  )
}
