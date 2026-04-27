/**
 * /api/merchant-feed — Google Merchant Center product feed (TSV)
 * URL: https://ghidulreducerilor.ro/api/merchant-feed
 *
 * Câmpuri obligatorii GMC: id, title, description, link, image_link,
 *   availability, price, condition
 * Câmpuri recomandate: sale_price, brand, google_product_category
 *
 * Submitere în GMC: Merchant Center → Products → Feeds → Add feed → TSV
 */

import { getActiveDeals } from '@/lib/data'

const SITE = 'https://ghidulreducerilor.ro'

// Mapare categorii interne → Google Product Category (taxonomy string)
// https://www.google.com/basepages/producttype/taxonomy-with-ids.ro-RO.txt
const CATEGORY_MAP: Record<string, string> = {
  // Fashion & Accesorii
  'ceasuri':        'Haine și accesorii > Bijuterii > Ceasuri',
  'bijuterii':      'Haine și accesorii > Bijuterii',
  'moda':           'Haine și accesorii',
  'haine':          'Haine și accesorii > Îmbrăcăminte',
  'incaltaminte':   'Haine și accesorii > Pantofi',
  'genti':          'Haine și accesorii > Genți, portofele și accesorii',
  'fashion':        'Haine și accesorii',
  // Beauty & Sănătate
  'cosmetice':      'Sănătate și frumusețe > Frumusețe personală',
  'parfumuri':      'Sănătate și frumusețe > Frumusețe personală > Parfumuri',
  'ingrijire':      'Sănătate și frumusețe > Îngrijire personală',
  'beauty':         'Sănătate și frumusețe > Frumusețe personală',
  'sanatate':       'Sănătate și frumusețe > Îngrijire medicală',
  'farmacie':       'Sănătate și frumusețe > Îngrijire medicală',
  'suplimente':     'Sănătate și frumusețe > Îngrijire medicală > Vitamine și suplimente',
  'nutritie':       'Alimente și băuturi',
  'sport-nutritie': 'Sănătate și frumusețe > Îngrijire medicală > Vitamine și suplimente',
  // Electronics
  'electronice':    'Electronice',
  'telefoane':      'Electronice > Comunicații > Telefoane',
  'laptopuri':      'Electronice > Calculatoare > Laptopuri',
  'tablete':        'Electronice > Calculatoare > Tablete',
  'audio':          'Electronice > Audio',
  'tv':             'Electronice > Video > Televizoare',
  'gaming':         'Electronice > Video > Jocuri video',
  'software':       'Software',
  // Casă & Grădină
  'casa':           'Locuință și grădină',
  'mobila':         'Locuință și grădină > Mobilier',
  'gradina':        'Locuință și grădină > Grădinarit',
  'electrocasnice': 'Locuință și grădină > Aparate electrocasnice',
  'bucatarie':      'Locuință și grădină > Bucătărie și sufragerie',
  'curatenie':      'Locuință și grădină > Menaj',
  'iluminat':       'Locuință și grădină > Iluminat',
  'climatizare':    'Locuință și grădină > Aparate electrocasnice > Aparate de climatizare',
  // Cărți & Educație
  'carti':          'Medii > Cărți',
  'educatie':       'Medii > Cărți',
  // Sport
  'sport':          'Articole sportive',
  'fitness':        'Articole sportive > Echipament de fitness',
  'outdoor':        'Articole sportive > Sport în aer liber',
  // Altele
  'auto':           'Vehicule și piese',
  'copii':          'Jucării și jocuri',
  'jucarii':        'Jucării și jocuri',
  'animale':        'Animale de companie',
}

function getGoogleCategory(categorie: string): string {
  const key = categorie.toLowerCase().trim()
  return CATEGORY_MAP[key] ?? 'Alte categorii'
}

// Sanitizare câmpuri TSV — elimină tab-uri și newline-uri
function tsv(val: string | number | undefined | null): string {
  if (val === null || val === undefined) return ''
  return String(val).replace(/[\t\n\r]/g, ' ').trim()
}

// Format preț GMC: "25.00 RON"
function fmtPrice(val: number): string {
  return `${val.toFixed(2)} RON`
}

export async function GET() {
  const deals = getActiveDeals()

  // Header TSV — câmpuri GMC standard
  const headers = [
    'id',
    'title',
    'description',
    'link',
    'image_link',
    'availability',
    'price',
    'sale_price',
    'condition',
    'brand',
    'google_product_category',
  ]

  const rows: string[] = [headers.join('\t')]

  for (const deal of deals) {
    // Skip deal-uri fără imagine sau titlu
    if (!deal.imagine_url || !deal.titlu) continue

    const productLink = `${SITE}/out/${deal.id}`
    const brand = deal.magazin.toUpperCase()

    // price = prețul original (GMC vrea prețul de bază)
    // sale_price = prețul redus
    const price = deal.pret_original > 0 ? deal.pret_original : deal.pret_redus
    const salePrice = deal.pret_redus

    const description = [
      `Reducere ${deal.procent_reducere}% la ${tsv(deal.titlu)}.`,
      `Preț original: ${fmtPrice(deal.pret_original)},`,
      `preț redus: ${fmtPrice(deal.pret_redus)}.`,
      `Disponibil pe ${brand}.`,
    ].join(' ')

    const row = [
      tsv(deal.id),
      tsv(deal.titlu),
      tsv(description),
      tsv(productLink),
      tsv(deal.imagine_url),
      'in stock',
      fmtPrice(price),
      fmtPrice(salePrice),
      'new',
      tsv(brand),
      tsv(getGoogleCategory(deal.categorie)),
    ]

    rows.push(row.join('\t'))
  }

  const body = rows.join('\n')

  return new Response(body, {
    headers: {
      'Content-Type': 'text/tab-separated-values; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, s-maxage=3600',
      'Content-Disposition': 'attachment; filename="merchant-feed.tsv"',
    },
  })
}
