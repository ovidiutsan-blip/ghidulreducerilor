import { MetadataRoute } from 'next'
import { getAllStoreSlugs, getDealsByStore, getAllCategories } from '@/lib/data'
import { getAllArticles } from '@/lib/blog'
import { getAllThemeHubSlugs, getThemeHubBySlug } from '@/lib/theme-hubs'
import { getAllStoreGuideSlugs } from '@/lib/store-guides'

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://ghidulreducerilor.ro'

export default function sitemap(): MetadataRoute.Sitemap {
  const stores = getAllStoreSlugs()
  const now = new Date()

  const staticPages = [
    { url: BASE_URL, lastModified: now, changeFrequency: 'daily' as const, priority: 1 },
    { url: `${BASE_URL}/black-friday`, lastModified: now, changeFrequency: 'weekly' as const, priority: 0.9 },
    { url: `${BASE_URL}/blog`, lastModified: now, changeFrequency: 'weekly' as const, priority: 0.7 },
    { url: `${BASE_URL}/categorii`, lastModified: now, changeFrequency: 'weekly' as const, priority: 0.7 },
    { url: `${BASE_URL}/ghiduri`, lastModified: now, changeFrequency: 'weekly' as const, priority: 0.7 },
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

  // Thematic category hubs (rich editorial content)
  const themeHubPages: MetadataRoute.Sitemap = getAllThemeHubSlugs().map(slug => ({
    url: `${BASE_URL}/categorii/${slug}`,
    lastModified: now,
    changeFrequency: 'weekly' as const,
    priority: 0.7,
  }))

  // /categorie/[slug] — only for slugs without an overlapping theme hub
  // (overlapping ones already canonical-redirect to /categorii/* and shouldn't
  // appear twice in the sitemap).
  const categoryPages: MetadataRoute.Sitemap = getAllCategories()
    .filter(slug => !getThemeHubBySlug(slug))
    .map(slug => ({
      url: `${BASE_URL}/categorie/${slug}`,
      lastModified: now,
      changeFrequency: 'daily' as const,
      priority: 0.6,
    }))

  // Store guides
  const storeGuidePages: MetadataRoute.Sitemap = getAllStoreGuideSlugs().map(slug => ({
    url: `${BASE_URL}/ghiduri/${slug}`,
    lastModified: now,
    changeFrequency: 'monthly' as const,
    priority: 0.7,
  }))

  // Pagini magazin — doar cele cu deal-uri active (paginile goale au noindex automat)
  const storePages: MetadataRoute.Sitemap = stores
    .filter(slug => getDealsByStore(slug).length > 0)
    .map(slug => ({
      url: `${BASE_URL}/reduceri/${slug}`,
      lastModified: now,
      changeFrequency: 'daily' as const,
      priority: 0.9,
    }))

  return [...staticPages, ...blogPages, ...themeHubPages, ...categoryPages, ...storeGuidePages, ...storePages]
}
