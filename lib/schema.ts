/**
 * lib/schema.ts — Funcții pentru generarea JSON-LD schema (schema.org)
 * Folosite pe paginile /reduceri/[magazin], /categorie/[slug], /deals etc.
 */

const SITE = 'https://ghidulreducerilor.ro'

export interface DealForSchema {
  id: string
  titlu?: string
  title?: string
  pret_redus?: number
  price?: number
  pret_original?: number
  originalPrice?: number
  procent_reducere?: number
  discount_percent?: number
  imagine_url?: string
  image?: string
  descriere?: string
  description?: string
  magazin?: string
  store?: string
  categorie?: string
  link_afiliat?: string
  affiliate_url?: string
  in_stock?: boolean
  is_active?: boolean
  activ?: boolean
  data_adaugare?: string
}

/**
 * Schema Product+Offer pentru un deal individual.
 * Afișat în Google Shopping / price chips în search results.
 */
export function dealToProductSchema(deal: DealForSchema, index: number) {
  const name = deal.titlu || deal.title || 'Ofertă'
  const price = deal.pret_redus ?? deal.price ?? 0
  const originalPrice = deal.pret_original ?? deal.originalPrice
  const image = deal.imagine_url || deal.image
  const description = deal.descriere || deal.description
  const storeName = (deal.magazin || deal.store || '').toUpperCase()
  const offerUrl = `${SITE}/out/${deal.id}`
  const inStock = deal.in_stock ?? deal.is_active ?? deal.activ ?? true

  // Preț valabil până la sfârșitul anului curent + 1
  const nextYear = new Date().getFullYear() + 1
  const priceValidUntil = `${nextYear}-01-01`

  const productSchema: Record<string, unknown> = {
    '@type': 'ListItem',
    position: index + 1,
    item: {
      '@type': 'Product',
      name,
      ...(image && { image }),
      ...(description && { description }),
      ...(storeName && { brand: { '@type': 'Brand', name: storeName } }),
      offers: {
        '@type': 'Offer',
        url: offerUrl,
        priceCurrency: 'RON',
        price: price,
        priceValidUntil,
        itemCondition: 'https://schema.org/NewCondition',
        availability: inStock
          ? 'https://schema.org/InStock'
          : 'https://schema.org/OutOfStock',
        ...(storeName && {
          seller: { '@type': 'Organization', name: storeName },
        }),
      },
    },
  }

  // Dacă există priceSpecification cu preț original
  if (originalPrice && originalPrice > price) {
    const offerItem = productSchema.item as Record<string, unknown>
    const offers = offerItem.offers as Record<string, unknown>
    offers.priceSpecification = {
      '@type': 'UnitPriceSpecification',
      price,
      priceCurrency: 'RON',
      referenceQuantity: {
        '@type': 'QuantitativeValue',
        value: 1,
        unitCode: 'C62',
      },
    }
  }

  return productSchema
}

/**
 * ItemList schema pentru o listă de deals (pagina magazin / categorie / deals).
 */
export function buildItemListSchema(
  name: string,
  deals: DealForSchema[],
  url?: string
) {
  return {
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name,
    ...(url && { url: `${SITE}${url}` }),
    numberOfItems: deals.length,
    itemListElement: deals.slice(0, 20).map((deal, i) =>
      dealToProductSchema(deal, i)
    ),
  }
}

/**
 * BreadcrumbList schema.
 */
export function buildBreadcrumbSchema(
  items: Array<{ name: string; href?: string }>
) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: item.name,
      ...(item.href && { item: `${SITE}${item.href}` }),
    })),
  }
}

/**
 * Combină mai multe scheme într-un singur @graph.
 */
export function buildGraphSchema(...schemas: object[]) {
  return {
    '@context': 'https://schema.org',
    '@graph': schemas.map((s) => {
      // Elimină @context din schemele individuale dacă există
      const { '@context': _, ...rest } = s as Record<string, unknown>
      return rest
    }),
  }
}
