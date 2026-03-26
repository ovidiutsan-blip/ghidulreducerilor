import Image from 'next/image'
import { ExternalLink } from 'lucide-react'
import { formatPrice } from '@/lib/utils'
import type { Deal } from '@/lib/data'

export default function DealCard({ deal }: { deal: Deal }) {
  return (
    <article className="card-hover overflow-hidden flex flex-col" itemScope itemType="https://schema.org/Product">
      {/* Imagine + Badge reducere */}
      <div className="relative aspect-square bg-neutral-100">
        <Image
          src={deal.imagine_url}
          alt={deal.titlu}
          fill
          className="object-cover"
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
        />
        <span className="badge-discount">-{deal.procent_reducere}%</span>
      </div>

      {/* Conținut */}
      <div className="p-4 flex flex-col flex-1">
        <h3 className="font-display font-semibold text-neutral-900 text-sm leading-snug mb-3 line-clamp-2" itemProp="name">
          {deal.titlu}
        </h3>

        {/* Prețuri */}
        <div className="mt-auto" itemProp="offers" itemScope itemType="https://schema.org/Offer">
          <div className="flex items-baseline gap-3 mb-3">
            <span className="price-new" itemProp="price" content={String(deal.pret_redus)}>
              {formatPrice(deal.pret_redus)}
            </span>
            <span className="price-old">{formatPrice(deal.pret_original)}</span>
          </div>
          <meta itemProp="priceCurrency" content="RON" />
          <meta itemProp="availability" content="https://schema.org/InStock" />

          <a
            href={deal.link_afiliat}
            target="_blank"
            rel="noopener noreferrer nofollow"
            className="btn-cta w-full text-sm"
          >
            Vezi oferta
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </article>
  )
}
