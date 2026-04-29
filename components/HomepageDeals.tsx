'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { Flame, ArrowRight } from 'lucide-react'
import DealCard from '@/components/DealCard'
import CategoryChips from '@/components/CategoryChips'
import type { Deal } from '@/lib/data'

const VISIBLE_INITIAL = 24
const VISIBLE_INCREMENT = 24

type Props = {
  deals: Deal[]
  totalCount: number
  categoryCounts: Record<string, number>
}

export default function HomepageDeals({ deals, totalCount, categoryCounts }: Props) {
  const [selected, setSelected] = useState('all')
  const [visibleCount, setVisibleCount] = useState(VISIBLE_INITIAL)

  const filtered = useMemo(() => {
    if (selected === 'all') return deals
    return deals.filter(d => d.categorie === selected)
  }, [deals, selected])

  const visible = filtered.slice(0, visibleCount)
  const hasMore = visible.length < filtered.length
  const truncatedByLimit = selected !== 'all' && (categoryCounts[selected] ?? 0) > deals.length

  // Reset visibleCount când utilizatorul schimbă filtrul
  function handleSelect(slug: string) {
    setSelected(slug)
    setVisibleCount(VISIBLE_INITIAL)
  }

  return (
    <section id="reduceri" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-brand-red/10 rounded-xl flex items-center justify-center">
          <Flame className="w-5 h-5 text-brand-red" />
        </div>
        <div>
          <h2 className="font-display font-bold text-2xl text-neutral-900">Reducerile Zilei</h2>
          <p className="text-sm text-neutral-500">{totalCount} oferte active — verificate azi</p>
        </div>
      </div>

      <CategoryChips selected={selected} onSelect={handleSelect} counts={categoryCounts} />

      <div className="mt-6 grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-6">
        {visible.map(deal => (
          <DealCard key={deal.id} deal={deal} />
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="text-center text-neutral-400 py-12">Nicio oferta in aceasta categorie.</p>
      )}

      {(hasMore || truncatedByLimit) && (
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
          {hasMore && (
            <button
              onClick={() => setVisibleCount(c => c + VISIBLE_INCREMENT)}
              className="btn-cta-outline text-sm"
            >
              Mai multe oferte ({Math.min(VISIBLE_INCREMENT, filtered.length - visible.length)})
            </button>
          )}
          {(truncatedByLimit || (selected === 'all' && totalCount > deals.length)) && (
            <Link
              href={selected === 'all' ? '/deals' : `/categorie/${selected}`}
              className="btn-cta text-sm"
            >
              Vezi toate {selected === 'all' ? totalCount : (categoryCounts[selected] ?? 0)} oferte
              <ArrowRight className="w-4 h-4" />
            </Link>
          )}
        </div>
      )}
    </section>
  )
}
