import { Metadata } from 'next'
import Link from 'next/link'
import { getAllStores } from '@/lib/data'
import { getCurrentMonthYear } from '@/lib/utils'

export const metadata: Metadata = {
  title: 'Cod Reducere Magazine Online România – Cupoane & Voucher Active',
  description:
    'Coduri de reducere și cupoane promoționale pentru cele mai mari magazine online din România. Verificate zilnic — emag, FashionDays, Notino, Libris și multe altele.',
  alternates: { canonical: '/cod-reducere' },
  robots: { index: true, follow: true },
}

export default function CodReducereIndexPage() {
  const stores = getAllStores()
  const monthYear = getCurrentMonthYear()

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero */}
      <div className="text-center mb-10">
        <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-neutral-900 mb-3">
          Coduri Reducere Magazine Online
        </h1>
        <p className="text-neutral-500 text-lg max-w-2xl mx-auto">
          Cupoane și voucher-e verificate zilnic pentru {stores.length} magazine din România – {monthYear}
        </p>
      </div>

      {/* Grid magazine */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 mb-12">
        {stores.map(store => (
          <Link
            key={store.slug}
            href={`/cod-reducere/${store.slug}`}
            className="flex items-center gap-3 bg-white border border-neutral-200 rounded-xl p-4 hover:border-brand-red hover:shadow-md transition-all group"
          >
            <span className="text-2xl shrink-0">{store.logo_emoji}</span>
            <div>
              <p className="font-semibold text-neutral-900 text-sm group-hover:text-brand-red transition-colors">
                {store.nume}
              </p>
              <p className="text-xs text-neutral-400">cod reducere →</p>
            </div>
          </Link>
        ))}
      </div>

      {/* Explicatie */}
      <section className="bg-neutral-50 rounded-2xl p-6 sm:p-8">
        <h2 className="font-display font-bold text-xl text-neutral-900 mb-3">
          Ce este un cod de reducere?
        </h2>
        <p className="text-neutral-600 leading-relaxed mb-4">
          Un cod de reducere (sau cod promoțional / voucher) este un șir de litere și cifre pe
          care îl introduci la checkout pentru a primi o reducere. Poate fi un procent din total
          (ex: 10% reducere), o sumă fixă (ex: 20 lei reducere) sau transport gratuit.
        </p>
        <p className="text-neutral-600 leading-relaxed">
          Pe GhidulReducerilor.ro verificăm zilnic codurile active de la {stores.length} magazine
          și le afișăm gratuit. Dacă un cod nu mai e valabil, îl eliminăm imediat.
        </p>
      </section>
    </div>
  )
}
