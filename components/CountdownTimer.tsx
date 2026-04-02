'use client'

import { useEffect, useState } from 'react'
import { Zap } from 'lucide-react'

function getSecondsUntilMidnight() {
  const now = new Date()
  const midnight = new Date()
  midnight.setHours(24, 0, 0, 0)
  return Math.floor((midnight.getTime() - now.getTime()) / 1000)
}

function formatTime(seconds: number) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return {
    h: String(h).padStart(2, '0'),
    m: String(m).padStart(2, '0'),
    s: String(s).padStart(2, '0'),
  }
}

export default function CountdownTimer() {
  const [seconds, setSeconds] = useState<number | null>(null)

  useEffect(() => {
    setSeconds(getSecondsUntilMidnight())
    const interval = setInterval(() => {
      setSeconds(getSecondsUntilMidnight())
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  if (seconds === null) return null

  const { h, m, s } = formatTime(seconds)

  return (
    <div className="flex items-center gap-2 bg-neutral-800/60 rounded-xl px-4 py-2 border border-neutral-700">
      <Zap className="w-4 h-4 text-amber-400 shrink-0" />
      <span className="text-sm text-neutral-300">Ofertele expiră în:</span>
      <div className="flex items-center gap-1 font-mono font-bold text-white">
        <span className="bg-neutral-700 px-2 py-0.5 rounded">{h}</span>
        <span className="text-neutral-400">:</span>
        <span className="bg-neutral-700 px-2 py-0.5 rounded">{m}</span>
        <span className="text-neutral-400">:</span>
        <span className="bg-neutral-700 px-2 py-0.5 rounded">{s}</span>
      </div>
    </div>
  )
}
