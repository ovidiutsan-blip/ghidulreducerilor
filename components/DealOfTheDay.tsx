'use client'

import Image from 'next/image'
import { useState } from 'react'
import { Crown, ExternalLink, ImageOff, TrendingDown } from 'lucide-react'
import { formatPrice } from '@/lib/utils'
import CountdownTimer from '@/components/CountdownTimer'
import type { Deal } from '@/lib/data'

export default function DealOfTheDay({ deal }: { deal: Deal }) {
  const [imgError, setImgError] = useState(false)
  const economie = deal.pret_original - deal.pret_redus

  return (
    <section className="bg-gradient-to-br from-neutral-900 via-neutral-800 to-neutral-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-amber-500/20 rounded-lg flex items-center justify-center">
              <Crown className="w-4 h-4 text-amber-400" />
            </div>
            <h2 className="font-display font-bold text-lg sm:text-xl">Oferta Zilei</h2>
          </div>
          <CountdownTimer />
        </div>

        {/* Deal content */}
        <div className="flex flex-col md:flex-row items-center gap-6 md:gap-10">
          {/* Image */}
          <div className="relative w-full md:w-1/3 aspect-square max-w-xs bg-white rounded-2xl overflow-hidden shrink-0">
            {imgError ? (
              <div className="absolute inset-0 bg-neutral-100 flex items-center justify-center">
                <ImageOff className="w-12 h-12 text-neutral-300" />
              </div>
            ) : (
              <Image
                src={deal.imagine_url}
                alt={deal.titlu}
                fill
                className="object-cover"
                sizes="(max-width: 768px) 80vw, 300px"
                onError={() => setImgError(true)}
                priority
              />
            )}
            <span className="absolute top-3 left-3 bg-brand-red text-white text-lg font-bold px-3 py-1.5 rounded-xl shadow-lg">
              -{deal.procent_reducere}%
            </span>
          </div>

          {/* Info */}
          <div className="flex-1 text-center md:text-left">
            <p className="text-sm text-neutral-400 uppercase tracking-wider mb-2">{deal.magazin}</p>
            <h3 className="font-display font-bold text-2xl sm:text-3xl leading-tight mb-4">
              {deal.titlu}
            </h3>

            <div className="flex items-baseline gap-3 justify-center md:justify-start mb-2">
              <span className="text-4xl sm:text-5xl font-bold text-white">{formatPrice(deal.pret_redus)}</span>
              <span className="text-xl text-neutral-500 line-through">{formatPrice(deal.pret_original)}</span>
            </div>

            <p className="text-emerald-400 font-medium text-lg mb-6">
              Economisesti {formatPrice(economie)}
            </p>

            <a
              href={`/out/${deal.id}`}
              target="_blank"
              rel="noopener noreferrer nofollow"
              className="inline-flex items-center justify-center gap-2 bg-brand-red hover:bg-brand-red-dark text-white font-bold px-8 py-4 rounded-xl text-lg transition-all hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0"
            >
              <TrendingDown className="w-5 h-5" />
              Vezi Oferta
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}
