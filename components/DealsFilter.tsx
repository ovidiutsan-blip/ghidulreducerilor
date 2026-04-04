'use client'

import { useState, useMemo } from 'react'
import { Filter, ArrowUpDown } from 'lucide-react'
import DealCard from '@/components/DealCard'
import type { Deal } from '@/lib/data'

type SortOption = 'discount' | 'pret_asc' | 'pret_desc'

export default function DealsFilter({
  deals,
  magazines,
}: {
  deals: Deal[]
  magazines: string[]
}) {
  const [selectedMagazin, setSelectedMagazin] = useState<string>('all')
  const [sortBy, setSortBy] = useState<SortOption>('discount')

  const filtered = useMemo(() => {
    let result = deals

    // Filter by magazine
    if (selectedMagazin !== 'all') {
      result = result.filter(d => d.magazin === selectedMagazin)
    }

    // Sort
    switch (sortBy) {
      case 'discount':
        result = [...result].sort((a, b) => b.procent_reducere - a.procent_reducere)
        break
      case 'pret_asc':
        result = [...result].sort((a, b) => a.pret_redus - b.pret_redus)
        break
      case 'pret_desc':
        result = [...result].sort((a, b) => b.pret_redus - a.pret_redus)
        break
    }

    return result
  }, [deals, selectedMagazin, sortBy])

  return (
    <>
      {/* Filters bar */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        {/* Magazine filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-neutral-400" />
          <select
            value={selectedMagazin}
            onChange={(e) => setSelectedMagazin(e.target.value)}
            className="text-sm border border-neutral-200 rounded-lg px-3 py-2 bg-white text-neutral-700 focus:outline-none focus:ring-2 focus:ring-brand-red/20 focus:border-brand-red"
          >
            <option value="all">Toate magazinele</option>
            {magazines.map(m => (
              <option key={m} value={m}>
                {m.charAt(0).toUpperCase() + m.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Sort */}
        <div className="flex items-center gap-2">
          <ArrowUpDown className="w-4 h-4 text-neutral-400" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="text-sm border border-neutral-200 rounded-lg px-3 py-2 bg-white text-neutral-700 focus:outline-none focus:ring-2 focus:ring-brand-red/20 focus:border-brand-red"
          >
            <option value="discount">Discount descrescător</option>
            <option value="pret_asc">Preț crescător</option>
            <option value="pret_desc">Preț descrescător</option>
          </select>
        </div>

        {/* Count */}
        <span className="text-sm text-neutral-400 ml-auto">
          {filtered.length} oferte
        </span>
      </div>

      {/* Grid */}
      {filtered.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-6">
          {filtered.map(deal => (
            <DealCard key={deal.id} deal={deal} />
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <p className="text-neutral-400 text-lg">Nicio ofertă găsită pentru filtrele selectate.</p>
        </div>
      )}
    </>
  )
}
