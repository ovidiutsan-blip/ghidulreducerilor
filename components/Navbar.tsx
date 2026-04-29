'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Tag, Menu, X, Bell } from 'lucide-react'
import SearchBar from '@/components/SearchBar'

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <nav className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-neutral-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group shrink-0">
            <div className="w-9 h-9 bg-brand-red rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform">
              <Tag className="w-5 h-5 text-white" />
            </div>
            <span className="font-display font-bold text-lg text-neutral-900">
              Ghidul<span className="text-brand-red">Reducerilor</span>
            </span>
          </Link>

          {/* Search bar - desktop */}
          <SearchBar />

          {/* CTA + Mobile menu */}
          <div className="flex items-center gap-2">
            <Link
              href="/black-friday"
              className="hidden md:inline-flex items-center gap-1.5 bg-neutral-900 hover:bg-black text-white text-sm font-semibold px-3 py-2 rounded-xl transition-all"
            >
              🔥 Black Friday
            </Link>
            <Link
              href="/abonare-alerte"
              className="hidden sm:inline-flex items-center gap-2 bg-brand-red hover:bg-brand-red-dark text-white text-sm font-semibold px-4 py-2 rounded-xl transition-all"
            >
              <Bell className="w-4 h-4" />
              Alerte
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

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-neutral-200 bg-white">
          <div className="px-4 py-4 space-y-3">
            <Link
              href="/black-friday"
              className="flex items-center gap-2 text-sm font-semibold text-neutral-900 hover:text-brand-red py-1"
              onClick={() => setMenuOpen(false)}
            >
              🔥 Black Friday 2026
            </Link>
            <Link
              href="/reduceri/emag"
              className="flex items-center gap-2 text-sm font-medium text-neutral-700 hover:text-brand-red py-1"
              onClick={() => setMenuOpen(false)}
            >
              🛒 eMAG Reduceri
            </Link>
            <Link
              href="/categorii"
              className="flex items-center gap-2 text-sm font-medium text-neutral-700 hover:text-brand-red py-1"
              onClick={() => setMenuOpen(false)}
            >
              🗂️ Categorii
            </Link>
            <Link
              href="/ghiduri"
              className="flex items-center gap-2 text-sm font-medium text-neutral-700 hover:text-brand-red py-1"
              onClick={() => setMenuOpen(false)}
            >
              📖 Ghiduri magazine
            </Link>
            <Link
              href="/blog"
              className="flex items-center gap-2 text-sm font-medium text-neutral-700 hover:text-brand-red py-1"
              onClick={() => setMenuOpen(false)}
            >
              📝 Blog
            </Link>
            <hr className="border-neutral-200" />
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
