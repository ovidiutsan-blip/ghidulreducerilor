'use client'

import { useState } from 'react'
import { Copy, ExternalLink, Check, ShieldCheck, AlertTriangle } from 'lucide-react'
import { isExpired, copyToClipboard } from '@/lib/utils'
import type { PromoCode } from '@/lib/data'

export default function PromoCodeCard({ code }: { code: PromoCode }) {
  const [copied, setCopied] = useState(false)
  const expired = isExpired(code.data_expirare)

  const handleCopy = async () => {
    const success = await copyToClipboard(code.cod)
    if (success) {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      // Deschide link-ul afiliat în tab nou
      window.open(code.link_afiliat, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <div className={`card-hover p-5 ${expired ? 'opacity-60' : ''}`}>
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        {/* Info cod */}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            {expired ? (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
                <AlertTriangle className="w-3 h-3" /> Expirat
              </span>
            ) : code.verificat ? (
              <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
                <ShieldCheck className="w-3 h-3" /> Verificat azi
              </span>
            ) : null}
          </div>
          <p className="font-medium text-neutral-900 mb-1">{code.descriere}</p>
          <p className="text-sm text-neutral-500">
            Valoare: <strong className="text-brand-red">{code.valoare}</strong>
            {' · '}Expiră: {new Date(code.data_expirare).toLocaleDateString('ro-RO')}
          </p>
        </div>

        {/* Cod + Buton */}
        <div className="flex items-center gap-3">
          <code className="font-mono font-medium text-sm bg-neutral-100 border border-dashed border-neutral-300 px-4 py-2.5 rounded-lg select-all">
            {code.cod}
          </code>
          <button
            onClick={handleCopy}
            disabled={expired}
            className={`btn-cta text-sm whitespace-nowrap ${expired ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {copied ? (
              <>
                <Check className="w-4 h-4" /> Copiat!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" /> Copiază + Cumpără
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
