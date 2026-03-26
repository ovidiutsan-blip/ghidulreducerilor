import { Metadata } from 'next'
import { Flame, Tag, TrendingDown } from 'lucide-react'
import DealCard from '@/components/DealCard'
import StoreCard from '@/components/StoreCard'
import EmailForm from '@/components/EmailForm'
import { getActiveDeals, getAllStores } from '@/lib/data'

export const metadata: Metadata = {
  title: 'GhidulReducerilor.ro — Cele Mai Bune Reduceri și Coduri Promo România 2026',
  description: 'Descoperă cele mai bune reduceri și coduri promoționale din România. eMAG, Altex, Fashion Days — oferte verificate zilnic, economii reale.',
  alternates: { canonical: '/' },
}

export default function HomePage() {
  const deals = getActiveDeals()
  const stores = getAllStores()

  // Schema markup WebSite + ItemList
  const jsonLd = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebSite',
        name: 'GhidulReducerilor.ro',
        url: 'https://ghidulreducerilor.ro',
        description: 'Cele mai bune reduceri și coduri promoționale din România',
        inLanguage: 'ro',
      },
      {
        '@type': 'ItemList',
        name: 'Reducerile Zilei',
        numberOfItems: deals.length,
        itemListElement: deals.map((deal, i) => ({
          '@type': 'ListItem',
          position: i + 1,
          name: deal.titlu,
          url: deal.link_afiliat,
        })),
      },
    ],
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-neutral-900 via-neutral-800 to-neutral-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 text-center">
          <div className="inline-flex items-center gap-2 bg-brand-red/20 text-brand-red-light px-4 py-1.5 rounded-full text-sm font-medium mb-6">
            <Flame className="w-4 h-4" />
            Actualizat zilnic
          </div>
          <h1 className="font-display font-extrabold text-4xl sm:text-5xl lg:text-6xl leading-tight mb-6">
            Cele mai bune <span className="text-brand-red">reduceri</span><br />
            din România, într-un singur loc
          </h1>
          <p className="text-lg sm:text-xl text-neutral-300 max-w-2xl mx-auto mb-8">
            Reduceri verificate zilnic de la eMAG, Altex, Fashion Days și alte magazine.
            Economisești bani, noi câștigăm un comision mic — toată lumea e fericită.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a href="#reduceri" className="btn-cta text-base px-8 py-4">
              <TrendingDown className="w-5 h-5" />
              Vezi reducerile zilei
            </a>
            <a href="#magazine" className="btn-cta-outline border-white/30 text-white hover:bg-white hover:text-neutral-900 text-base px-8 py-4">
              <Tag className="w-5 h-5" />
              Coduri promoționale
            </a>
          </div>
        </div>
      </section>

      {/* Reducerile Zilei */}
      <section id="reduceri" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 bg-brand-red/10 rounded-xl flex items-center justify-center">
            <Flame className="w-5 h-5 text-brand-red" />
          </div>
          <div>
            <h2 className="font-display font-bold text-2xl text-neutral-900">Reducerile Zilei</h2>
            <p className="text-sm text-neutral-500">Cele mai bune oferte, verificate azi</p>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {deals.map(deal => (
            <DealCard key={deal.id} deal={deal} />
          ))}
        </div>
      </section>

      {/* Magazine Partenere */}
      <section id="magazine" className="bg-neutral-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-brand-red/10 rounded-xl flex items-center justify-center">
              <Tag className="w-5 h-5 text-brand-red" />
            </div>
            <div>
              <h2 className="font-display font-bold text-2xl text-neutral-900">Magazine Partenere</h2>
              <p className="text-sm text-neutral-500">Reduceri de la magazinele tale preferate</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {stores.map(store => (
              <StoreCard key={store.id} store={store} />
            ))}
          </div>
        </div>
      </section>

      {/* Secțiune Abonare Email */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-gradient-to-br from-brand-red to-brand-red-dark rounded-3xl p-8 sm:p-12 text-center text-white">
          <h2 className="font-display font-bold text-2xl sm:text-3xl mb-3">
            Nu rata nicio reducere importantă
          </h2>
          <p className="text-white/80 mb-8 max-w-lg mx-auto">
            Primești alertă pe email când apare o reducere mare la magazinul tău preferat. Gratuit, fără spam.
          </p>
          <div className="bg-white rounded-2xl p-6 sm:p-8 text-left max-w-md mx-auto">
            <EmailForm />
          </div>
        </div>
      </section>
    </>
  )
}
