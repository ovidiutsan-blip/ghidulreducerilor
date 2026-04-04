'use client'

import { useState, useEffect } from 'react'
import { Clock } from 'lucide-react'
import { getRecentlyViewed } from '@/lib/recently-viewed'
import FlashDealCard from '@/components/FlashDealCard'
import type { Deal } from '@/lib/data'

export default function RecentlyViewed({ allDeals }: { allDeals: Deal[] }) {
  const [deals, setDeals] = useState<Deal[]>([])

  useEffect(() => {
    const ids = getRecentlyViewed()
    if (ids.length === 0) return
    const dealsMap = new Map(allDeals.map(d => [d.id, d]))
    const recent = ids.map(id => dealsMap.get(id)).filter(Boolean) as Deal[]
    setDeals(recent)
  }, [allDeals])

  if (deals.length === 0) return null

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center gap-2 mb-5">
        <div className="w-8 h-8 bg-blue-500/10 rounded-lg flex items-center justify-center">
          <Clock className="w-4 h-4 text-blue-500" />
        </div>
        <h2 className="font-display font-bold text-xl text-neutral-900">Recent vizualizate</h2>
      </div>
      <div className="flex gap-3 overflow-x-auto scrollbar-hide snap-x snap-mandatory pb-2">
        {deals.map(deal => (
          <FlashDealCard key={deal.id} deal={deal} />
        ))}
      </div>
    </section>
  )
}
