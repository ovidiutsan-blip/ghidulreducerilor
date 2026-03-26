import { Metadata } from 'next'
import { Bell } from 'lucide-react'
import EmailForm from '@/components/EmailForm'
import Breadcrumb from '@/components/Breadcrumb'

export const metadata: Metadata = {
  title: 'Alerte Reduceri — Primește oferte pe email',
  description: 'Abonează-te gratuit și primește alertă când apar reduceri mari la magazinele tale preferate. Fără spam, doar oferte bune.',
  alternates: { canonical: '/abonare-alerte' },
}

export default function AlertePage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Breadcrumb items={[{ label: 'Alerte Reduceri' }]} />

      <div className="text-center mb-10">
        <div className="w-16 h-16 bg-brand-red/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Bell className="w-8 h-8 text-brand-red" />
        </div>
        <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-neutral-900 mb-3">
          Alerte Reduceri pe Email
        </h1>
        <p className="text-neutral-600 max-w-lg mx-auto">
          Completează formularul și vei primi un email când apare o reducere importantă
          la magazinul tău preferat. Gratuit, fără spam — te poți dezabona oricând.
        </p>
      </div>

      <div className="card-hover p-8">
        <EmailForm />
      </div>

      {/* Beneficii */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mt-12">
        <div className="text-center">
          <div className="text-3xl mb-2">🎯</div>
          <h3 className="font-display font-semibold text-neutral-900 mb-1">Personalizat</h3>
          <p className="text-sm text-neutral-500">Primești alerte doar de la magazinele care te interesează</p>
        </div>
        <div className="text-center">
          <div className="text-3xl mb-2">⚡</div>
          <h3 className="font-display font-semibold text-neutral-900 mb-1">Rapid</h3>
          <p className="text-sm text-neutral-500">Ești notificat primul când apare o reducere mare</p>
        </div>
        <div className="text-center">
          <div className="text-3xl mb-2">🔒</div>
          <h3 className="font-display font-semibold text-neutral-900 mb-1">Fără spam</h3>
          <p className="text-sm text-neutral-500">Maxim 2-3 email-uri pe săptămână, doar oferte verificate</p>
        </div>
      </div>
    </div>
  )
}
