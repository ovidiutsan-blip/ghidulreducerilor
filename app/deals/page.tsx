import { Metadata } from 'next'
import { Flame } from 'lucide-react'
import DealsFilter from '@/components/DealsFilter'
import { getActiveDeals, getUniqueMagazine } from '@/lib/data'
import { buildItemListSchema, buildBreadcrumbSchema } from '@/lib/schema'

export const metadata: Metadata = {
  title: 'Reduceri și Oferte | Ghidul Reducerilor',
  description: 'Toate reducerile și ofertele active din România — filtrează după magazin, sortează după discount sau preț. Oferte verificate zilnic.',
  alternates: { canonical: '/deals' },
  openGraph: {
    title: 'Reduceri și Oferte | Ghidul Reducerilor',
    description: 'Toate reducerile active din România — oferte verificate zilnic, prețuri reale.',
    images: [{ url: 'https://ghidulreducerilor.ro/api/og', width: 1200, height: 630 }],
  },
}

export default function DealsPage() {
  const deals = getActiveDeals()
  const magazines = getUniqueMagazine()

  const itemListSchema = buildItemListSchema('Toate Reducerile Active', deals, '/deals')
  const breadcrumbSchema = buildBreadcrumbSchema([
    { name: 'Acasă', href: '/' },
    { name: 'Toate Reducerile' },
  ])

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(itemListSchema) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbSchema) }} />
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 bg-brand-red/10 rounded-xl flex items-center justify-center">
          <Flame className="w-5 h-5 text-brand-red" />
        </div>
        <div>
          <h1 className="font-display font-bold text-2xl text-neutral-900">Toate Reducerile</h1>
          <p className="text-sm text-neutral-500">{deals.length} oferte active — verificate azi</p>
        </div>
      </div>

      <DealsFilter deals={deals} magazines={magazines} />
    </section>
    </>
  )
}
