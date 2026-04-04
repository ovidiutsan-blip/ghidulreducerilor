import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import Breadcrumb from '@/components/Breadcrumb'
import DealsFilter from '@/components/DealsFilter'
import { getDealsByCategory, getAllCategories, getUniqueMagazine } from '@/lib/data'
import { getCategoryBySlug, CATEGORIES } from '@/lib/categories'
import { getCurrentMonthYear } from '@/lib/utils'

type Props = { params: { slug: string } }

export function generateStaticParams() {
  const categories = getAllCategories()
  return categories.map(slug => ({ slug }))
}

export function generateMetadata({ params }: Props): Metadata {
  const cat = getCategoryBySlug(params.slug)
  if (!cat) return {}
  const month = getCurrentMonthYear()
  return {
    title: `Reduceri ${cat.label} — Oferte ${month}`,
    description: `Cele mai bune reduceri la ${cat.label.toLowerCase()} din Romania. Oferte verificate zilnic cu discount-uri reale.`,
    alternates: { canonical: `/categorie/${params.slug}` },
  }
}

export default function CategoryPage({ params }: Props) {
  const slug = params.slug
  const cat = getCategoryBySlug(slug)
  if (!cat) notFound()

  const deals = getDealsByCategory(slug)
  const magazines = Array.from(new Set(deals.map(d => d.magazin))).sort()
  const Icon = cat.icon

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: `Reduceri ${cat.label}`,
    numberOfItems: deals.length,
    itemListElement: deals.slice(0, 10).map((deal, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: deal.titlu,
      url: `https://ghidulreducerilor.ro/out/${deal.id}`,
    })),
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumb items={[
          { label: 'Acasa', href: '/' },
          { label: cat.label },
        ]} />

        <div className="flex items-center gap-3 mb-8 mt-4">
          <div className="w-12 h-12 bg-brand-red/10 rounded-xl flex items-center justify-center">
            <Icon className="w-6 h-6 text-brand-red" />
          </div>
          <div>
            <h1 className="font-display font-bold text-2xl sm:text-3xl text-neutral-900">
              Reduceri {cat.label}
            </h1>
            <p className="text-sm text-neutral-500">{deals.length} oferte active</p>
          </div>
        </div>

        <DealsFilter deals={deals} magazines={magazines} />
      </div>
    </>
  )
}
