'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Grid3X3, Tag, Bell } from 'lucide-react'

const TABS = [
  { href: '/', label: 'Acasa', icon: Home },
  { href: '/categorii', label: 'Categorii', icon: Grid3X3 },
  { href: '/#reduceri', label: 'Oferte', icon: Tag },
  { href: '/abonare-alerte', label: 'Alerte', icon: Bell },
]

export default function MobileBottomNav() {
  const pathname = usePathname()

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-neutral-200 safe-area-bottom">
      <div className="flex items-center justify-around py-2">
        {TABS.map(tab => {
          const Icon = tab.icon
          const isActive = tab.href === '/' ? pathname === '/' : pathname.startsWith(tab.href)
          return (
            <Link
              key={tab.label}
              href={tab.href}
              className={`flex flex-col items-center gap-0.5 px-3 py-1 ${
                isActive ? 'text-brand-red' : 'text-neutral-400'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] font-medium">{tab.label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
