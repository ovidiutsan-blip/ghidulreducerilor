import { NextRequest, NextResponse } from 'next/server'
import { getActiveDeals, getAllStoreSlugs, getDealsByStore } from '@/lib/data'
import { getAllArticles } from '@/lib/blog'
import { getAllThemeHubSlugs } from '@/lib/theme-hubs'
import { getAllStoreGuideSlugs } from '@/lib/store-guides'

// Singurul cron care rulează pe Vercel — notifică search engines cu URL-urile actualizate
// Toate celelalte cron-uri rulează via GitHub Actions
//
// 2023+: Google și Bing au deprecat endpoint-ul /ping?sitemap=.
// Folosim IndexNow protocol (Bing, Yandex, Seznam, Naver) + Bing sitemap hint.
// IndexNow key file: public/qj1ck64io70epfm3xzudslytvwbg5han.txt (plaintext = valoarea cheii)

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://ghidulreducerilor.ro'
const INDEXNOW_KEY = 'qj1ck64io70epfm3xzudslytvwbg5han'
const INDEXNOW_KEY_LOCATION = `${BASE_URL}/${INDEXNOW_KEY}.txt`
const HOST = BASE_URL.replace(/^https?:\/\//, '')

function isCronRequest(req: NextRequest): boolean {
  return req.headers.get('authorization') === `Bearer ${process.env.CRON_SECRET}`
}

// Construiește lista URL-urilor importante pentru reindexare (max 10.000 per cerere conform IndexNow spec)
function buildUrlList(): string[] {
  const urls: string[] = [
    `${BASE_URL}/`,
    `${BASE_URL}/sitemap.xml`,
    `${BASE_URL}/rss.xml`,
    `${BASE_URL}/blog`,
    `${BASE_URL}/categorii`,
    `${BASE_URL}/ghiduri`,
    `${BASE_URL}/black-friday`,
  ]

  // Toate articolele de blog
  for (const { meta } of getAllArticles()) {
    urls.push(`${BASE_URL}/blog/${meta.slug}`)
  }

  // Toate hub-urile tematice
  for (const slug of getAllThemeHubSlugs()) {
    urls.push(`${BASE_URL}/categorii/${slug}`)
  }

  // Toate ghidurile per magazin
  for (const slug of getAllStoreGuideSlugs()) {
    urls.push(`${BASE_URL}/ghiduri/${slug}`)
  }

  // Pagini de magazin cu deal-uri active
  for (const slug of getAllStoreSlugs()) {
    if (getDealsByStore(slug).length > 0) {
      urls.push(`${BASE_URL}/reduceri/${slug}`)
    }
  }

  // Deduplicate
  return Array.from(new Set(urls))
}

async function submitIndexNow(urlList: string[]): Promise<{ ok: boolean; status: number; count: number }> {
  const payload = {
    host: HOST,
    key: INDEXNOW_KEY,
    keyLocation: INDEXNOW_KEY_LOCATION,
    urlList,
  }

  try {
    const res = await fetch('https://api.indexnow.org/indexnow', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
      },
      body: JSON.stringify(payload),
    })
    // IndexNow: 200 = success, 202 = accepted, 400 = bad request, 403 = key mismatch, 422 = already submitted recently
    return { ok: res.status === 200 || res.status === 202, status: res.status, count: urlList.length }
  } catch (error) {
    return { ok: false, status: 0, count: urlList.length }
  }
}

async function submitBingIndexNow(sitemapUrl: string): Promise<number> {
  // Bing IndexNow single-URL endpoint ca fallback — reindexează sitemap-ul direct
  try {
    const res = await fetch(
      `https://www.bing.com/indexnow?url=${encodeURIComponent(sitemapUrl)}&key=${INDEXNOW_KEY}`,
      { method: 'GET' }
    )
    return res.status
  } catch {
    return 0
  }
}

export async function GET(req: NextRequest) {
  if (!isCronRequest(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const sitemapUrl = `${BASE_URL}/sitemap.xml`
  const urlList = buildUrlList()
  const dealCount = getActiveDeals().length

  // IndexNow submission — un singur request notifică Bing, Yandex, Seznam, Naver
  const indexNow = await submitIndexNow(urlList)

  // Bing sitemap hint via IndexNow single-URL endpoint
  const bingStatus = await submitBingIndexNow(sitemapUrl)

  console.log(
    `[CRON sitemap-ping] IndexNow: ${indexNow.status} (${indexNow.count} URLs), Bing sitemap: ${bingStatus}`
  )

  return NextResponse.json({
    ok: indexNow.ok,
    sitemap: sitemapUrl,
    dealCount,
    indexNow: {
      status: indexNow.status,
      urlCount: indexNow.count,
    },
    bing: bingStatus,
    timestamp: new Date().toISOString(),
  })
}
