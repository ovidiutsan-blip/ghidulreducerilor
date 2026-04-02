'use client'

import { Flame, Clock, Users, TrendingDown } from 'lucide-react'
import { getActiveDeals } from '@/lib/data'

export default function TrustBar({ totalDeals }: { totalDeals: number }) {
  return (
    <div className="bg-neutral-900 border-b border-neutral-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-center gap-6 sm:gap-10 py-2.5 text-xs sm:text-sm text-neutral-300 overflow-x-auto scrollbar-hide">
          <span className="flex items-center gap-1.5 shrink-0">
            <Flame className="w-3.5 h-3.5 text-brand-red" />
            <strong className="text-white">{totalDeals}+</strong> oferte active
          </span>
          <span className="hidden sm:flex items-center gap-1.5 shrink-0 text-neutral-500">|</span>
          <span className="flex items-center gap-1.5 shrink-0">
            <Clock className="w-3.5 h-3.5 text-emerald-400" />
            Actualizat <strong className="text-white">zilnic</strong>
          </span>
          <span className="hidden sm:flex items-center gap-1.5 shrink-0 text-neutral-500">|</span>
          <span className="flex items-center gap-1.5 shrink-0">
            <Users className="w-3.5 h-3.5 text-blue-400" />
            <strong className="text-white">10.000+</strong> abonați
          </span>
          <span className="hidden sm:flex items-center gap-1.5 shrink-0 text-neutral-500">|</span>
          <span className="flex items-center gap-1.5 shrink-0">
            <TrendingDown className="w-3.5 h-3.5 text-amber-400" />
            Economii medii <strong className="text-white">34%</strong>
          </span>
        </div>
      </div>
    </div>
  )
}
