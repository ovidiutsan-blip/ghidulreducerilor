import { Zap } from 'lucide-react'
import FlashDealCard from '@/components/FlashDealCard'
import type { Deal } from '@/lib/data'

export default function FlashDeals({ deals }: { deals: Deal[] }) {
  if (deals.length === 0) return null

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center gap-2 mb-5">
        <div className="w-8 h-8 bg-amber-500/10 rounded-lg flex items-center justify-center">
          <Zap className="w-4 h-4 text-amber-500" />
        </div>
        <h2 className="font-display font-bold text-xl text-neutral-900">Oferte Flash</h2>
        <span className="text-sm text-neutral-400 ml-2">Top {deals.length} reduceri</span>
      </div>
      <div className="flex gap-3 overflow-x-auto scrollbar-hide snap-x snap-mandatory pb-2">
        {deals.map((deal, i) => (
          <FlashDealCard key={deal.id} deal={deal} priority={i < 3} />
        ))}
      </div>
    </section>
  )
}
