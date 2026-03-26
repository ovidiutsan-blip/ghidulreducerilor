import deals from '@/data/deals.json'
import codes from '@/data/codes.json'
import stores from '@/data/stores.json'

export type Deal = {
  id: string
  magazin: string
  titlu: string
  imagine_url: string
  pret_original: number
  pret_redus: number
  procent_reducere: number
  link_afiliat: string
  categorie: string
  data_adaugare: string
  activ: boolean
}

export type PromoCode = {
  id: string
  magazin: string
  cod: string
  descriere: string
  valoare: string
  tip: string
  data_expirare: string
  link_afiliat: string
  verificat: boolean
}

export type Store = {
  id: string
  nume: string
  slug: string
  descriere: string
  logo_emoji: string
  culoare: string
  categorie_principala: string
  url_site: string
  comision_mediu: string
}

// Returnează toate ofertele active
export function getActiveDeals(): Deal[] {
  return (deals as Deal[]).filter(d => d.activ)
}

// Returnează ofertele pentru un magazin specific
export function getDealsByStore(storeSlug: string): Deal[] {
  return (deals as Deal[]).filter(d => d.magazin === storeSlug && d.activ)
}

// Returnează codurile promoționale pentru un magazin
export function getCodesByStore(storeSlug: string): PromoCode[] {
  return (codes as PromoCode[]).filter(c => c.magazin === storeSlug)
}

// Returnează toate magazinele
export function getAllStores(): Store[] {
  return stores as Store[]
}

// Returnează un magazin după slug
export function getStoreBySlug(slug: string): Store | undefined {
  return (stores as Store[]).find(s => s.slug === slug)
}

// Returnează toate slug-urile de magazine (pentru generateStaticParams)
export function getAllStoreSlugs(): string[] {
  return (stores as Store[]).map(s => s.slug)
}
