'use client'

import { useState, useRef, useEffect } from 'react'
import Image from 'next/image'
import { Search, X } from 'lucide-react'
import { formatPrice } from '@/lib/utils'
import type { SearchResult } from '@/app/api/search/route'

const DEBOUNCE_MS = 250

export default function SearchBar() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [open, setOpen] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const q = query.trim()
    if (q.length < 2) {
      setResults([])
      return
    }

    const ctrl = new AbortController()
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`, {
          signal: ctrl.signal,
        })
        if (!res.ok) return
        const data = (await res.json()) as { results: SearchResult[] }
        setResults(data.results)
      } catch {
        // AbortError sau retea — ignoră
      }
    }, DEBOUNCE_MS)

    return () => {
      clearTimeout(timer)
      ctrl.abort()
    }
  }, [query])

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  useEffect(() => {
    setOpen(results.length > 0)
  }, [results])

  function handleFocus() {
    if (query.length >= 2 && results.length > 0) setOpen(true)
  }

  return (
    <>
      {/* Desktop search */}
      <div ref={ref} className="hidden md:block relative flex-1 max-w-md mx-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onFocus={handleFocus}
            placeholder="Cauta reduceri..."
            className="w-full pl-10 pr-4 py-2 text-sm border border-neutral-200 rounded-xl bg-neutral-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red/20 focus:border-brand-red transition-all"
          />
          {query && (
            <button onClick={() => { setQuery(''); setOpen(false) }} className="absolute right-3 top-1/2 -translate-y-1/2">
              <X className="w-4 h-4 text-neutral-400 hover:text-neutral-600" />
            </button>
          )}
        </div>

        {open && results.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl border border-neutral-200 shadow-lg overflow-hidden z-50">
            {results.map(deal => (
              <a
                key={deal.id}
                href={`/out/${deal.id}`}
                target="_blank"
                rel="noopener noreferrer nofollow"
                className="flex items-center gap-3 px-4 py-3 hover:bg-neutral-50 transition-colors"
                onClick={() => setOpen(false)}
              >
                <div className="w-10 h-10 rounded-lg bg-neutral-100 overflow-hidden shrink-0 relative">
                  <Image
                    src={deal.imagine_url}
                    alt={deal.titlu}
                    fill
                    className="object-cover"
                    sizes="40px"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-neutral-900 truncate">{deal.titlu}</p>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-brand-red">{formatPrice(deal.pret_redus)}</span>
                    <span className="text-xs text-neutral-400 line-through">{formatPrice(deal.pret_original)}</span>
                    <span className="text-xs font-semibold text-white bg-brand-red px-1.5 py-0.5 rounded">-{deal.procent_reducere}%</span>
                  </div>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>

      {/* Mobile search icon + overlay */}
      <button
        onClick={() => { setMobileOpen(true); setTimeout(() => inputRef.current?.focus(), 100) }}
        className="md:hidden p-2 text-neutral-600 hover:text-neutral-900"
        aria-label="Cauta"
      >
        <Search className="w-5 h-5" />
      </button>

      {mobileOpen && (
        <div className="fixed inset-0 z-[60] bg-white md:hidden">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-neutral-200">
            <Search className="w-5 h-5 text-neutral-400 shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Cauta reduceri..."
              className="flex-1 text-base outline-none"
            />
            <button onClick={() => { setMobileOpen(false); setQuery('') }}>
              <X className="w-5 h-5 text-neutral-600" />
            </button>
          </div>
          <div className="overflow-y-auto max-h-[calc(100vh-60px)]">
            {results.map(deal => (
              <a
                key={deal.id}
                href={`/out/${deal.id}`}
                target="_blank"
                rel="noopener noreferrer nofollow"
                className="flex items-center gap-3 px-4 py-3 border-b border-neutral-100"
                onClick={() => setMobileOpen(false)}
              >
                <div className="w-12 h-12 rounded-lg bg-neutral-100 overflow-hidden shrink-0 relative">
                  <Image
                    src={deal.imagine_url}
                    alt={deal.titlu}
                    fill
                    className="object-cover"
                    sizes="48px"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-neutral-900 line-clamp-1">{deal.titlu}</p>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-brand-red">{formatPrice(deal.pret_redus)}</span>
                    <span className="text-xs text-neutral-400 line-through">{formatPrice(deal.pret_original)}</span>
                    <span className="text-xs font-semibold text-white bg-brand-red px-1.5 py-0.5 rounded">-{deal.procent_reducere}%</span>
                  </div>
                </div>
              </a>
            ))}
            {query.length >= 2 && results.length === 0 && (
              <p className="text-center text-neutral-400 py-8">Nicio oferta gasita pentru &ldquo;{query}&rdquo;</p>
            )}
          </div>
        </div>
      )}
    </>
  )
}
