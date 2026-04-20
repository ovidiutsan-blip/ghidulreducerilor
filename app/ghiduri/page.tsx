import { Metadata } from 'next'
import Link from 'next/link'
import { ArrowRight, BookOpen } from 'lucide-react'
import Breadcrumb from '@/components/Breadcrumb'
import { STORE_GUIDES } from '@/lib/store-guides'
import { getStoreBySlug, getDealsByStore } from '@/lib/data'

export const metadata: Metadata = {
  title: 'Ghiduri de cumpărare — Notino, Answear, Dr.Max, Fashion Days și altele | GhidulReducerilor.ro',
  description: 'Ghiduri complete de cumpărare pentru cele mai populare magazine online din România: când sunt reducerile, cum folosești codurile promo, livrare, retur.',
  alternates: { canonical: '/ghiduri' },
  openGraph: {
    title: 'Ghiduri de cumpărare pentru magazine online din România',
    description: 'Ghiduri cu tips și coduri promo pentru Notino, Answear, Dr.Max, Fashion Days, Libris, Elefant, Vegis, MatHaus.',
    url: 'https://ghidulreducerilor.ro/ghiduri',
    type: 'website',
  },
}

export default function GhiduriIndexPage() {
  const guidesWithMeta = STORE_GUIDES.map(g => {
    const store = getStoreBySlug(g.storeSlug)
    const dealCount = getDealsByStore(g.storeSlug).length
    return { guide: g, store, dealCount }
  })

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'Ghiduri de cumpărare pentru magazine online din România',
    description: 'Ghiduri complete pentru cumpărători: Notino, Answear, Dr.Max, Fashion Days, Libris, Elefant, Vegis, MatHaus.',
    url: 'https://ghidulreducerilor.ro/ghiduri',
    inLanguage: 'ro',
    hasPart: STORE_GUIDES.map(g => ({
      '@type': 'Article',
      name: g.title,
      url: `https://ghidulreducerilor.ro/ghiduri/${g.slug}`,
    })),
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <Breadcrumb
            items={[
              { label: 'Acasă', href: '/' },
              { label: 'Ghiduri' },
            ]}
          />

          {/* Hero */}
          <div className="text-center mt-6 mb-12">
            <BookOpen className="w-14 h-14 text-blue-600 mx-auto mb-4" />
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Ghiduri de cumpărare
            </h1>
            <p className="text-lg text-gray-700 max-w-2xl mx-auto">
              Cum cumperi inteligent de pe cele mai populare magazine online din România: când sunt reducerile mari, cum folosești codurile promo, livrare, retur.
            </p>
          </div>

          {/* Guides grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {guidesWithMeta.map(({ guide, store, dealCount }) => (
              <Link
                key={guide.slug}
                href={`/ghiduri/${guide.slug}`}
                className="group bg-white border-2 border-gray-200 rounded-2xl p-6 hover:border-blue-400 hover:shadow-lg transition-all"
              >
                <div className="flex items-start gap-4">
                  <span
                    className="flex-shrink-0 w-14 h-14 flex items-center justify-center rounded-xl text-3xl"
                    style={{ backgroundColor: `${store?.culoare || '#1D3557'}15` }}
                    aria-hidden="true"
                  >
                    {store?.logo_emoji || '🏪'}
                  </span>
                  <div className="flex-1 min-w-0">
                    <h2 className="text-xl font-bold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
                      {store?.nume || guide.slug}
                    </h2>
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                      {guide.metaDescription}
                    </p>
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      {dealCount > 0 && (
                        <span className="inline-flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                          {dealCount} oferte active
                        </span>
                      )}
                      <span>·</span>
                      <span>{guide.sections.length} secțiuni</span>
                      <span>·</span>
                      <span>{guide.faq.length} FAQ</span>
                    </div>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all flex-shrink-0 mt-1" />
                </div>
              </Link>
            ))}
          </div>

          {/* Related */}
          <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-4">
            <Link
              href="/categorii"
              className="flex items-center justify-between p-5 bg-blue-50 hover:bg-blue-100 border-2 border-blue-200 rounded-xl transition-colors group"
            >
              <div>
                <div className="font-semibold text-gray-900">Reduceri pe categorii</div>
                <div className="text-sm text-gray-600">Fashion, Beauty, Farmacie, Cărți, Casă & Grădină</div>
              </div>
              <ArrowRight className="w-5 h-5 text-blue-600 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/blog"
              className="flex items-center justify-between p-5 bg-gray-50 hover:bg-gray-100 border-2 border-gray-200 rounded-xl transition-colors group"
            >
              <div>
                <div className="font-semibold text-gray-900">Blog & articole</div>
                <div className="text-sm text-gray-600">Tips, ghiduri și calendar Black Friday</div>
              </div>
              <ArrowRight className="w-5 h-5 text-gray-600 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}
