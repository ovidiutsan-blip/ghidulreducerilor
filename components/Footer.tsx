import Link from 'next/link'
import { Tag } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-neutral-900 text-neutral-300 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-brand-red rounded-lg flex items-center justify-center">
                <Tag className="w-4 h-4 text-white" />
              </div>
              <span className="font-display font-bold text-white">
                GhidulReducerilor
              </span>
            </div>
            <p className="text-sm text-neutral-400 leading-relaxed">
              Cele mai bune reduceri și coduri promoționale din România, verificate zilnic.
            </p>
          </div>

          {/* Magazine */}
          <div>
            <h3 className="font-display font-semibold text-white text-sm uppercase tracking-wider mb-4">Magazine</h3>
            <ul className="space-y-2">
              <li><Link href="/reduceri/emag" className="text-sm hover:text-white transition-colors">Reduceri eMAG</Link></li>
              <li><Link href="/reduceri/altex" className="text-sm hover:text-white transition-colors">Reduceri Altex</Link></li>
              <li><Link href="/reduceri/fashion-days" className="text-sm hover:text-white transition-colors">Reduceri Fashion Days</Link></li>
            </ul>
          </div>

          {/* Coduri Promo */}
          <div>
            <h3 className="font-display font-semibold text-white text-sm uppercase tracking-wider mb-4">Coduri Promo</h3>
            <ul className="space-y-2">
              <li><Link href="/coduri-promo/emag" className="text-sm hover:text-white transition-colors">Coduri eMAG</Link></li>
              <li><Link href="/coduri-promo/altex" className="text-sm hover:text-white transition-colors">Coduri Altex</Link></li>
              <li><Link href="/coduri-promo/fashion-days" className="text-sm hover:text-white transition-colors">Coduri Fashion Days</Link></li>
            </ul>
          </div>

          {/* Informații */}
          <div>
            <h3 className="font-display font-semibold text-white text-sm uppercase tracking-wider mb-4">Informații</h3>
            <ul className="space-y-2">
              <li><Link href="/despre" className="text-sm hover:text-white transition-colors">Despre noi</Link></li>
              <li><Link href="/abonare-alerte" className="text-sm hover:text-white transition-colors">Alerte Reduceri</Link></li>
              <li><Link href="/despre#confidentialitate" className="text-sm hover:text-white transition-colors">Politica de confidențialitate</Link></li>
            </ul>
          </div>
        </div>

        {/* Disclaimer afiliere + Copyright */}
        <div className="border-t border-neutral-700 mt-10 pt-8">
          <p className="text-xs text-neutral-500 leading-relaxed mb-4">
            <strong className="text-neutral-400">Disclaimer afiliere:</strong> Acest site conține linkuri de afiliere prin rețeaua Profitshare.ro.
            Când cumperi prin aceste linkuri, primim un comision fără costuri suplimentare pentru tine.
            Acest lucru ne ajută să menținem site-ul actualizat cu cele mai bune oferte.
          </p>
          <p className="text-xs text-neutral-500">
            © {new Date().getFullYear()} GhidulReducerilor.ro — Toate drepturile rezervate.
          </p>
        </div>
      </div>
    </footer>
  )
}
