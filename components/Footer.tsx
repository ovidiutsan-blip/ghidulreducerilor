import Link from 'next/link'
import { Tag } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-neutral-900 text-neutral-300 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-brand-red rounded-lg flex items-center justify-center">
                <Tag className="w-4 h-4 text-white" />
              </div>
              <span className="font-display font-bold text-white">GhidulReducerilor</span>
            </div>
            <p className="text-sm text-neutral-400 leading-relaxed mb-4">
              Cele mai bune reduceri si coduri promotionale din Romania, verificate zilnic.
            </p>
            <p className="text-xs text-neutral-500">
              <a href="https://www.tiktok.com/@catalinovidiu" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
                📱 TikTok: @catalinovidiu
              </a>
            </p>
          </div>

          {/* Magazine */}
          <div>
            <h3 className="font-display font-semibold text-white text-sm uppercase tracking-wider mb-4">Magazine</h3>
            <ul className="space-y-2">
              <li><Link href="/reduceri/emag" className="text-sm hover:text-white transition-colors">Reduceri eMAG</Link></li>
              <li><Link href="/reduceri/notino" className="text-sm hover:text-white transition-colors">Reduceri Notino</Link></li>
              <li><Link href="/reduceri/fashion-days" className="text-sm hover:text-white transition-colors">Reduceri Fashion Days</Link></li>
              <li><Link href="/reduceri/answear" className="text-sm hover:text-white transition-colors">Reduceri Answear</Link></li>
              <li><Link href="/reduceri/catena" className="text-sm hover:text-white transition-colors">Reduceri Catena</Link></li>
              <li><Link href="/reduceri/decathlon" className="text-sm hover:text-white transition-colors">Reduceri Decathlon</Link></li>
              <li><Link href="/reduceri/cel" className="text-sm hover:text-white transition-colors">Reduceri Cel.ro</Link></li>
              <li><Link href="/reduceri/pcgarage" className="text-sm hover:text-white transition-colors">Reduceri PC Garage</Link></li>
            </ul>
          </div>

          {/* Coduri Promo */}
          <div>
            <h3 className="font-display font-semibold text-white text-sm uppercase tracking-wider mb-4">Coduri Promo</h3>
            <ul className="space-y-2">
              <li><Link href="/coduri-promo/emag" className="text-sm hover:text-white transition-colors">Coduri eMAG</Link></li>
              <li><Link href="/coduri-promo/notino" className="text-sm hover:text-white transition-colors">Coduri Notino</Link></li>
              <li><Link href="/coduri-promo/fashion-days" className="text-sm hover:text-white transition-colors">Coduri Fashion Days</Link></li>
              <li><Link href="/coduri-promo/answear" className="text-sm hover:text-white transition-colors">Coduri Answear</Link></li>
              <li><Link href="/coduri-promo/catena" className="text-sm hover:text-white transition-colors">Coduri Catena</Link></li>
              <li><Link href="/coduri-promo/decathlon" className="text-sm hover:text-white transition-colors">Coduri Decathlon</Link></li>
              <li><Link href="/coduri-promo/libris" className="text-sm hover:text-white transition-colors">Coduri Libris</Link></li>
            </ul>
          </div>

          {/* Informatii */}
          <div>
            <h3 className="font-display font-semibold text-white text-sm uppercase tracking-wider mb-4">Informatii</h3>
            <ul className="space-y-2">
              <li><Link href="/despre" className="text-sm hover:text-white transition-colors">Despre noi</Link></li>
              <li><Link href="/abonare-alerte" className="text-sm hover:text-white transition-colors">Alerte Reduceri</Link></li>
              <li><Link href="/despre#confidentialitate" className="text-sm hover:text-white transition-colors">Confidentialitate</Link></li>
              <li><Link href="/reduceri/vexio" className="text-sm hover:text-white transition-colors">Reduceri Vexio</Link></li>
              <li><Link href="/reduceri/libris" className="text-sm hover:text-white transition-colors">Reduceri Libris</Link></li>
            </ul>
          </div>
        </div>

        {/* Disclaimer + Copyright */}
        <div className="border-t border-neutral-700 mt-10 pt-8">
          <p className="text-xs text-neutral-500 leading-relaxed mb-3">
            <strong className="text-neutral-400">⚠️ Disclaimer afiliere:</strong>{' '}
            GhidulReducerilor.ro contine linkuri de afiliere prin reteaua{' '}
            <a href="https://www.profitshare.ro" target="_blank" rel="noopener noreferrer" className="hover:text-neutral-300 underline">Profitshare.ro</a>.
            Cand cumperi prin aceste linkuri, primim un comision fara costuri suplimentare pentru tine.
            Preturile si disponibilitatea sunt actualizate zilnic dar pot diferi fata de cele din magazin.
          </p>
          <p className="text-xs text-neutral-500">
            © {new Date().getFullYear()} GhidulReducerilor.ro — Toate drepturile rezervate.
          </p>
        </div>
      </div>
    </footer>
  )
}
