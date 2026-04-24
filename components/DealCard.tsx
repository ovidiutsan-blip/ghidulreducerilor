'use client'

import Image from 'next/image'
import { useState } from 'react'
import { ExternalLink, ImageOff, Star, Truck } from 'lucide-react'
import { formatPrice } from '@/lib/utils'
import { addRecentlyViewed } from '@/lib/recently-viewed'
import { FAST_DELIVERY_STORES } from '@/lib/categories'
import type { Deal } from '@/lib/data'

const STORE_INFO: Record<string, { emoji: string; name: string }> = {
  emag: { emoji: '🛒', name: 'eMAG' },
  watch24: { emoji: '⌚', name: 'Watch24' },
  forit: { emoji: '🖥️', name: 'ForIT' },
  fornello: { emoji: '🔥', name: 'Fornello' },
}

function FallbackImage({ title }: { title: string }) {
  return (
    <div className="absolute inset-0 bg-gradient-to-br from-neutral-100 to-neutral-200 flex flex-col items-center justify-center p-4 text-center">
      <ImageOff className="w-10 h-10 text-neutral-300 mb-2" />
      <span className="text-xs text-neutral-400 line-clamp-2">{title}</span>
    </div>
  )
}

function isBadImageUrl(url: string | null | undefined): boolean {
  if (!url) return true
  return url.includes('lazy-loader') || url.endsWith('.gif')
}

export default function DealCard({ deal }: { deal: Deal }) {
  const [imgError, setImgError] = useState(() => isBadImageUrl(deal.imagine_url))
  const economie = deal.pret_original - deal.pret_redus
  const store = STORE_INFO[deal.magazin]
  const hasFastDelivery = FAST_DELIVERY_STORES.includes(deal.magazin)

  function handleClick() {
    addRecentlyViewed(deal.id)
  }

  return (
    <a
      href={`/out/${deal.id}`}
      target="_blank"
      rel="noopener noreferrer nofollow"
      className="card-hover overflow-hidden flex flex-col block group"
      itemScope
      itemType="https://schema.org/Product"
      onClick={handleClick}
    >
      {/* Image + badges */}
      <div className="relative aspect-square bg-white overflow-hidden">
        {imgError ? (
          <FallbackImage title={deal.titlu} />
        ) : (
          <div className="absolute inset-2">
            <Image
              src={deal.imagine_url}
              alt={`${deal.titlu} — reducere ${deal.procent_reducere}% de la ${formatPrice(deal.pret_original)} la ${formatPrice(deal.pret_redus)}`}
              fill
              className="object-contain group-hover:scale-105 transition-transform duration-300"
              sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
              onError={() => setImgError(true)}
            />
          </div>
        )}
        <span className="badge-discount">-{deal.procent_reducere}%</span>

        {/* Store badge */}
        {store && (
          <span className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm text-xs font-medium text-neutral-700 px-2 py-1 rounded-lg shadow-sm">
            {store.emoji} {store.name}
          </span>
        )}
      </div>

      {/* Schema microdata */}
      <meta itemProp="image" content={deal.imagine_url} />
      <meta itemProp="description" content={`${deal.titlu} — reducere ${deal.procent_reducere}% de la ${formatPrice(deal.pret_original)} la ${formatPrice(deal.pret_redus)}`} />

      {/* Content */}
      <div className="p-3 sm:p-4 flex flex-col flex-1">
        <h3 className="font-display font-semibold text-neutral-900 text-sm leading-snug mb-2 line-clamp-2" itemProp="name">
          {deal.titlu}
        </h3>

        {/* Rating placeholder + delivery */}
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <div className="flex items-center gap-0.5">
            {[1, 2, 3, 4, 5].map(i => (
              <Star key={i} className={`w-3 h-3 ${i <= 4 ? 'text-amber-400 fill-amber-400' : 'text-neutral-200'}`} />
            ))}
          </div>
          {hasFastDelivery && (
            <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">
              <Truck className="w-3 h-3" />
              Livrare rapida
            </span>
          )}
        </div>

        {/* Prices */}
        <div className="mt-auto" itemProp="offers" itemScope itemType="https://schema.org/Offer">
          <div className="flex items-baseline gap-2 mb-1">
            <span className="price-new" itemProp="price" content={String(deal.pret_redus)}>
              {formatPrice(deal.pret_redus)}
            </span>
            <span className="price-old">{formatPrice(deal.pret_original)}</span>
          </div>
          <p className="text-xs text-emerald-600 font-medium mb-3">
            Economisesti {formatPrice(economie)}
          </p>
          <meta itemProp="priceCurrency" content="RON" />
          <meta itemProp="availability" content="https://schema.org/InStock" />
          <meta itemProp="url" content={`https://ghidulreducerilor.ro/out/${deal.id}`} />
          <div itemProp="shippingDetails" itemScope itemType="https://schema.org/OfferShippingDetails" className="hidden">
            <div itemProp="shippingDestination" itemScope itemType="https://schema.org/DefinedRegion">
              <meta itemProp="addressCountry" content="RO" />
            </div>
          </div>
          <div itemProp="hasMerchantReturnPolicy" itemScope itemType="https://schema.org/MerchantReturnPolicy" className="hidden">
            <meta itemProp="applicableCountry" content="RO" />
            <meta itemProp="returnPolicyCategory" content="https://schema.org/MerchantReturnFiniteReturnWindow" />
            <meta itemProp="merchantReturnDays" content="14" />
          </div>

          <span className="btn-cta w-full text-sm">
            Vezi oferta
            <ExternalLink className="w-4 h-4" />
          </span>
        </div>
      </div>
    </a>
  )
}
