'use client'

import Image from 'next/image'
import { useState } from 'react'
import { ImageOff } from 'lucide-react'
import { formatPrice } from '@/lib/utils'
import type { Deal } from '@/lib/data'

function isBadImageUrl(url: string | null | undefined): boolean {
  if (!url) return true
  return url.includes('lazy-loader') || url.endsWith('.gif')
}

export default function FlashDealCard({ deal, priority = false }: { deal: Deal; priority?: boolean }) {
  const [imgError, setImgError] = useState(() => isBadImageUrl(deal.imagine_url))

  return (
    <a
      href={`/out/${deal.id}`}
      target="_blank"
      rel="noopener noreferrer nofollow"
      className="flex-shrink-0 w-40 sm:w-48 snap-start bg-white rounded-xl border border-neutral-200 overflow-hidden hover:shadow-md transition-shadow group"
    >
      <div className="relative aspect-square bg-white overflow-hidden">
        {imgError ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <ImageOff className="w-8 h-8 text-neutral-300" />
          </div>
        ) : (
          <div className="absolute inset-1.5">
            <Image
              src={deal.imagine_url}
              alt={deal.titlu}
              fill
              className="object-contain group-hover:scale-105 transition-transform duration-300"
              sizes="192px"
              priority={priority}
              onError={() => setImgError(true)}
            />
          </div>
        )}
        <span className="absolute top-2 left-2 bg-brand-red text-white text-xs font-bold px-2 py-0.5 rounded-lg">
          -{deal.procent_reducere}%
        </span>
      </div>
      <div className="p-3">
        <p className="text-xs text-neutral-600 line-clamp-2 mb-2 leading-tight">{deal.titlu}</p>
        <div className="flex items-baseline gap-1.5">
          <span className="text-sm font-bold text-brand-red">{formatPrice(deal.pret_redus)}</span>
          <span className="text-xs text-neutral-400 line-through">{formatPrice(deal.pret_original)}</span>
        </div>
      </div>
    </a>
  )
}
