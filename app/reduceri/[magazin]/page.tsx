import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import DealCard from '@/components/DealCard'
import Breadcrumb from '@/components/Breadcrumb'
import { getDealsByStore, getStoreBySlug, getAllStoreSlugs } from '@/lib/data'
import { getCurrentMonthYear } from '@/lib/utils'

type Props = { params: { magazin: string } }

export function generateStaticParams() {
  return getAllStoreSlugs().map(slug => ({ magazin: slug }))
}

export function generateMetadata({ params }: Props): Metadata {
  const store = getStoreBySlug(params.magazin)
  if (!store) return {}
  const monthYear = getCurrentMonthYear()
  const deals = getDealsByStore(params.magazin)
  const isEmpty = deals.length === 0

  return {
    title: `Reduceri ${store.nume} – Oferte și Promoții ${monthYear}`,
    description: `Cele mai bune reduceri ${store.nume} din ${monthYear}. Oferte verificate, prețuri reduse și promoții exclusive. Economisește la fiecare comandă!`,
    alternates: { canonical: `/reduceri/${store.slug}` },
    // Pagini fără oferte active = thin content → noindex (previne penalizare SEO)
    robots: isEmpty
      ? { index: false, follow: true }
      : { index: true, follow: true },
    openGraph: {
      title: `Reduceri ${store.nume} – Oferte ${monthYear}`,
      description: `Descoperă reducerile ${store.nume}. Oferte verificate zilnic.`,
    },
  }
}

export default function StorePage({ params }: Props) {
  const store = getStoreBySlug(params.magazin)
  if (!store) notFound()

  const deals = getDealsByStore(params.magazin)
  const monthYear = getCurrentMonthYear()

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Breadcrumb items={[
        { label: 'Reduceri', href: '/#reduceri' },
        { label: store.nume },
      ]} />

      {/* Header magazin */}
      <div className="flex items-center gap-4 mb-8">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl shrink-0"
          style={{ backgroundColor: store.culoare + '20' }}
        >
          {store.logo_emoji}
        </div>
        <div>
          <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-neutral-900">
            Reduceri {store.nume} – Oferte și Promoții {monthYear}
          </h1>
          <p className="text-neutral-500 mt-1">
            {deals.length} oferte active · Actualizat zilnic
          </p>
        </div>
      </div>

      {/* Grid produse */}
      {deals.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-16">
          {deals.map(deal => (
            <DealCard key={deal.id} deal={deal} />
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <p className="text-neutral-500 text-lg">Nu sunt reduceri active momentan. Revino curând!</p>
        </div>
      )}

      {/* Despre Magazin — SEO content */}
      <section className="bg-neutral-50 rounded-2xl p-8 mt-8">
        <h2 className="font-display font-bold text-xl text-neutral-900 mb-4">
          Despre {store.nume}
        </h2>
        <p className="text-neutral-600 leading-relaxed mb-4">
          {store.descriere}
        </p>
        <p className="text-neutral-600 leading-relaxed">
          Pe GhidulReducerilor.ro găsești cele mai bune oferte de la {store.nume}, verificate zilnic.
          Toate link-urile sunt de afiliere prin Profitshare.ro — când cumperi prin ele, noi primim un
          comision mic fără costuri suplimentare pentru tine.
        </p>
        <div className="mt-4">
          <a
            href={`/coduri-promo/${store.slug}`}
            className="btn-cta-outline text-sm"
          >
            Vezi codurile promoționale {store.nume} →
          </a>
        </div>
      </section>
    </div>
  )
}
