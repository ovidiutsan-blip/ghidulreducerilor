import { MetadataRoute } from 'next'
import { getAllStoreSlugs, getDealsByStore, getCodesByStore } from '@/lib/data'
import { getAllArticles } from '@/lib/blog'
import { getAllThemeHubSlugs } from '@/lib/theme-hubs'

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://ghidulreducerilor.ro'

export default function sitemap(): MetadataRoute.Sitemap {
  const stores = getAllStoreSlugs()
  const now = new Date()

  const staticPages = [
    { url: BASE_URL, lastModified: now, changeFrequency: 'daily' as const, priority: 1 },
    { url: `${BASE_URL}/blog`, lastModified: now, changeFrequency: 'weekly' as const, priority: 0.7 },
    { url: `${BASE_URL}/categorii`, lastModified: now, changeFrequency: 'weekly' as const, priority: 0.7 },
    { url: `${BASE_URL}/cum-functioneaza`, lastModified: now, changeFrequency: 'monthly' as const, priority: 0.6 },
    { url: `${BASE_URL}/abonare-alerte`, lastModified: now, changeFrequency: 'monthly' as const, priority: 0.5 },
    { url: `${BASE_URL}/despre`, lastModified: now, changeFrequency: 'monthly' as const, priority: 0.3 },
  ]

  // Blog articles
  const blogPages: MetadataRoute.Sitemap = getAllArticles().map(({ meta }) => ({
    url: `${BASE_URL}/blog/${meta.slug}`,
    lastModified: new Date(meta.updatedAt),
    changeFrequency: 'monthly' as const,
    priority: 0.6,
  }))

  // Thematic category hubs
  const themeHubPages: MetadataRoute.Sitemap = getAllThemeHubSlugs().map(slug => ({
    url: `${BASE_URL}/categorii/${slug}`,
    lastModified: now,
    changeFrequency: 'weekly' as const,
    priority: 0.7,
  }))

  // Include doar paginile cu conținut — pagini goale au noindex și nu aparțin în sitemap
  const storePages = stores.flatMap(slug => {
    const hasDeals = getDealsByStore(slug).length > 0
    const hasCodes = getCodesByStore(slug).length > 0
    const entries: MetadataRoute.Sitemap = []

    if (hasDeals) {
      entries.push({
        url: `${BASE_URL}/reduceri/${slug}`,
        lastModified: now,
        changeFrequency: 'daily' as const,
        priority: 0.9,
      })
    }
    if (hasCodes) {
      entries.push({
        url: `${BASE_URL}/coduri-promo/${slug}`,
        lastModified: now,
        changeFrequency: 'daily' as const,
        priority: 0.8,
      })
    }
    return entries
  })

  return [...staticPages, ...blogPages, ...themeHubPages, ...storePages]
}
