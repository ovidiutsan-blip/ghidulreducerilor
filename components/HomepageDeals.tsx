'use client'

import { useState, useMemo } from 'react'
import { Flame } from 'lucide-react'
import DealCard from '@/components/DealCard'
import CategoryChips from '@/components/CategoryChips'
import type { Deal } from '@/lib/data'

export default function HomepageDeals({ deals }: { deals: Deal[] }) {
  const [selected, setSelected] = useState('all')

  const counts = useMemo(() => {
    const map: Record<string, number> = {}
    deals.forEach(d => {
      map[d.categorie] = (map[d.categorie] || 0) + 1
    })
    return map
  }, [deals])

  const filtered = useMemo(() => {
    if (selected === 'all') return deals
    return deals.filter(d => d.categorie === selected)
  }, [deals, selected])

  return (
    <section id="reduceri" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-brand-red/10 rounded-xl flex items-center justify-center">
          <Flame className="w-5 h-5 text-brand-red" />
        </div>
        <div>
          <h2 className="font-display font-bold text-2xl text-neutral-900">Reducerile Zilei</h2>
          <p className="text-sm text-neutral-500">{deals.length} oferte active — verificate azi</p>
        </div>
      </div>

      <CategoryChips selected={selected} onSelect={setSelected} counts={counts} />

      <div className="mt-6 grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-6">
        {filtered.map(deal => (
          <DealCard key={deal.id} deal={deal} />
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="text-center text-neutral-400 py-12">Nicio oferta in aceasta categorie.</p>
      )}
    </section>
  )
}
