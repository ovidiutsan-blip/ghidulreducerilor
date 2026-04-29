import { Metadata } from 'next'
import Link from 'next/link'
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  Flame,
  HelpCircle,
  ShoppingBag,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import Breadcrumb from '@/components/Breadcrumb'
import {
  BF_CURRENT,
  BF_FAQ,
  BF_HISTORY,
  BF_PREP_STEPS,
  BF_STORES,
  getAllParticipatingStores,
} from '@/lib/black-friday'
import { getStoreBySlug } from '@/lib/data'

const PAGE_TITLE = `Black Friday ${BF_CURRENT.an} România — Când începe, magazine participante și strategii`
const PAGE_DESCRIPTION = `Ghid complet pentru Black Friday ${BF_CURRENT.an} în România: data exactă eMAG, Fashion Days, Notino și Answear, istoric 2023-2025, strategie de pregătire în 4 pași, sfaturi pentru reduceri reale.`
const CANONICAL = 'https://ghidulreducerilor.ro/black-friday'

export const metadata: Metadata = {
  title: PAGE_TITLE,
  description: PAGE_DESCRIPTION,
  alternates: { canonical: CANONICAL },
  openGraph: {
    title: PAGE_TITLE,
    description: PAGE_DESCRIPTION,
    url: CANONICAL,
    type: 'website',
    locale: 'ro_RO',
  },
  twitter: {
    card: 'summary_large_image',
    title: PAGE_TITLE,
    description: PAGE_DESCRIPTION,
  },
}

function formatRODate(iso: string): string {
  const d = new Date(iso)
  const luni = [
    'ianuarie', 'februarie', 'martie', 'aprilie', 'mai', 'iunie',
    'iulie', 'august', 'septembrie', 'octombrie', 'noiembrie', 'decembrie',
  ]
  const zileSaptamana = ['duminică', 'luni', 'marți', 'miercuri', 'joi', 'vineri', 'sâmbătă']
  return `${zileSaptamana[d.getDay()]}, ${d.getDate()} ${luni[d.getMonth()]} ${d.getFullYear()}`
}

export default function BlackFridayPage() {
  const earlyStores = BF_STORES.filter(s => s.wave === 'early' || s.wave === 'both')
  const globalStores = BF_STORES.filter(s => s.wave === 'global' || s.wave === 'both')
  const allStores = getAllParticipatingStores()

  // JSON-LD: Event + FAQPage + BreadcrumbList + WebPage
  const jsonLd = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebPage',
        '@id': `${CANONICAL}#webpage`,
        url: CANONICAL,
        name: PAGE_TITLE,
        description: PAGE_DESCRIPTION,
        inLanguage: 'ro',
        isPartOf: { '@id': 'https://ghidulreducerilor.ro#website' },
      },
      {
        '@type': 'Event',
        '@id': `${CANONICAL}#event-early`,
        name: `Black Friday România ${BF_CURRENT.an} (eMAG)`,
        description: `Evenimentul principal Black Friday din România, deschis de eMAG și Fashion Days. Reduceri până la -70% pe electronice, fashion și electrocasnice.`,
        startDate: BF_CURRENT.earlyBFDate,
        endDate: BF_CURRENT.earlyBFEndDate,
        eventAttendanceMode: 'https://schema.org/OnlineEventAttendanceMode',
        eventStatus: 'https://schema.org/EventScheduled',
        location: {
          '@type': 'VirtualLocation',
          url: 'https://www.emag.ro/black-friday',
        },
        organizer: {
          '@type': 'Organization',
          name: 'eMAG',
          url: 'https://www.emag.ro',
        },
        image: 'https://ghidulreducerilor.ro/og-black-friday.png',
        offers: {
          '@type': 'Offer',
          availability: 'https://schema.org/InStock',
          url: 'https://ghidulreducerilor.ro/black-friday',
          priceCurrency: 'RON',
          validFrom: BF_CURRENT.earlyBFDate,
        },
      },
      {
        '@type': 'Event',
        '@id': `${CANONICAL}#event-global`,
        name: `Black Friday Global ${BF_CURRENT.an} (Cyber Week)`,
        description: `Black Friday-ul global cu Notino, Answear și brand-uri internaționale. Cyber Monday pe 30 noiembrie ${BF_CURRENT.an}.`,
        startDate: BF_CURRENT.globalBFDate,
        endDate: BF_CURRENT.globalBFEndDate,
        eventAttendanceMode: 'https://schema.org/OnlineEventAttendanceMode',
        eventStatus: 'https://schema.org/EventScheduled',
        location: {
          '@type': 'VirtualLocation',
          url: 'https://ghidulreducerilor.ro/black-friday',
        },
        image: 'https://ghidulreducerilor.ro/og-black-friday.png',
      },
      {
        '@type': 'FAQPage',
        mainEntity: BF_FAQ.map(f => ({
          '@type': 'Question',
          name: f.q,
          acceptedAnswer: { '@type': 'Answer', text: f.a },
        })),
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          {
            '@type': 'ListItem',
            position: 1,
            name: 'Acasă',
            item: 'https://ghidulreducerilor.ro',
          },
          {
            '@type': 'ListItem',
            position: 2,
            name: `Black Friday ${BF_CURRENT.an}`,
            item: CANONICAL,
          },
        ],
      },
    ],
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumb items={[{ label: `Black Friday ${BF_CURRENT.an}` }]} />

        {/* Hero */}
        <header className="mb-10 mt-4">
          <div className="inline-flex items-center gap-2 bg-neutral-900 text-white text-xs font-semibold px-3 py-1.5 rounded-full mb-4">
            <Flame className="w-3.5 h-3.5 text-brand-red" />
            Pagină actualizată · {formatRODate(BF_CURRENT.lastUpdated)}
          </div>
          <h1 className="font-display font-bold text-3xl sm:text-5xl text-neutral-900 leading-tight mb-4">
            Black Friday {BF_CURRENT.an} în România
          </h1>
          <p className="text-lg sm:text-xl text-neutral-700 leading-relaxed max-w-3xl">
            Când începe, ce magazine participă, cum identifici reducerile reale și strategia
            completă de pregătire. Pagina se actualizează pe 1 iulie și 1 octombrie {BF_CURRENT.an}
            cu datele oficiale confirmate.
          </p>
        </header>

        {/* Key dates box */}
        <section className="mb-12">
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="bg-gradient-to-br from-neutral-900 to-neutral-800 text-white rounded-2xl p-6 sm:p-7">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-9 h-9 bg-brand-red rounded-lg flex items-center justify-center">
                  <CalendarDays className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs uppercase tracking-wider text-white/60 font-semibold">
                  Val 1 · BF România
                </span>
              </div>
              <p className="font-display font-bold text-2xl sm:text-3xl mb-2">
                {formatRODate(BF_CURRENT.earlyBFDate)}
              </p>
              <p className="text-white/80 text-sm leading-relaxed mb-3">
                Deschis de eMAG și Fashion Days. Electronice, electrocasnice, fashion
                mainstream. Durează până duminică {formatRODate(BF_CURRENT.earlyBFEndDate).split(',')[1].trim()}.
              </p>
              <div className="inline-block bg-white/10 text-white text-xs font-medium px-3 py-1 rounded-full">
                📌 Dată estimată — confirmarea oficială în octombrie {BF_CURRENT.an}
              </div>
            </div>

            <div className="bg-gradient-to-br from-brand-red to-brand-red-dark text-white rounded-2xl p-6 sm:p-7">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-9 h-9 bg-white/20 rounded-lg flex items-center justify-center">
                  <CalendarDays className="w-5 h-5 text-white" />
                </div>
                <span className="text-xs uppercase tracking-wider text-white/70 font-semibold">
                  Val 2 · BF Global + Cyber Monday
                </span>
              </div>
              <p className="font-display font-bold text-2xl sm:text-3xl mb-2">
                {formatRODate(BF_CURRENT.globalBFDate)}
              </p>
              <p className="text-white/90 text-sm leading-relaxed mb-3">
                Notino, Answear și brand-urile internaționale. Continuă cu Cyber Monday pe{' '}
                {formatRODate(BF_CURRENT.globalBFEndDate).split(',')[1].trim()}.
              </p>
              <div className="inline-block bg-white/20 text-white text-xs font-medium px-3 py-1 rounded-full">
                🌍 Dată confirmată (vinerea de după Thanksgiving US)
              </div>
            </div>
          </div>
        </section>

        {/* Editorial intro */}
        <section className="prose prose-lg prose-neutral max-w-none mb-14">
          <p className="text-neutral-700 leading-relaxed">
            Black Friday în România a devenit unul dintre cele mai mari evenimente comerciale ale
            anului. În {BF_CURRENT.an}, piața se împarte ca în anii anteriori în două valuri
            majore: Black Friday „românesc", deschis tradițional de eMAG în prima vineri din
            noiembrie, și Black Friday global, aliniat cu Thanksgiving-ul american, în ultimul
            weekend al lunii. Dacă înțelegi diferența dintre cele două, poți prinde reducerile
            potrivite pentru fiecare categorie — electronice în primul val, parfumerie și fashion
            premium în al doilea.
          </p>
          <p className="text-neutral-700 leading-relaxed">
            Cumpără strategic, nu impulsiv. În ghidul de mai jos găsești datele oficiale (pe măsură
            ce se confirmă), lista magazinelor partenere verificate, istoricul ultimilor trei ani
            cu volume și highlight-uri reale, cei 4 pași de pregătire pe care îi recomandăm clienților
            noștri și răspunsurile la cele mai frecvente întrebări despre returul,
            verificarea prețurilor și cumularea cu coduri promoționale.
          </p>
        </section>

        {/* Prep steps */}
        <section className="mb-14">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-brand-red/10 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-brand-red" />
            </div>
            <div>
              <h2 className="font-display font-bold text-xl sm:text-2xl text-neutral-900">
                Strategie de pregătire în 4 pași
              </h2>
              <p className="text-sm text-neutral-500">Așa cumperi cu reduceri reale, nu reduceri cosmetice</p>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            {BF_PREP_STEPS.map((step, i) => (
              <div
                key={i}
                className="bg-white border border-neutral-200 rounded-2xl p-6 hover:border-brand-red/30 hover:shadow-md transition-all"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-brand-red/10 to-amber-100 rounded-xl flex items-center justify-center text-2xl">
                    {step.icon}
                  </div>
                  <span className="font-display font-bold text-brand-red text-sm uppercase tracking-wider">
                    Pasul {i + 1}
                  </span>
                </div>
                <h3 className="font-display font-bold text-lg text-neutral-900 mb-2">
                  {step.titlu}
                </h3>
                <p className="text-sm text-neutral-700 leading-relaxed">{step.descriere}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Participating stores — Early BF */}
        <section className="mb-14">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-yellow-100 rounded-xl flex items-center justify-center">
              <ShoppingBag className="w-5 h-5 text-yellow-700" />
            </div>
            <div>
              <h2 className="font-display font-bold text-xl sm:text-2xl text-neutral-900">
                Magazine în Val 1 · BF România ({formatRODate(BF_CURRENT.earlyBFDate).split(',')[1]?.trim()})
              </h2>
              <p className="text-sm text-neutral-500">
                {earlyStores.length} parteneri verificați — deschid campania în prima vineri din noiembrie
              </p>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {earlyStores.map(bfStore => {
              const store = getStoreBySlug(bfStore.slug)
              return (
                <Link
                  key={bfStore.slug}
                  href={`/reduceri/${bfStore.slug}`}
                  className="group bg-white border border-neutral-200 rounded-2xl p-5 hover:border-brand-red hover:shadow-md transition-all"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div
                      className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl shrink-0"
                      style={{ backgroundColor: `${bfStore.culoare}20` }}
                    >
                      {bfStore.logoEmoji}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-display font-bold text-neutral-900 truncate">
                        {bfStore.nume}
                      </p>
                      <p className="text-xs font-semibold text-brand-red">
                        {bfStore.discountTipic}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-neutral-600 leading-relaxed mb-3 line-clamp-3">
                    {bfStore.notaScurta}
                  </p>
                  <div className="flex items-center gap-1 text-brand-red text-sm font-semibold group-hover:gap-2 transition-all">
                    Vezi oferte {store?.nume || bfStore.nume}
                    <ArrowRight className="w-4 h-4" />
                  </div>
                </Link>
              )
            })}
          </div>
        </section>

        {/* Participating stores — Global BF */}
        <section className="mb-14">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-neutral-900 rounded-xl flex items-center justify-center">
              <Flame className="w-5 h-5 text-brand-red" />
            </div>
            <div>
              <h2 className="font-display font-bold text-xl sm:text-2xl text-neutral-900">
                Magazine în Val 2 · BF Global ({formatRODate(BF_CURRENT.globalBFDate).split(',')[1]?.trim()})
              </h2>
              <p className="text-sm text-neutral-500">
                {globalStores.length} parteneri — aliniați la BF-ul internațional, până la Cyber Monday
              </p>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {globalStores.map(bfStore => (
              <Link
                key={bfStore.slug}
                href={`/reduceri/${bfStore.slug}`}
                className="group bg-white border border-neutral-200 rounded-2xl p-5 hover:border-brand-red hover:shadow-md transition-all"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl shrink-0"
                    style={{ backgroundColor: `${bfStore.culoare}20` }}
                  >
                    {bfStore.logoEmoji}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-display font-bold text-neutral-900 truncate">
                      {bfStore.nume}
                    </p>
                    <p className="text-xs font-semibold text-brand-red">
                      {bfStore.discountTipic}
                    </p>
                  </div>
                </div>
                <p className="text-sm text-neutral-600 leading-relaxed mb-3 line-clamp-3">
                  {bfStore.notaScurta}
                </p>
                <div className="flex items-center gap-1 text-brand-red text-sm font-semibold group-hover:gap-2 transition-all">
                  Vezi oferte {bfStore.nume}
                  <ArrowRight className="w-4 h-4" />
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* History */}
        <section className="mb-14">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-amber-100 rounded-xl flex items-center justify-center text-xl">
              📊
            </div>
            <div>
              <h2 className="font-display font-bold text-xl sm:text-2xl text-neutral-900">
                Istoric Black Friday în România (2023-2025)
              </h2>
              <p className="text-sm text-neutral-500">Date și cifre din edițiile anterioare</p>
            </div>
          </div>
          <div className="space-y-4">
            {BF_HISTORY.map(entry => (
              <article
                key={entry.an}
                className="bg-white border border-neutral-200 rounded-2xl p-6 hover:border-neutral-300 transition-colors"
              >
                <div className="flex items-start gap-4 flex-wrap">
                  <div className="w-16 h-16 bg-neutral-900 text-white rounded-xl flex items-center justify-center font-display font-bold text-xl shrink-0">
                    {entry.an}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap mb-2">
                      <h3 className="font-display font-bold text-lg text-neutral-900">
                        {formatRODate(entry.dataBF)}
                      </h3>
                      <span className="text-xs font-medium text-neutral-500 bg-neutral-100 px-2 py-1 rounded-full">
                        {entry.durata}
                      </span>
                    </div>
                    <p className="text-sm text-neutral-700 leading-relaxed">
                      {entry.highlights}
                    </p>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* Tips callout */}
        <section className="mb-14">
          <div className="bg-gradient-to-br from-neutral-900 to-neutral-800 text-white rounded-3xl p-8 sm:p-10">
            <div className="flex items-center gap-3 mb-6">
              <Sparkles className="w-6 h-6 text-brand-red" />
              <h2 className="font-display font-bold text-xl sm:text-2xl">
                Cum verifici dacă o reducere e reală
              </h2>
            </div>
            <ul className="space-y-4">
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-brand-red shrink-0 mt-0.5" />
                <span className="text-white/90 leading-relaxed">
                  <strong className="text-white">Compară cu prețul din ultimele 90 de zile</strong> —
                  dacă reducerea te duce la un preț mai mare decât minimul din ultima perioadă,
                  nu e o afacere reală.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-brand-red shrink-0 mt-0.5" />
                <span className="text-white/90 leading-relaxed">
                  <strong className="text-white">Ignoră procentul afișat</strong> — uită-te la
                  prețul final. 60% reducere de la un preț umflat poate fi mai scump decât 20%
                  reducere de la un preț onest.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-brand-red shrink-0 mt-0.5" />
                <span className="text-white/90 leading-relaxed">
                  <strong className="text-white">Caută același produs pe 2-3 magazine</strong> —
                  dacă eMAG vinde la 1.200 lei și Altex la 1.250 lei, reducerea e legitimă. Dacă
                  eMAG e la 1.200 lei și Altex la 950 lei, prețul de referință e inventat.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-brand-red shrink-0 mt-0.5" />
                <span className="text-white/90 leading-relaxed">
                  <strong className="text-white">Nu te grăbi în primele 30 de minute</strong> —
                  reducerile bune durează toată ziua sau tot weekendul. Panica artificială (&bdquo;mai
                  sunt 2 bucăți!&rdquo;) e de cele mai multe ori un truc al platformei.
                </span>
              </li>
            </ul>
          </div>
        </section>

        {/* FAQ */}
        <section className="mb-14">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-brand-red/10 rounded-xl flex items-center justify-center">
              <HelpCircle className="w-5 h-5 text-brand-red" />
            </div>
            <div>
              <h2 className="font-display font-bold text-xl sm:text-2xl text-neutral-900">
                Întrebări frecvente despre Black Friday {BF_CURRENT.an}
              </h2>
              <p className="text-sm text-neutral-500">Tot ce trebuie să știi înainte să cumperi</p>
            </div>
          </div>
          <div className="space-y-3">
            {BF_FAQ.map((item, i) => (
              <details
                key={i}
                className="group rounded-xl border border-neutral-200 bg-white hover:border-brand-red/30 transition-colors"
              >
                <summary className="flex items-start justify-between gap-4 p-5 cursor-pointer list-none">
                  <h3 className="font-display font-semibold text-neutral-900 text-base leading-snug">
                    {item.q}
                  </h3>
                  <span className="shrink-0 w-6 h-6 rounded-full bg-neutral-100 flex items-center justify-center text-neutral-500 group-open:rotate-45 group-open:bg-brand-red group-open:text-white transition-all">
                    +
                  </span>
                </summary>
                <div className="px-5 pb-5 text-neutral-700 leading-relaxed">{item.a}</div>
              </details>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="bg-gradient-to-br from-brand-red to-brand-red-dark rounded-3xl p-8 sm:p-12 text-center text-white">
          <h2 className="font-display font-bold text-2xl sm:text-3xl mb-3">
            Nu rata Black Friday {BF_CURRENT.an}
          </h2>
          <p className="text-white/80 mb-8 max-w-xl mx-auto">
            Abonează-te la alertele GhidulReducerilor.ro — primești notificare în momentul în care
            produsele tale prioritare intră în promoție. Fără spam, doar ofertele relevante.
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Link
              href="/abonare-alerte"
              className="inline-flex items-center gap-2 bg-white text-brand-red font-display font-semibold px-6 py-3 rounded-full hover:bg-neutral-50 transition-colors"
            >
              Setează alerte gratuite
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/categorii"
              className="inline-flex items-center gap-2 bg-white/10 border border-white/30 text-white font-display font-semibold px-6 py-3 rounded-full hover:bg-white/20 transition-colors backdrop-blur-sm"
            >
              Vezi toate categoriile
            </Link>
          </div>
        </section>

        {/* Related */}
        <section className="mt-14 pt-10 border-t border-neutral-200">
          <h2 className="font-display font-bold text-lg text-neutral-900 mb-4">
            Vezi și alte ghiduri
          </h2>
          <div className="flex flex-wrap gap-2">
            <Link
              href="/ghiduri"
              className="inline-flex items-center gap-2 bg-white border border-neutral-200 hover:border-brand-red hover:text-brand-red text-sm font-medium text-neutral-700 px-4 py-2 rounded-full transition-colors"
            >
              📖 Ghiduri magazine
            </Link>
            <Link
              href="/categorii"
              className="inline-flex items-center gap-2 bg-white border border-neutral-200 hover:border-brand-red hover:text-brand-red text-sm font-medium text-neutral-700 px-4 py-2 rounded-full transition-colors"
            >
              🗂️ Categorii tematice
            </Link>
            <Link
              href="/blog"
              className="inline-flex items-center gap-2 bg-white border border-neutral-200 hover:border-brand-red hover:text-brand-red text-sm font-medium text-neutral-700 px-4 py-2 rounded-full transition-colors"
            >
              📝 Blog & articole
            </Link>
            <Link
              href="/cod-reducere/emag"
              className="inline-flex items-center gap-2 bg-white border border-neutral-200 hover:border-brand-red hover:text-brand-red text-sm font-medium text-neutral-700 px-4 py-2 rounded-full transition-colors"
            >
              🏷️ Coduri eMAG
            </Link>
          </div>
          <p className="text-xs text-neutral-500 mt-6">
            Monitorizăm {allStores.length} magazine partenere pentru Black Friday {BF_CURRENT.an}.
            Pagina se actualizează pe 1 iulie și 1 octombrie {BF_CURRENT.an} cu datele confirmate
            oficial.
          </p>
        </section>
      </div>
    </>
  )
}
