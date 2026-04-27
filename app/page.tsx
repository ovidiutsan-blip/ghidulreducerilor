import { Metadata } from 'next'
import { Tag } from 'lucide-react'
import DealOfTheDay from '@/components/DealOfTheDay'
import FlashDeals from '@/components/FlashDeals'
import HomepageDeals from '@/components/HomepageDeals'
import RecentlyViewed from '@/components/RecentlyViewed'
import StoreCard from '@/components/StoreCard'
import EmailForm from '@/components/EmailForm'
import TrustBar from '@/components/TrustBar'
import ExitIntentPopup from '@/components/ExitIntentPopup'
import { getActiveDeals, getAllStores, getDealOfTheDay, getFlashDeals } from '@/lib/data'
import { buildItemListSchema, buildBreadcrumbSchema } from '@/lib/schema'

export const metadata: Metadata = {
  title: 'GhidulReducerilor.ro — Cele Mai Bune Reduceri și Coduri Promo România 2026',
  description: 'Descoperă cele mai bune reduceri si coduri promotionale eMAG din Romania. Oferte verificate zilnic, prețuri reale, economii garantate.',
  alternates: { canonical: '/' },
  openGraph: {
    title: 'GhidulReducerilor.ro — Reduceri și Coduri Promoționale România 2026',
    description: 'Cele mai bune reduceri eMAG din Romania verificate zilnic. Oferte reale, prețuri scăzute, economii garantate.',
    images: [{ url: 'https://ghidulreducerilor.ro/api/og', width: 1200, height: 630 }],
  },
}

// Câte deal-uri trimitem în prop la HomepageDeals (RSC payload + SSR HTML).
// Mai sus de atât = HTML hits 7+ MB; categoriile cu peste atâtea deals au
// pagină dedicată /categorie/[slug] cu paginare proprie.
const HOMEPAGE_DEALS_LIMIT = 100

export default function HomePage() {
  const allActiveDeals = getActiveDeals()
  const stores = getAllStores()
  const dealOfTheDay = getDealOfTheDay()
  const flashDeals = getFlashDeals(8)

  // Counts per categorie calculate pe TOATE deals (chips trebuie să arate totalul real).
  const categoryCounts: Record<string, number> = {}
  for (const d of allActiveDeals) {
    categoryCounts[d.categorie] = (categoryCounts[d.categorie] || 0) + 1
  }

  // Subset trimis la HomepageDeals: cele mai mari discount-uri primele.
  const homepageDeals = [...allActiveDeals]
    .sort((a, b) => (b.procent_reducere ?? 0) - (a.procent_reducere ?? 0))
    .slice(0, HOMEPAGE_DEALS_LIMIT)

  // Schema WebSite cu SearchAction
  const websiteSchema = {
    '@type': 'WebSite',
    name: 'GhidulReducerilor.ro',
    url: 'https://ghidulreducerilor.ro',
    description: 'Cele mai bune reduceri și coduri promoționale din România',
    inLanguage: 'ro',
    potentialAction: {
      '@type': 'SearchAction',
      target: 'https://ghidulreducerilor.ro/reduceri/{search_term_string}',
      'query-input': 'required name=search_term_string',
    },
  }

  // ItemList cu Product+Offer complet (top 15 deals sortate după reducere)
  const topDeals = homepageDeals.slice(0, 15)
  const itemListSchema = buildItemListSchema('Cele Mai Bune Reduceri Azi', topDeals, '/')

  // Breadcrumb homepage
  const breadcrumbSchema = buildBreadcrumbSchema([{ name: 'Acasă', href: '/' }])

  // Combina totul intr-un singur @graph
  const jsonLd = {
    '@context': 'https://schema.org',
    '@graph': [
      websiteSchema,
      { ...itemListSchema, '@context': undefined },
      { ...breadcrumbSchema, '@context': undefined },
    ],
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* SEO H1 — vizibil pentru screen readers + crawlere; nu schimbă layout-ul */}
      <h1 className="sr-only">
        Ghidul Reducerilor — reduceri verificate zilnic și coduri promoționale din România
      </h1>

      {/* Trust Bar */}
      <TrustBar totalDeals={allActiveDeals.length} />

      {/* Deal of the Day */}
      <DealOfTheDay deal={dealOfTheDay} />

      {/* Flash Deals */}
      <FlashDeals deals={flashDeals} />

      {/* All Deals with Category Chips */}
      <HomepageDeals
        deals={homepageDeals}
        totalCount={allActiveDeals.length}
        categoryCounts={categoryCounts}
      />

      {/* Recently Viewed */}
      <RecentlyViewed allDeals={homepageDeals} />

      {/* Magazine Partenere */}
      <section id="magazine" className="bg-neutral-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-14">
          <div className="flex items-center gap-3 mb-6 sm:mb-8">
            <div className="w-10 h-10 bg-brand-red/10 rounded-xl flex items-center justify-center">
              <Tag className="w-5 h-5 text-brand-red" />
            </div>
            <div>
              <h2 className="font-display font-bold text-xl sm:text-2xl text-neutral-900">Magazine Partenere</h2>
              <p className="text-sm text-neutral-500">Reduceri de la {stores.length} magazine verificate</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4">
            {stores.map(store => (
              <StoreCard key={store.id} store={store} />
            ))}
          </div>
        </div>
      </section>

      {/* Abonare Email */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-14">
        <div className="bg-gradient-to-br from-brand-red to-brand-red-dark rounded-3xl p-6 sm:p-12 text-center text-white">
          <h2 className="font-display font-bold text-xl sm:text-3xl mb-3">
            Nu rata nicio reducere importanta
          </h2>
          <p className="text-white/80 mb-6 sm:mb-8 max-w-lg mx-auto text-sm sm:text-base">
            Primesti alerta pe email cand apare o reducere mare la magazinul tau preferat. Gratuit, fara spam.
          </p>
          <div className="bg-white rounded-2xl p-4 sm:p-8 text-left max-w-md mx-auto">
            <EmailForm />
          </div>
        </div>
      </section>

      {/* Exit Intent Popup */}
      <ExitIntentPopup />
    </>
  )
}
