import deals from '@/data/deals.json'
import stores from '@/data/stores.json'

export type Deal = {
  id: string
  slug?: string
  magazin: string
  titlu: string
  imagine_url: string
  pret_original: number
  pret_redus: number
  procent_reducere: number
  link_afiliat: string
  product_url?: string
  categorie: string
  data_adaugare: string
  activ: boolean
}

export type Store = {
  id: string
  nume: string
  slug: string
  descriere: string
  logo_emoji: string
  logo_url?: string
  culoare: string
  categorie_principala: string
  url_site: string
  comision_mediu: string
  retea?: 'profitshare' | '2performant'
}

// Defensiv: filtrează deal-uri "garbage" cu prețuri parsate greșit.
// Pattern observat: scraperul evomag pune pret_redus=99 (placeholder)
// + pret_original scalat x100 (ex: 63999 = ar trebui 639.99) când există <sup>
// pentru bani fără separator. Reduce procent_reducere la 99-100% suspect.
function isLegitDeal(d: Deal): boolean {
  // pret_redus < 5 RON e clearly garbage (sub minimul realist pentru orice produs reduceri)
  if (d.pret_redus < 5) return false
  // pret_redus exact 99 + reducere mare = placeholder evomag "Stoc epuizat"
  // (pretul original e parsat gresit din <sup>XX</sup>, scaled x100)
  if (d.pret_redus <= 99 && d.procent_reducere >= 95) return false
  return true
}

// Returnează toate ofertele active
export function getActiveDeals(): Deal[] {
  return (deals as Deal[]).filter(d => d.activ && isLegitDeal(d))
}

// Returnează ofertele pentru un magazin specific
export function getDealsByStore(storeSlug: string): Deal[] {
  return (deals as Deal[])
    .filter(d => d.magazin === storeSlug && d.activ && isLegitDeal(d))
    .sort(byDiscountImageFirst)
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

// Returnează lista unică de magazine din deals (pentru filtrare)
export function getUniqueMagazine(): string[] {
  const magazineSet = new Set((deals as Deal[]).filter(d => d.activ).map(d => d.magazin))
  return Array.from(magazineSet).sort()
}

// Caută un deal după slug
export function getDealBySlug(slug: string): Deal | undefined {
  return (deals as Deal[]).find(d => d.slug === slug)
}

// Returnează deals filtrate pe categorie
export function getDealsByCategory(category: string): Deal[] {
  return (deals as Deal[]).filter(d => d.categorie === category && d.activ)
}

// Returnează toate categoriile unice din deals active
export function getAllCategories(): string[] {
  const catSet = new Set((deals as Deal[]).filter(d => d.activ).map(d => d.categorie))
  return Array.from(catSet).sort()
}

// Comparator: discount descrescător, dar deal-urile FĂRĂ imagine coboară
// sub cele cu imagine — cardurile fallback (gri) nu trebuie să ocupe
// sloturile de top ale site-ului (unele feed-uri livrează imagini moarte
// pe care pipeline-ul nu le poate repara, ex. magazine cu bot-protection).
export function byDiscountImageFirst(a: Deal, b: Deal): number {
  const img = Number(Boolean(b.imagine_url)) - Number(Boolean(a.imagine_url))
  if (img !== 0) return img
  return (b.procent_reducere ?? 0) - (a.procent_reducere ?? 0)
}

// Returnează "deal of the day" — cel mai mare discount, rotatie zilnica
export function getDealOfTheDay(): Deal {
  const active = getActiveDeals()
  const today = new Date()
  const dayIndex = today.getFullYear() * 366 + today.getMonth() * 31 + today.getDate()
  // Sorteaza dupa discount descrescator, apoi rotatie pe baza zilei
  const sorted = [...active].sort(byDiscountImageFirst)
  const topDeals = sorted.slice(0, 10)
  return topDeals[dayIndex % topDeals.length]
}

// Returnează top N deals dupa discount (pt flash deals).
// Max 2 per magazin — altfel un feed cu discounturi mari aproape identice
// (ex. 7 lenjerii de la același magazin) monopolizează toată secțiunea.
export function getFlashDeals(count: number = 8): Deal[] {
  const sorted = [...getActiveDeals()].sort(byDiscountImageFirst)
  const perStore: Record<string, number> = {}
  const picked: Deal[] = []
  for (const d of sorted) {
    if ((perStore[d.magazin] || 0) >= 2) continue
    perStore[d.magazin] = (perStore[d.magazin] || 0) + 1
    picked.push(d)
    if (picked.length === count) break
  }
  return picked
}

// Magazine care au cel puțin un deal activ, cu numărul de oferte,
// sortate descrescător — sursa pentru homepage/footer, ca listele să nu
// mai promoveze magazine goale când un feed dispare.
export function getStoresWithDealCounts(): Array<Store & { dealCount: number }> {
  const counts: Record<string, number> = {}
  for (const d of getActiveDeals()) {
    counts[d.magazin] = (counts[d.magazin] || 0) + 1
  }
  return (stores as Store[])
    .map(s => ({ ...s, dealCount: counts[s.slug] || 0 }))
    .filter(s => s.dealCount > 0)
    .sort((a, b) => b.dealCount - a.dealCount)
}

// Versiune pentru props către componente client: link_afiliat/product_url nu
// sunt folosite în UI (click-ul trece prin /out/{id}), dar umflă payload-ul
// RSC serializat în HTML cu sute de KB la liste mari.
export function stripDealsForClient(list: Deal[]): Deal[] {
  return list.map(({ link_afiliat: _l, product_url: _p, slug: _s, ...rest }) => ({
    ...rest,
    link_afiliat: '',
  }))
}

// Returnează info magazin pentru un deal
export function getStoreForDeal(deal: Deal): Store | undefined {
  return (stores as Store[]).find(s => s.slug === deal.magazin)
}
