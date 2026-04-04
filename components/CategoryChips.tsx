'use client'

import { CATEGORIES } from '@/lib/categories'

export default function CategoryChips({
  selected,
  onSelect,
  counts,
}: {
  selected: string
  onSelect: (slug: string) => void
  counts: Record<string, number>
}) {
  return (
    <div className="flex gap-2 overflow-x-auto scrollbar-hide pb-1">
      <button
        onClick={() => onSelect('all')}
        className={`shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
          selected === 'all'
            ? 'bg-brand-red text-white'
            : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
        }`}
      >
        Toate
      </button>
      {CATEGORIES.map(cat => {
        const count = counts[cat.slug] || 0
        if (count === 0) return null
        return (
          <button
            key={cat.slug}
            onClick={() => onSelect(cat.slug)}
            className={`shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              selected === cat.slug
                ? 'bg-brand-red text-white'
                : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200'
            }`}
          >
            {cat.label}
            <span className="ml-1 opacity-60">({count})</span>
          </button>
        )
      })}
    </div>
  )
}
