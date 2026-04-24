'use client'

import Link from 'next/link'
import Image from 'next/image'
import { ArrowRight } from 'lucide-react'
import { useState } from 'react'
import type { Store } from '@/lib/data'

export default function StoreCard({ store }: { store: Store }) {
  const [imgError, setImgError] = useState(false)
  const showLogo = !!(store.logo_url && !imgError)

  return (
    <Link
      href={`/reduceri/${store.slug}`}
      className="card-hover p-6 flex items-center gap-4 group"
    >
      <div
        className="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0 overflow-hidden"
        style={{ backgroundColor: store.culoare + '20' }}
      >
        {showLogo ? (
          <Image
            src={store.logo_url!}
            alt={store.nume}
            width={48}
            height={48}
            className="w-10 h-10 object-contain"
            onError={() => setImgError(true)}
          />
        ) : (
          <span className="text-2xl">{store.logo_emoji || '🛍️'}</span>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <h3 className="font-display font-semibold text-neutral-900 group-hover:text-brand-red transition-colors">
          {store.nume}
        </h3>
        <p className="text-sm text-neutral-500 truncate">
          Reduceri și coduri promoționale
        </p>
      </div>
      <ArrowRight className="w-5 h-5 text-neutral-400 group-hover:text-brand-red group-hover:translate-x-1 transition-all shrink-0" />
    </Link>
  )
}
