import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import DealCard from '@/components/DealCard'
import PromoCodeCard from '@/components/PromoCodeCard'
import Breadcrumb from '@/components/Breadcrumb'
import {
  getDealsByStore,
  getCodesByStore,
  getStoreBySlug,
  getAllStoreSlugs,
} from '@/lib/data'
import { getCurrentMonthYear } from '@/lib/utils'

type Props = { params: Promise<{ magazin: string }> }

export function generateStaticParams() {
  return getAllStoreSlugs().map(slug => ({ magazin: slug }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { magazin } = await params
  const store = getStoreBySlug(magazin)
  if (!store) return {}
  const monthYear = getCurrentMonthYear()

  return {
    title: `Cod Reducere ${store.nume} – Cupoane & Oferte ${monthYear}`,
    description: `Cod reducere ${store.nume} activ în ${monthYear}. Cupoane verificate + cele mai bune oferte și prețuri reduse. Economisește la fiecare comandă pe ${store.nume}!`,
    alternates: { canonical: `/cod-reducere/${store.slug}` },
    robots: { index: true, follow: true },
    openGraph: {
      title: `Cod Reducere ${store.nume} – ${monthYear}`,
      description: `Cupoane și reduceri ${store.nume} verificate zilnic.`,
    },
  }
}

export default async function CodReducerePage({ params }: Props) {
  const { magazin } = await params
  const store = getStoreBySlug(magazin)
  if (!store) notFound()

  const codes = getCodesByStore(magazin)
  const deals = getDealsByStore(magazin).slice(0, 8)
  const monthYear = getCurrentMonthYear()
  const hasCodes = codes.length > 0
  const hasDeals = deals.length > 0

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Breadcrumb items={[
        { label: 'Cod Reducere', href: '/cod-reducere' },
        { label: store.nume },
      ]} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4 mb-6 sm:mb-8">
        <div
          className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl flex items-center justify-center text-3xl shrink-0"
          style={{ backgroundColor: store.culoare + '20' }}
        >
          {store.logo_emoji}
        </div>
        <div>
          <h1 className="font-display font-extrabold text-xl sm:text-3xl md:text-4xl text-neutral-900 leading-tight">
            Cod Reducere {store.nume} – {monthYear}
          </h1>
          <p className="text-neutral-500 mt-1 text-sm">
            {hasCodes
              ? `${codes.length} cod${codes.length !== 1 ? 'uri' : ''} activ${codes.length !== 1 ? 'e' : ''}`
              : 'Verificat azi · Oferte active disponibile'}
            {' '}· Actualizat zilnic
          </p>
        </div>
      </div>

      {/* ─── Coduri promoționale ─── */}
      {hasCodes ? (
        <section className="mb-12">
          <h2 className="font-display font-bold text-xl text-neutral-900 mb-4">
            Coduri promoționale active
          </h2>
          <div className="space-y-4">
            {codes.map(code => (
              <PromoCodeCard key={code.id} code={code} />
            ))}
          </div>
        </section>
      ) : (
        <section className="mb-10 bg-amber-50 border border-amber-200 rounded-2xl p-6">
          <div className="flex gap-3 items-start">
            <span className="text-2xl">📋</span>
            <div>
              <h2 className="font-bold text-neutral-800 text-lg mb-1">
                Nu există coduri promoționale active momentan
              </h2>
              <p className="text-neutral-600 text-sm leading-relaxed">
                {store.nume} nu oferă un cod reducere activ în acest moment. Dar nu
                pleca! Mai jos găsești reducerile curente — prețuri deja scăzute,
                fără să ai nevoie de vreun cod.
              </p>
            </div>
          </div>
        </section>
      )}

      {/* ─── Cum se folosește un cod ─── */}
      <section className="bg-neutral-50 rounded-2xl p-6 sm:p-8 mb-10">
        <h2 className="font-display font-bold text-xl text-neutral-900 mb-4">
          Cum folosești un cod reducere {store.nume}?
        </h2>
        <ol className="space-y-3 text-neutral-600 text-sm sm:text-base">
          {[
            `Apasă butonul "Copiază + Cumpără" de lângă codul dorit`,
            `Codul se copiază automat și se deschide site-ul ${store.nume}`,
            `Adaugă produsele în coș, apoi la checkout caută câmpul "Cod promoțional"`,
            `Lipește codul (Ctrl+V / Cmd+V) și apasă "Aplică". Reducerea se aplică instant!`,
          ].map((step, i) => (
            <li key={i} className="flex gap-3">
              <span className="w-7 h-7 bg-brand-red text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0">
                {i + 1}
              </span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </section>

      {/* ─── Oferte active ─── */}
      {hasDeals && (
        <section className="mb-12">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display font-bold text-xl text-neutral-900">
              Reduceri active {store.nume} – fără cod necesar
            </h2>
            <Link
              href={`/reduceri/${store.slug}`}
              className="text-brand-red text-sm font-medium hover:underline"
            >
              Vezi toate →
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-6">
            {deals.map(deal => (
              <DealCard key={deal.id} deal={deal} />
            ))}
          </div>
        </section>
      )}

      {/* ─── FAQ SEO ─── */}
      <section className="mb-10">
        <h2 className="font-display font-bold text-xl text-neutral-900 mb-6">
          Întrebări frecvente despre codurile {store.nume}
        </h2>
        <div className="space-y-4">
          {[
            {
              q: `Există un cod reducere ${store.nume} activ în ${monthYear}?`,
              a: hasCodes
                ? `Da! Găsești mai sus ${codes.length} cod${codes.length !== 1 ? 'uri' : ''} activ${codes.length !== 1 ? 'e' : ''} verificat${codes.length !== 1 ? 'e' : ''} pentru ${store.nume}. Copiază codul și aplică-l la checkout.`
                : `Nu există un cod reducere ${store.nume} activ în acest moment. Verificăm zilnic. Între timp, găsești reduceri directe de preț mai sus — fără cod necesar.`,
            },
            {
              q: `Cât de des se actualizează codurile ${store.nume}?`,
              a: `Verificăm ofertele și codurile ${store.nume} zilnic, uneori de mai multe ori pe zi. Dacă un cod nu mai funcționează, îl eliminăm imediat.`,
            },
            {
              q: `Pot combina un cod reducere cu alte oferte ${store.nume}?`,
              a: `Depinde de regulile ${store.nume} — unele coduri sunt valabile și pe produse deja reduse, altele nu. Informația este specificată pe fiecare cod în parte.`,
            },
          ].map(({ q, a }, i) => (
            <details
              key={i}
              className="border border-neutral-200 rounded-xl overflow-hidden group"
            >
              <summary className="flex items-center justify-between px-5 py-4 cursor-pointer font-medium text-neutral-800 hover:bg-neutral-50 list-none">
                {q}
                <span className="text-neutral-400 group-open:rotate-180 transition-transform text-lg">▾</span>
              </summary>
              <div className="px-5 pb-4 text-neutral-600 text-sm leading-relaxed">{a}</div>
            </details>
          ))}
        </div>
      </section>

      {/* ─── Cross-link ─── */}
      <div className="flex flex-wrap gap-3">
        <Link href={`/reduceri/${store.slug}`} className="btn-cta-outline text-sm">
          Toate reducerile {store.nume} →
        </Link>
        <Link href={`/ghiduri/${store.slug}`} className="btn-cta-outline text-sm">
          Ghid cumpărături {store.nume} →
        </Link>
      </div>
    </div>
  )
}
