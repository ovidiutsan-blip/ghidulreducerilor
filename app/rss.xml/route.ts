import { NextResponse } from 'next/server'
import { getActiveDeals, getStoreForDeal } from '@/lib/data'
import { getAllArticles } from '@/lib/blog'

export const dynamic = 'force-static'
export const revalidate = 3600 // regenerate la fiecare oră

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://ghidulreducerilor.ro'
const SITE_TITLE = 'Ghidul Reducerilor — Reduceri și Coduri Promoționale România'
const SITE_DESC =
  'Feed RSS cu cele mai bune reduceri și articole noi de pe ghidulreducerilor.ro — magazine verificate, preturi omnibus, coduri promoționale active.'

// Escape XML entities pentru CDATA-safe content
function xmlEscape(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

function formatPrice(n: number): string {
  // Romanian format: 1.234,56 RON
  return n
    .toFixed(2)
    .replace('.', ',')
    .replace(/\B(?=(\d{3})+(?!\d))/g, '.')
}

export async function GET() {
  const now = new Date()
  const buildDate = now.toUTCString()

  // Top 30 deals sortate după dată
  const allDeals = getActiveDeals()
  const topDeals = [...allDeals]
    .sort((a, b) => {
      const da = new Date(a.data_adaugare).getTime()
      const db = new Date(b.data_adaugare).getTime()
      return db - da
    })
    .slice(0, 30)

  const dealItems = topDeals
    .map(deal => {
      const store = getStoreForDeal(deal)
      const storeName = store?.nume || deal.magazin
      const dealUrl = `${BASE_URL}/reduceri/${deal.magazin}#deal-${deal.id}`
      const title = `${deal.titlu} — ${deal.procent_reducere}% reducere la ${storeName}`
      const pubDate = new Date(deal.data_adaugare).toUTCString()
      const description = [
        `<strong>${xmlEscape(deal.titlu)}</strong>`,
        `<p>Reducere de <strong>${deal.procent_reducere}%</strong> la ${xmlEscape(storeName)}.</p>`,
        `<p>Preț original: <s>${formatPrice(deal.pret_original)} RON</s> — `,
        `Preț redus: <strong>${formatPrice(deal.pret_redus)} RON</strong></p>`,
        deal.imagine_url ? `<p><img src="${xmlEscape(deal.imagine_url)}" alt="${xmlEscape(deal.titlu)}" /></p>` : '',
      ].join('')

      return `    <item>
      <title>${xmlEscape(title)}</title>
      <link>${xmlEscape(dealUrl)}</link>
      <guid isPermaLink="false">deal-${xmlEscape(deal.id)}</guid>
      <pubDate>${pubDate}</pubDate>
      <category>${xmlEscape(deal.categorie)}</category>
      <description><![CDATA[${description}]]></description>
    </item>`
    })
    .join('\n')

  // Blog articles
  const articles = getAllArticles()
  const articleItems = articles
    .map(({ meta }) => {
      const articleUrl = `${BASE_URL}/blog/${meta.slug}`
      const pubDate = new Date(meta.publishedAt).toUTCString()
      return `    <item>
      <title>${xmlEscape(meta.title)}</title>
      <link>${xmlEscape(articleUrl)}</link>
      <guid isPermaLink="true">${xmlEscape(articleUrl)}</guid>
      <pubDate>${pubDate}</pubDate>
      ${meta.tags.map(t => `<category>${xmlEscape(t)}</category>`).join('\n      ')}
      <description><![CDATA[${meta.excerpt || meta.description}]]></description>
    </item>`
    })
    .join('\n')

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>${xmlEscape(SITE_TITLE)}</title>
    <link>${BASE_URL}</link>
    <description>${xmlEscape(SITE_DESC)}</description>
    <language>ro-RO</language>
    <lastBuildDate>${buildDate}</lastBuildDate>
    <atom:link href="${BASE_URL}/rss.xml" rel="self" type="application/rss+xml" />
    <generator>Next.js ghidulreducerilor.ro</generator>
${articleItems}
${dealItems}
  </channel>
</rss>`

  return new NextResponse(xml, {
    status: 200,
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
      'Cache-Control': 'public, max-age=3600, s-maxage=3600, stale-while-revalidate=86400',
    },
  })
}
