'use client'

import { useState, useMemo } from 'react'
import { Filter, ArrowUpDown, X } from 'lucide-react'
import DealCard from '@/components/DealCard'
import { CATEGORIES } from '@/lib/categories'
import type { Deal } from '@/lib/data'

type SortOption = 'discount' | 'pret_asc' | 'pret_desc' | 'newest'

export default function DealsFilter({
  deals,
  magazines,
}: {
  deals: Deal[]
  magazines: string[]
}) {
  const [selectedMagazin, setSelectedMagazin] = useState<string>('all')
  const [selectedCategorie, setSelectedCategorie] = useState<string>('all')
  const [sortBy, setSortBy] = useState<SortOption>('discount')
  const [pretMin, setPretMin] = useState('')
  const [pretMax, setPretMax] = useState('')

  const categories = useMemo(() => {
    const cats = Array.from(new Set(deals.map(d => d.categorie))).sort()
    return cats
  }, [deals])

  const activeFilters = (selectedMagazin !== 'all' ? 1 : 0)
    + (selectedCategorie !== 'all' ? 1 : 0)
    + (pretMin ? 1 : 0)
    + (pretMax ? 1 : 0)

  function clearFilters() {
    setSelectedMagazin('all')
    setSelectedCategorie('all')
    setPretMin('')
    setPretMax('')
    setSortBy('discount')
  }

  const filtered = useMemo(() => {
    let result = deals

    if (selectedMagazin !== 'all') {
      result = result.filter(d => d.magazin === selectedMagazin)
    }
    if (selectedCategorie !== 'all') {
      result = result.filter(d => d.categorie === selectedCategorie)
    }
    if (pretMin) {
      const min = parseFloat(pretMin)
      if (!isNaN(min)) result = result.filter(d => d.pret_redus >= min)
    }
    if (pretMax) {
      const max = parseFloat(pretMax)
      if (!isNaN(max)) result = result.filter(d => d.pret_redus <= max)
    }

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
      case 'newest':
        result = [...result].sort((a, b) => b.data_adaugare.localeCompare(a.data_adaugare))
        break
    }

    return result
  }, [deals, selectedMagazin, selectedCategorie, sortBy, pretMin, pretMax])

  return (
    <>
      {/* Filters bar */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        {/* Magazine filter */}
        {magazines.length > 1 && (
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
        )}

        {/* Category filter */}
        {categories.length > 1 && (
          <select
            value={selectedCategorie}
            onChange={(e) => setSelectedCategorie(e.target.value)}
            className="text-sm border border-neutral-200 rounded-lg px-3 py-2 bg-white text-neutral-700 focus:outline-none focus:ring-2 focus:ring-brand-red/20 focus:border-brand-red"
          >
            <option value="all">Toate categoriile</option>
            {categories.map(c => {
              const cat = CATEGORIES.find(x => x.slug === c)
              return (
                <option key={c} value={c}>{cat ? cat.label : c}</option>
              )
            })}
          </select>
        )}

        {/* Price range */}
        <div className="flex items-center gap-1">
          <input
            type="number"
            placeholder="Pret min"
            value={pretMin}
            onChange={e => setPretMin(e.target.value)}
            className="w-24 text-sm border border-neutral-200 rounded-lg px-3 py-2 bg-white text-neutral-700 focus:outline-none focus:ring-2 focus:ring-brand-red/20 focus:border-brand-red"
          />
          <span className="text-neutral-400">-</span>
          <input
            type="number"
            placeholder="Pret max"
            value={pretMax}
            onChange={e => setPretMax(e.target.value)}
            className="w-24 text-sm border border-neutral-200 rounded-lg px-3 py-2 bg-white text-neutral-700 focus:outline-none focus:ring-2 focus:ring-brand-red/20 focus:border-brand-red"
          />
        </div>

        {/* Sort */}
        <div className="flex items-center gap-2">
          <ArrowUpDown className="w-4 h-4 text-neutral-400" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="text-sm border border-neutral-200 rounded-lg px-3 py-2 bg-white text-neutral-700 focus:outline-none focus:ring-2 focus:ring-brand-red/20 focus:border-brand-red"
          >
            <option value="discount">Discount descrescator</option>
            <option value="pret_asc">Pret crescator</option>
            <option value="pret_desc">Pret descrescator</option>
            <option value="newest">Cele mai noi</option>
          </select>
        </div>

        {/* Clear + count */}
        <div className="flex items-center gap-2 ml-auto">
          {activeFilters > 0 && (
            <button
              onClick={clearFilters}
              className="flex items-center gap-1 text-sm text-brand-red hover:text-brand-red-dark"
            >
              <X className="w-3.5 h-3.5" />
              Sterge filtre ({activeFilters})
            </button>
          )}
          <span className="text-sm text-neutral-400">
            {filtered.length} oferte
          </span>
        </div>
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
          <p className="text-neutral-400 text-lg">Nicio oferta gasita pentru filtrele selectate.</p>
          <button onClick={clearFilters} className="mt-3 text-brand-red hover:underline text-sm">
            Sterge filtrele
          </button>
        </div>
      )}
    </>
  )
}
