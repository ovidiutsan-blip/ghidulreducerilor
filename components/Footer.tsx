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

          {/* Categorii */}
          <div>
            <h3 className="font-display font-semibold text-white text-sm uppercase tracking-wider mb-4">Categorii</h3>
            <ul className="space-y-2">
              <li><Link href="/categorii/fashion" className="text-sm hover:text-white transition-colors">👗 Fashion</Link></li>
              <li><Link href="/categorii/beauty" className="text-sm hover:text-white transition-colors">💄 Beauty</Link></li>
              <li><Link href="/categorii/farmacie-sanatate" className="text-sm hover:text-white transition-colors">💊 Farmacie & Sănătate</Link></li>
              <li><Link href="/categorii/carti" className="text-sm hover:text-white transition-colors">📚 Cărți</Link></li>
              <li><Link href="/categorii/casa-gradina" className="text-sm hover:text-white transition-colors">🏠 Casă & Grădină</Link></li>
            </ul>
          </div>

          {/* Ghiduri magazine */}
          <div>
            <h3 className="font-display font-semibold text-white text-sm uppercase tracking-wider mb-4">Ghiduri magazine</h3>
            <ul className="space-y-2">
              <li><Link href="/ghiduri/notino" className="text-sm hover:text-white transition-colors">Ghid Notino</Link></li>
              <li><Link href="/ghiduri/answear" className="text-sm hover:text-white transition-colors">Ghid Answear</Link></li>
              <li><Link href="/ghiduri/drmax" className="text-sm hover:text-white transition-colors">Ghid Dr.Max</Link></li>
              <li><Link href="/ghiduri/fashiondays" className="text-sm hover:text-white transition-colors">Ghid Fashion Days</Link></li>
              <li><Link href="/ghiduri" className="text-sm hover:text-white transition-colors font-semibold">Toate ghidurile →</Link></li>
            </ul>
          </div>

          {/* Informatii */}
          <div>
            <h3 className="font-display font-semibold text-white text-sm uppercase tracking-wider mb-4">Informatii</h3>
            <ul className="space-y-2">
              <li><Link href="/blog" className="text-sm hover:text-white transition-colors">Blog & Articole</Link></li>
              <li><Link href="/categorii" className="text-sm hover:text-white transition-colors">Toate categoriile</Link></li>
              <li><Link href="/coduri-promo/emag" className="text-sm hover:text-white transition-colors">Coduri eMAG</Link></li>
              <li><Link href="/cum-functioneaza" className="text-sm hover:text-white transition-colors">Cum funcționează</Link></li>
              <li><Link href="/despre" className="text-sm hover:text-white transition-colors">Despre noi</Link></li>
              <li><Link href="/abonare-alerte" className="text-sm hover:text-white transition-colors">Alerte Reduceri</Link></li>
              <li><Link href="/despre#confidentialitate" className="text-sm hover:text-white transition-colors">Confidentialitate</Link></li>
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
