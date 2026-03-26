import Link from 'next/link'
import { Home, Search } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="max-w-lg mx-auto px-4 py-24 text-center">
      <div className="text-8xl font-display font-extrabold text-neutral-200 mb-4">404</div>
      <h1 className="font-display font-bold text-2xl text-neutral-900 mb-3">
        Pagina nu a fost găsită
      </h1>
      <p className="text-neutral-500 mb-8">
        Oferta pe care o cauți poate a expirat sau pagina a fost mutată.
        Hai să găsim altceva bun!
      </p>
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <Link href="/" className="btn-cta">
          <Home className="w-4 h-4" />
          Înapoi la reduceri
        </Link>
        <Link href="/#magazine" className="btn-cta-outline">
          <Search className="w-4 h-4" />
          Caută magazine
        </Link>
      </div>
    </div>
  )
}
