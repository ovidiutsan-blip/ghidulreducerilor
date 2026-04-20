import { Metadata } from 'next'
import Link from 'next/link'
import { ArrowRight, Grid3X3 } from 'lucide-react'
import Breadcrumb from '@/components/Breadcrumb'
import { THEME_HUBS } from '@/lib/theme-hubs'
import { getStoreBySlug, getDealsByStore } from '@/lib/data'

export const metadata: Metadata = {
  title: 'Categorii de reduceri — Fashion, Beauty, Farmacie, Cărți, Casă și Grădină',
  description: 'Explorează reducerile grupate pe categorii: modă, cosmetice, suplimente, cărți și produse pentru casă. Toate verificate zilnic.',
  alternates: { canonical: '/categorii' },
  openGraph: {
    title: 'Categorii de reduceri — GhidulReducerilor.ro',
    description: 'Reduceri pe categorii: fashion, beauty, farmacie, cărți, casă și grădină.',
    url: 'https://ghidulreducerilor.ro/categorii',
    type: 'website',
  },
}

export default function CategoriiIndexPage() {
  const hubsWithCounts = THEME_HUBS.map(hub => {
    const stores = hub.storeSlugs
      .map(s => getStoreBySlug(s))
      .filter(Boolean)
    const dealCount = hub.storeSlugs.reduce((sum, slug) => sum + getDealsByStore(slug).length, 0)
    return { hub, storeCount: stores.length, dealCount }
  })

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'Categorii de reduceri',
    description: 'Reduceri grupate pe categorii tematice: fashion, beauty, farmacie, cărți, casă și grădină.',
    url: 'https://ghidulreducerilor.ro/categorii',
    hasPart: hubsWithCounts.map(({ hub }) => ({
      '@type': 'WebPage',
      name: hub.label,
      url: `https://ghidulreducerilor.ro/categorii/${hub.slug}`,
      description: hub.description,
    })),
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumb items={[{ label: 'Categorii' }]} />

        <header className="mb-10 mt-4">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-14 h-14 bg-brand-red/10 rounded-2xl flex items-center justify-center">
              <Grid3X3 className="w-7 h-7 text-brand-red" />
            </div>
            <div>
              <h1 className="font-display font-bold text-3xl sm:text-4xl text-neutral-900 leading-tight">
                Reduceri pe categorii
              </h1>
              <p className="text-sm text-neutral-500 mt-1">
                {THEME_HUBS.length} categorii tematice · magazine verificate
              </p>
            </div>
          </div>
          <p className="text-lg text-neutral-700 leading-relaxed max-w-3xl">
            Alege categoria care te interesează și vezi doar ofertele relevante, grupate pe magazinele
            cele mai bune pentru fiecare domeniu. Descoperă ghiduri de cumpărare, sfaturi și
            întrebări frecvente pentru fiecare vertical.
          </p>
        </header>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {hubsWithCounts.map(({ hub, storeCount, dealCount }) => (
            <Link
              key={hub.slug}
              href={`/categorii/${hub.slug}`}
              className="group relative rounded-2xl border border-neutral-200 bg-white hover:border-brand-red hover:shadow-lg transition-all p-6 flex flex-col"
            >
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl mb-4"
                style={{ backgroundColor: hub.color + '20' }}
              >
                {hub.emoji}
              </div>
              <h2 className="font-display font-bold text-xl text-neutral-900 group-hover:text-brand-red transition-colors mb-2">
                {hub.label}
              </h2>
              <p className="text-sm text-neutral-600 leading-relaxed mb-4 flex-1">
                {hub.description}
              </p>
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-neutral-500">
                  {storeCount} magazine · {dealCount} oferte
                </span>
                <ArrowRight className="w-5 h-5 text-neutral-400 group-hover:text-brand-red group-hover:translate-x-1 transition-all" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </>
  )
}
