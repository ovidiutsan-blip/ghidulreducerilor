import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { ArrowRight, CheckCircle2, Sparkles, HelpCircle, ShoppingBag, Tag, BookOpen } from 'lucide-react'
import Breadcrumb from '@/components/Breadcrumb'
import { getStoreGuideBySlug, getAllStoreGuideSlugs, STORE_GUIDES } from '@/lib/store-guides'
import { getStoreBySlug, getDealsByStore } from '@/lib/data'

type Props = { params: Promise<{ magazin: string }> }

export function generateStaticParams() {
  return getAllStoreGuideSlugs().map(magazin => ({ magazin }))
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { magazin } = await params
  const guide = getStoreGuideBySlug(magazin)
  if (!guide) return {}
  return {
    title: guide.metaTitle,
    description: guide.metaDescription,
    alternates: { canonical: `/ghiduri/${guide.slug}` },
    openGraph: {
      title: guide.metaTitle,
      description: guide.metaDescription,
      url: `https://ghidulreducerilor.ro/ghiduri/${guide.slug}`,
      type: 'article',
    },
  }
}

export default async function StoreGuidePage({ params }: Props) {
  const { magazin } = await params
  const guide = getStoreGuideBySlug(magazin)
  if (!guide) notFound()

  const store = getStoreBySlug(guide.storeSlug)
  const dealCount = getDealsByStore(guide.storeSlug).length

  // JSON-LD: Article + FAQPage + BreadcrumbList
  const jsonLd = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Article',
        headline: guide.title,
        description: guide.metaDescription,
        datePublished: '2026-04-20',
        dateModified: guide.lastUpdated,
        author: { '@type': 'Organization', name: 'GhidulReducerilor.ro' },
        publisher: {
          '@type': 'Organization',
          name: 'GhidulReducerilor.ro',
          url: 'https://ghidulreducerilor.ro',
        },
        mainEntityOfPage: {
          '@type': 'WebPage',
          '@id': `https://ghidulreducerilor.ro/ghiduri/${guide.slug}`,
        },
        inLanguage: 'ro',
      },
      {
        '@type': 'FAQPage',
        mainEntity: guide.faq.map(item => ({
          '@type': 'Question',
          name: item.q,
          acceptedAnswer: { '@type': 'Answer', text: item.a },
        })),
      },
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: 'Acasă', item: 'https://ghidulreducerilor.ro' },
          { '@type': 'ListItem', position: 2, name: 'Ghiduri', item: 'https://ghidulreducerilor.ro/ghiduri' },
          { '@type': 'ListItem', position: 3, name: store?.nume || guide.slug, item: `https://ghidulreducerilor.ro/ghiduri/${guide.slug}` },
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

      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <Breadcrumb
            items={[
              { label: 'Acasă', href: '/' },
              { label: 'Ghiduri', href: '/ghiduri' },
              { label: store?.nume || guide.slug },
            ]}
          />

          {/* Hero */}
          <div className="mt-6 mb-10">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-5xl" aria-hidden="true">{store?.logo_emoji || '🏪'}</span>
              <span
                className="inline-block px-3 py-1 rounded-full text-sm font-semibold text-white"
                style={{ backgroundColor: store?.culoare || '#1D3557' }}
              >
                Ghid {store?.nume || guide.slug}
              </span>
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4 leading-tight">
              {guide.title}
            </h1>
            <p className="text-sm text-gray-500 mb-6">
              Actualizat: {new Date(guide.lastUpdated).toLocaleDateString('ro-RO', {
                day: 'numeric', month: 'long', year: 'numeric'
              })}
            </p>
            <div className="prose prose-lg max-w-none text-gray-700 leading-relaxed">
              <p>{guide.intro}</p>
            </div>
          </div>

          {/* CTA bar — direct links to store pages */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-12">
            <Link
              href={`/reduceri/${guide.storeSlug}`}
              className="flex items-center justify-between bg-blue-50 hover:bg-blue-100 border-2 border-blue-200 rounded-xl p-4 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <ShoppingBag className="w-5 h-5 text-blue-600" />
                <div>
                  <div className="font-semibold text-gray-900">Vezi reducerile active</div>
                  <div className="text-sm text-gray-600">{dealCount} oferte pe {store?.nume || guide.slug}</div>
                </div>
              </div>
              <ArrowRight className="w-5 h-5 text-blue-600 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href={`/cod-reducere/${guide.storeSlug}`}
              className="flex items-center justify-between bg-amber-50 hover:bg-amber-100 border-2 border-amber-200 rounded-xl p-4 transition-colors group"
            >
              <div className="flex items-center gap-3">
                <Tag className="w-5 h-5 text-amber-600" />
                <div>
                  <div className="font-semibold text-gray-900">Coduri promo</div>
                  <div className="text-sm text-gray-600">Cupoane active pe {store?.nume || guide.slug}</div>
                </div>
              </div>
              <ArrowRight className="w-5 h-5 text-amber-600 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>

          {/* Sections */}
          <article className="prose prose-lg max-w-none prose-headings:text-gray-900 prose-headings:font-bold prose-p:text-gray-700 prose-p:leading-relaxed prose-a:text-blue-600">
            {guide.sections.map((section, idx) => (
              <section key={idx} className="mb-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-gray-100">
                  {section.heading}
                </h2>
                <p>{section.body}</p>
              </section>
            ))}
          </article>

          {/* Tips callout */}
          <div className="my-12 bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 border-2 border-amber-200 rounded-2xl p-6 md:p-8">
            <div className="flex items-center gap-3 mb-4">
              <Sparkles className="w-6 h-6 text-amber-600" />
              <h2 className="text-2xl font-bold text-gray-900 m-0">Tips rapide</h2>
            </div>
            <ul className="space-y-3 m-0 p-0 list-none">
              {guide.tips.map((tip, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-800">{tip}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* FAQ */}
          <section className="my-12">
            <div className="flex items-center gap-3 mb-6">
              <HelpCircle className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900 m-0">Întrebări frecvente</h2>
            </div>
            <div className="space-y-3">
              {guide.faq.map((item, idx) => (
                <details
                  key={idx}
                  className="group bg-white border border-gray-200 rounded-xl p-4 hover:border-blue-300 transition-colors"
                >
                  <summary className="flex items-center justify-between cursor-pointer font-semibold text-gray-900 list-none">
                    <span>{item.q}</span>
                    <span className="ml-4 text-2xl text-blue-600 group-open:rotate-45 transition-transform">+</span>
                  </summary>
                  <p className="mt-3 text-gray-700 leading-relaxed">{item.a}</p>
                </details>
              ))}
            </div>
          </section>

          {/* Related guides */}
          <section className="my-12">
            <div className="flex items-center gap-3 mb-6">
              <BookOpen className="w-6 h-6 text-gray-600" />
              <h2 className="text-xl font-bold text-gray-900 m-0">Alte ghiduri de cumpărare</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {STORE_GUIDES.filter(g => g.slug !== guide.slug).slice(0, 6).map(g => (
                <Link
                  key={g.slug}
                  href={`/ghiduri/${g.slug}`}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-full text-sm text-gray-800 transition-colors"
                >
                  <span>→</span>
                  <span className="font-medium">{g.slug.charAt(0).toUpperCase() + g.slug.slice(1)}</span>
                </Link>
              ))}
            </div>
          </section>

          {/* Final CTA */}
          <div className="mt-12 bg-gradient-to-r from-gray-900 to-gray-800 rounded-2xl p-8 text-center text-white">
            <h2 className="text-2xl font-bold mb-3">
              Gata să economisești pe {store?.nume || 'acest magazin'}?
            </h2>
            <p className="text-gray-300 mb-6 max-w-2xl mx-auto">
              Verificăm manual ofertele în fiecare zi. Intră direct pe pagina magazinului pentru reducerile active.
            </p>
            <div className="flex flex-wrap gap-3 justify-center">
              <Link
                href={`/reduceri/${guide.storeSlug}`}
                className="inline-flex items-center gap-2 bg-white text-gray-900 px-5 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                Vezi reducerile {store?.nume || ''}
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/ghiduri"
                className="inline-flex items-center gap-2 bg-transparent border-2 border-white/30 text-white px-5 py-3 rounded-lg font-semibold hover:bg-white/10 transition-colors"
              >
                Toate ghidurile
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
