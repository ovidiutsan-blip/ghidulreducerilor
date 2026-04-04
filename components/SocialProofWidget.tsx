'use client'

import { useEffect, useState } from 'react'
import { ShoppingBag } from 'lucide-react'

const NOTIFICATIONS = [
  { nume: 'Andrei din Cluj', economie: '89', magazin: 'eMAG' },
  { nume: 'Maria din București', economie: '124', magazin: 'eMAG' },
  { nume: 'Ion din Timișoara', economie: '67', magazin: 'eMAG' },
  { nume: 'Elena din Iași', economie: '203', magazin: 'eMAG' },
  { nume: 'Mihai din Brașov', economie: '45', magazin: 'eMAG' },
  { nume: 'Alina din Constanța', economie: '156', magazin: 'eMAG' },
  { nume: 'Bogdan din Ploiești', economie: '78', magazin: 'eMAG' },
  { nume: 'Roxana din Craiova', economie: '92', magazin: 'eMAG' },
]

export default function SocialProofWidget() {
  const [current, setCurrent] = useState<typeof NOTIFICATIONS[0] | null>(null)
  const [visible, setVisible] = useState(false)
  const [index, setIndex] = useState(0)

  useEffect(() => {
    // Prima notificare dupa 8s
    const firstTimer = setTimeout(() => {
      setCurrent(NOTIFICATIONS[0])
      setVisible(true)

      // Ascunde dupa 5s
      setTimeout(() => setVisible(false), 5000)
    }, 8000)

    // Urmatoarele notificari la fiecare 30s
    const interval = setInterval(() => {
      setIndex(prev => {
        const next = (prev + 1) % NOTIFICATIONS.length
        setCurrent(NOTIFICATIONS[next])
        setVisible(true)
        setTimeout(() => setVisible(false), 5000)
        return next
      })
    }, 30000)

    return () => {
      clearTimeout(firstTimer)
      clearInterval(interval)
    }
  }, [])

  if (!current) return null

  return (
    <div
      className={`fixed bottom-4 left-4 z-40 transition-all duration-500 ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'
      }`}
    >
      <div className="bg-white rounded-2xl shadow-xl border border-neutral-100 px-4 py-3 flex items-center gap-3 max-w-xs">
        <div className="w-10 h-10 bg-emerald-50 rounded-xl flex items-center justify-center shrink-0">
          <ShoppingBag className="w-5 h-5 text-emerald-600" />
        </div>
        <div>
          <p className="text-xs font-semibold text-neutral-900">{current.nume}</p>
          <p className="text-xs text-neutral-500">
            a economisit <strong className="text-emerald-600">{current.economie} RON</strong> la {current.magazin}
          </p>
        </div>
        <button
          onClick={() => setVisible(false)}
          className="text-neutral-300 hover:text-neutral-500 ml-1 shrink-0"
          aria-label="Inchide"
        >
          ×
        </button>
      </div>
    </div>
  )
}
