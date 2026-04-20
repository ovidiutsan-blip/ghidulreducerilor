import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { ArrowRight, CheckCircle2, Sparkles, HelpCircle } from 'lucide-react'
import Breadcrumb from '@/components/Breadcrumb'
import StoreCard from '@/components/StoreCard'
import DealCard from '@/components/DealCard'
import { getThemeHubBySlug, getAllThemeHubSlugs, THEME_HUBS } from '@/lib/theme-hubs'
import { getStoreBySlug, getDealsByStore } from '@/lib/data'

type Props = { params: { slug: string } }

export function generateStaticParams() {
  return getAllThemeHubSlugs().map(slug => ({ slug }))
}

export function generateMetadata({ params }: Props): Metadata {
  const hub = getThemeHubBySlug(params.slug)
  if (!hub) return {}
  return {
    title: hub.title,
    description: hub.description,
    alternates: { canonical: `/categorii/${hub.slug}` },
    openGraph: {
      title: hub.title,
      description: hub.description,
      url: `https://ghidulreducerilor.ro/categorii/${hub.slug}`,
      type: 'website',
    },
  }
}

export default function ThemeHubPage({ params }: Props) {
  const hub = getThemeHubBySlug(params.slug)
  if (!hub) notFound()

  // Resolve stores from hub storeSlugs
  const stores = hub.storeSlugs
    .map(slug => getStoreBySlug(slug))
    .filter((s): s is NonNullable<typeof s> => Boolean(s))

  // Aggregate deals from all stores in this theme, filter strictly by hub's own dealCategories
  // (prevents cross-taxonomy leakage — e.g., eMAG electronics appearing on the Fashion hub)
  const storeDeals = hub.storeSlugs.flatMap(slug => getDealsByStore(slug))
  const allDeals = hub.dealCategories.length > 0
    ? storeDeals.filter(d => hub.dealCategories.includes(d.categorie))
    : []
  const topDeals = [...allDeals]
    .sort((a, b) => b.procent_reducere - a.procent_reducere)
    .slice(0, 8)

  // JSON-LD structured data
  const jsonLd = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'CollectionPage',
        name: hub.title,
        description: hub.description,
        url: `https://ghidulreducerilor.ro/categorii/${hub.slug}`,
        inLanguage: 'ro',
      },
      {
        '@type': 'ItemList',
        name: `Magazine ${hub.label}`,
        numberOfItems: stores.length,
        itemListElement: stores.map((store, i) => ({
          '@type': 'ListItem',
          position: i + 1,
          name: store.nume,
          url: `https://ghidulreducerilor.ro/reduceri/${store.slug}`,
        })),
      },
      {
        '@type': 'FAQPage',
        mainEntity: hub.faq.map(item => ({
          '@type': 'Question',
          name: item.q,
          acceptedAnswer: {
            '@type': 'Answer',
            text: item.a,
          },
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumb items={[
          { label: 'Categorii' },
          { label: hub.label },
        ]} />

        {/* Hero */}
        <header className="mb-10 mt-4">
          <div className="flex items-center gap-4 mb-4">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center text-4xl shrink-0"
              style={{ backgroundColor: hub.color + '20' }}
            >
              {hub.emoji}
            </div>
            <div>
              <h1 className="font-display font-bold text-2xl sm:text-4xl text-neutral-900 leading-tight">
                {hub.title}
              </h1>
              <p className="text-sm text-neutral-500 mt-1">
                {stores.length} magazine verificate{allDeals.length > 0 ? ` · ${allDeals.length} oferte active` : ''}
              </p>
            </div>
          </div>
          <p className="text-lg text-neutral-700 leading-relaxed max-w-3xl">
            {hub.description}
          </p>
        </header>

        {/* Editorial intro */}
        <section className="prose prose-lg prose-neutral max-w-none mb-14">
          {hub.heroIntro.split('\n\n').map((para, i) => (
            <p key={i} className="text-neutral-700 leading-relaxed">
              {para}
            </p>
          ))}
        </section>

        {/* Featured stores */}
        <section className="mb-14">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-brand-red/10 rounded-xl flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-brand-red" />
            </div>
            <div>
              <h2 className="font-display font-bold text-xl sm:text-2xl text-neutral-900">
                Magazine {hub.label}
              </h2>
              <p className="text-sm text-neutral-500">Parteneri verificați cu oferte active</p>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {stores.map(store => (
              <StoreCard key={store.id} store={store} />
            ))}
          </div>
        </section>

        {/* Top deals */}
        {topDeals.length === 0 && (
          <section className="mb-14">
            <div className="bg-neutral-50 border border-neutral-200 rounded-2xl p-6 sm:p-8 text-center">
              <div className="text-4xl mb-3">🔎</div>
              <h2 className="font-display font-bold text-lg text-neutral-900 mb-2">
                Ofertele {hub.label.toLowerCase()} sunt în curs de validare
              </h2>
              <p className="text-neutral-600 max-w-xl mx-auto leading-relaxed">
                Monitorizăm zilnic campaniile din magazinele partenere de mai sus. Dealurile apar aici imediat după ce sunt verificate de echipă — fără reduceri false sau prețuri umflate.
                Până atunci, folosește cardurile de magazin pentru a vizita direct ofertele curente.
              </p>
            </div>
          </section>
        )}
        {topDeals.length > 0 && (
          <section className="mb-14">
            <div className="flex items-center justify-between gap-3 mb-6 flex-wrap">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-brand-red/10 rounded-xl flex items-center justify-center text-2xl">
                  🔥
                </div>
                <div>
                  <h2 className="font-display font-bold text-xl sm:text-2xl text-neutral-900">
                    Top oferte {hub.label}
                  </h2>
                  <p className="text-sm text-neutral-500">Cele mai mari reduceri din categorie</p>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
              {topDeals.map(deal => (
                <DealCard key={deal.id} deal={deal} />
              ))}
            </div>
          </section>
        )}

        {/* Tips */}
        <section className="mb-14">
          <div className="bg-gradient-to-br from-brand-red/5 to-amber-50 border border-brand-red/10 rounded-2xl p-6 sm:p-8">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle2 className="w-6 h-6 text-brand-red" />
              <h2 className="font-display font-bold text-xl text-neutral-900">
                Sfaturi pentru economii maxime
              </h2>
            </div>
            <ul className="space-y-3">
              {hub.tips.map((tip, i) => (
                <li key={i} className="flex items-start gap-3 text-neutral-700">
                  <span
                    className="shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white mt-0.5"
                    style={{ backgroundColor: hub.color }}
                  >
                    {i + 1}
                  </span>
                  <span className="leading-relaxed">{tip}</span>
                </li>
              ))}
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
                Întrebări frecvente
              </h2>
              <p className="text-sm text-neutral-500">Tot ce trebuie să știi înainte să cumperi</p>
            </div>
          </div>
          <div className="space-y-3">
            {hub.faq.map((item, i) => (
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
                <div className="px-5 pb-5 text-neutral-700 leading-relaxed">
                  {item.a}
                </div>
              </details>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="bg-gradient-to-br from-brand-red to-brand-red-dark rounded-3xl p-8 sm:p-12 text-center text-white">
          <h2 className="font-display font-bold text-2xl sm:text-3xl mb-3">
            Vezi toate ofertele {hub.label}
          </h2>
          <p className="text-white/80 mb-8 max-w-xl mx-auto">
            Oferte actualizate zilnic, verificate manual. Fără reduceri false, fără prețuri umflate.
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Link
              href="/"
              className="inline-flex items-center gap-2 bg-white text-brand-red font-display font-semibold px-6 py-3 rounded-full hover:bg-neutral-50 transition-colors"
            >
              Toate reducerile
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/blog"
              className="inline-flex items-center gap-2 bg-white/10 border border-white/30 text-white font-display font-semibold px-6 py-3 rounded-full hover:bg-white/20 transition-colors backdrop-blur-sm"
            >
              Citește ghidurile noastre
            </Link>
          </div>
        </section>

        {/* Other hubs */}
        <section className="mt-14 pt-10 border-t border-neutral-200">
          <h2 className="font-display font-bold text-lg text-neutral-900 mb-4">
            Explorează alte categorii
          </h2>
          <div className="flex flex-wrap gap-2">
            {THEME_HUBS.filter(t => t.slug !== hub.slug).map(other => (
              <Link
                key={other.slug}
                href={`/categorii/${other.slug}`}
                className="inline-flex items-center gap-2 bg-white border border-neutral-200 hover:border-brand-red hover:text-brand-red text-sm font-medium text-neutral-700 px-4 py-2 rounded-full transition-colors"
              >
                <span>{other.emoji}</span>
                {other.label}
              </Link>
            ))}
          </div>
        </section>
      </div>
    </>
  )
}
