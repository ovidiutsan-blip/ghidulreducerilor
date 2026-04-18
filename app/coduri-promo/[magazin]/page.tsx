import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import PromoCodeCard from '@/components/PromoCodeCard'
import Breadcrumb from '@/components/Breadcrumb'
import { getCodesByStore, getStoreBySlug, getAllStoreSlugs } from '@/lib/data'
import { getCurrentMonthYear } from '@/lib/utils'

type Props = { params: { magazin: string } }

export function generateStaticParams() {
  return getAllStoreSlugs().map(slug => ({ magazin: slug }))
}

export function generateMetadata({ params }: Props): Metadata {
  const store = getStoreBySlug(params.magazin)
  if (!store) return {}
  const monthYear = getCurrentMonthYear()
  const codes = getCodesByStore(params.magazin)
  const isEmpty = codes.length === 0

  return {
    title: `Coduri Promoționale ${store.nume} – ${monthYear}`,
    description: `Coduri promoționale și cupoane ${store.nume} active în ${monthYear}. Copiază codul, aplică-l la checkout și economisește instant!`,
    alternates: { canonical: `/coduri-promo/${store.slug}` },
    // Pagini fără coduri active = thin content → noindex (previne penalizare SEO)
    robots: isEmpty
      ? { index: false, follow: true }
      : { index: true, follow: true },
    openGraph: {
      title: `Coduri Promo ${store.nume} – ${monthYear}`,
      description: `Cupoane și coduri de reducere ${store.nume} verificate.`,
    },
  }
}

export default function PromoCodesPage({ params }: Props) {
  const store = getStoreBySlug(params.magazin)
  if (!store) notFound()

  const codes = getCodesByStore(params.magazin)
  const monthYear = getCurrentMonthYear()

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Breadcrumb items={[
        { label: 'Coduri Promo', href: '/#magazine' },
        { label: store.nume },
      ]} />

      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl shrink-0"
          style={{ backgroundColor: store.culoare + '20' }}
        >
          {store.logo_emoji}
        </div>
        <div>
          <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-neutral-900">
            Coduri Promoționale {store.nume} – {monthYear}
          </h1>
          <p className="text-neutral-500 mt-1">
            {codes.length} coduri disponibile · Click pe &quot;Copiază + Cumpără&quot; pentru a aplica
          </p>
        </div>
      </div>

      {/* Lista coduri */}
      {codes.length > 0 ? (
        <div className="space-y-4 mb-16">
          {codes.map(code => (
            <PromoCodeCard key={code.id} code={code} />
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <p className="text-neutral-500 text-lg">Nu sunt coduri promoționale active momentan.</p>
        </div>
      )}

      {/* Cum funcționează */}
      <section className="bg-neutral-50 rounded-2xl p-8">
        <h2 className="font-display font-bold text-xl text-neutral-900 mb-4">
          Cum folosești un cod promoțional {store.nume}?
        </h2>
        <ol className="space-y-3 text-neutral-600">
          <li className="flex gap-3">
            <span className="w-7 h-7 bg-brand-red text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0">1</span>
            <span>Apasă butonul <strong>&quot;Copiază + Cumpără&quot;</strong> de lângă codul dorit</span>
          </li>
          <li className="flex gap-3">
            <span className="w-7 h-7 bg-brand-red text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0">2</span>
            <span>Codul se copiază automat și se deschide site-ul {store.nume}</span>
          </li>
          <li className="flex gap-3">
            <span className="w-7 h-7 bg-brand-red text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0">3</span>
            <span>Adaugă produsele în coș, apoi lipește codul la checkout (Ctrl+V)</span>
          </li>
          <li className="flex gap-3">
            <span className="w-7 h-7 bg-brand-red text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0">4</span>
            <span>Reducerea se aplică automat. Gata, ai economisit! 🎉</span>
          </li>
        </ol>
        <div className="mt-6">
          <a
            href={`/reduceri/${store.slug}`}
            className="btn-cta-outline text-sm"
          >
            Vezi toate reducerile {store.nume} →
          </a>
        </div>
      </section>
    </div>
  )
}
