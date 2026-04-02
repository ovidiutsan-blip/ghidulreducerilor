'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Tag, Menu, X, Bell, ChevronDown } from 'lucide-react'

const MAGAZINE_DESKTOP = [
  { href: '/reduceri/emag', label: 'eMAG' },
  { href: '/reduceri/notino', label: 'Notino' },
  { href: '/reduceri/fashion-days', label: 'Fashion Days' },
  { href: '/reduceri/catena', label: 'Catena' },
  { href: '/reduceri/decathlon', label: 'Decathlon' },
]

const MAGAZINE_MOBILE = [
  { href: '/reduceri/emag', emoji: '🛒', label: 'eMAG' },
  { href: '/reduceri/notino', emoji: '🌸', label: 'Notino' },
  { href: '/reduceri/fashion-days', emoji: '👗', label: 'Fashion Days' },
  { href: '/reduceri/answear', emoji: '👟', label: 'Answear' },
  { href: '/reduceri/catena', emoji: '💊', label: 'Catena' },
  { href: '/reduceri/decathlon', emoji: '🏃', label: 'Decathlon' },
  { href: '/reduceri/vexio', emoji: '💻', label: 'Vexio' },
  { href: '/reduceri/cel', emoji: '📱', label: 'Cel.ro' },
  { href: '/reduceri/pcgarage', emoji: '🎮', label: 'PC Garage' },
  { href: '/reduceri/libris', emoji: '📚', label: 'Libris' },
  { href: '/reduceri/forit', emoji: '🖥️', label: 'ForIT' },
  { href: '/reduceri/fornello', emoji: '🔥', label: 'Fornello' },
]

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-neutral-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 bg-brand-red rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform">
              <Tag className="w-5 h-5 text-white" />
            </div>
            <span className="font-display font-bold text-lg text-neutral-900">
              Ghidul<span className="text-brand-red">Reducerilor</span>
            </span>
          </Link>

          {/* Navigare desktop */}
          <div className="hidden md:flex items-center gap-5">
            {MAGAZINE_DESKTOP.map(({ href, label }) => (
              <Link key={href} href={href} className="text-sm font-medium text-neutral-600 hover:text-brand-red transition-colors">
                {label}
              </Link>
            ))}
            <Link href="/#magazine" className="text-sm font-medium text-neutral-400 hover:text-brand-red transition-colors flex items-center gap-0.5">
              Mai multe <ChevronDown className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* CTA + Mobile menu */}
          <div className="flex items-center gap-3">
            <Link
              href="/abonare-alerte"
              className="hidden sm:inline-flex items-center gap-2 bg-brand-red hover:bg-brand-red-dark text-white text-sm font-semibold px-4 py-2 rounded-xl transition-all"
            >
              <Bell className="w-4 h-4" />
              Alerte Reduceri
            </Link>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="md:hidden p-2 text-neutral-600 hover:text-neutral-900"
              aria-label="Meniu"
            >
              {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Meniu mobil */}
      {menuOpen && (
        <div className="md:hidden border-t border-neutral-200 bg-white">
          <div className="px-4 py-4">
            <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-3">Magazine</p>
            <div className="grid grid-cols-2 gap-2 mb-4">
              {MAGAZINE_MOBILE.map(({ href, emoji, label }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-2 text-sm font-medium text-neutral-700 hover:text-brand-red py-1"
                  onClick={() => setMenuOpen(false)}
                >
                  <span>{emoji}</span> {label}
                </Link>
              ))}
            </div>
            <hr className="border-neutral-200 mb-4" />
            <Link
              href="/abonare-alerte"
              className="btn-cta w-full text-sm"
              onClick={() => setMenuOpen(false)}
            >
              <Bell className="w-4 h-4" />
              Alerte Reduceri
            </Link>
          </div>
        </div>
      )}
    </nav>
  )
}
