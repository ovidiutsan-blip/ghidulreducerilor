'use client'

import { useState, useEffect } from 'react'
import { Cookie } from 'lucide-react'

export default function CookieConsent() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const consent = localStorage.getItem('cookie_consent')
    if (!consent) {
      // Arata bannerul dupa 1.5s
      const t = setTimeout(() => setVisible(true), 1500)
      return () => clearTimeout(t)
    }
  }, [])

  const accept = () => {
    localStorage.setItem('cookie_consent', 'all')
    setVisible(false)
    // Activeaza GA4 dupa accept
    if (typeof window !== 'undefined' && (window as any).gtag) {
      ;(window as any).gtag('consent', 'update', {
        analytics_storage: 'granted',
        ad_storage: 'denied',
      })
    }
  }

  const acceptNecessary = () => {
    localStorage.setItem('cookie_consent', 'necessary')
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 sm:p-6">
      <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-2xl border border-neutral-200 p-5 sm:p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center shrink-0">
            <Cookie className="w-5 h-5 text-amber-500" />
          </div>
          <div className="flex-1">
            <p className="font-semibold text-neutral-900 text-sm mb-1">Folosim cookie-uri</p>
            <p className="text-neutral-500 text-xs leading-relaxed">
              Folosim cookie-uri pentru statistici (Google Analytics) și pentru a îmbunătăți experiența ta.
              Nu vindem datele tale.{' '}
              <a href="/despre#confidentialitate" className="text-brand-red hover:underline">
                Politica de confidențialitate
              </a>
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0 w-full sm:w-auto">
            <button
              onClick={acceptNecessary}
              className="flex-1 sm:flex-none text-sm text-neutral-500 hover:text-neutral-700 px-4 py-2 rounded-xl border border-neutral-200 hover:border-neutral-300 transition-colors"
            >
              Doar necesare
            </button>
            <button
              onClick={accept}
              className="flex-1 sm:flex-none btn-cta text-sm px-5 py-2"
            >
              Accept toate
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
