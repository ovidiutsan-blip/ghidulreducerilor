'use client'

import Link from 'next/link'
import { CATEGORIES } from '@/lib/categories'

// availableSlugs: categoriile care au deal-uri active (calculate server-side
// în layout). Fără filtru, bara ducea la pagini de categorie goale.
export default function CategoryBar({ availableSlugs }: { availableSlugs?: string[] }) {
  const visible = availableSlugs
    ? CATEGORIES.filter(c => availableSlugs.includes(c.slug))
    : CATEGORIES
  return (
    <div className="sticky top-16 z-40 bg-white border-b border-neutral-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-1 py-2 overflow-x-auto scrollbar-hide snap-x snap-mandatory">
          {visible.map(cat => {
            const Icon = cat.icon
            return (
              <Link
                key={cat.slug}
                href={`/categorie/${cat.slug}`}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium text-neutral-600 hover:bg-brand-red/10 hover:text-brand-red transition-colors whitespace-nowrap shrink-0 snap-start"
              >
                <Icon className="w-4 h-4" />
                {cat.label}
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}
