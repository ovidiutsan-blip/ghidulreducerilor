import { NextResponse } from 'next/server'
import dealsData from '@/data/deals.json'
import type { Deal } from '@/lib/data'

const deals = dealsData as Deal[]

// Hostnames permise pentru redirect afiliat. Match exact sau sufix DNS (`.host`).
const ALLOWED_AFFILIATE_HOSTS = [
  'l.profitshare.ro',
  'app.profitshare.ro',
  'event.2performant.com',
  'vegis.ro',
  'evomag.ro',
]

function isAllowedAffiliateUrl(url: string): boolean {
  try {
    const u = new URL(url)
    if (u.protocol !== 'https:' && u.protocol !== 'http:') return false
    return ALLOWED_AFFILIATE_HOSTS.some(
      h => u.hostname === h || u.hostname.endsWith('.' + h)
    )
  } catch {
    return false
  }
}

const FALLBACK_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://ghidulreducerilor.ro'

function safeRedirect(req: Request, target: string, ctx: { id: string; type: string; magazin: string; label: string }) {
  if (!isAllowedAffiliateUrl(target)) {
    console.warn(`[REDIRECT BLOCKED] ${ctx.type}:${ctx.id} | ${ctx.magazin} | host not allowed: ${target}`)
    return NextResponse.redirect(FALLBACK_URL, { status: 302 })
  }
  logClick(req, ctx.id, ctx.type, ctx.magazin, ctx.label)
  return NextResponse.redirect(target, { status: 302 })
}

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params

  // ID numeric = link Profitshare direct (l.profitshare.ro/l/NNNNN)
  if (/^\d+$/.test(id)) {
    return safeRedirect(req, `https://l.profitshare.ro/l/${id}`, {
      id, type: 'profitshare', magazin: 'profitshare', label: `PS link ${id}`
    })
  }

  // Caută în deals (by id sau slug)
  const deal = deals.find(d => d.id === id || d.slug === id)
  if (deal?.link_afiliat) {
    const selfRef = deal.link_afiliat.match(/\/out\/(\d+)/)
    const target = selfRef
      ? `https://l.profitshare.ro/l/${selfRef[1]}`
      : deal.link_afiliat
    return safeRedirect(req, target, { id, type: 'deal', magazin: deal.magazin, label: deal.titlu })
  }

  // Fallback la homepage
  console.log(`[REDIRECT] 404 — ID inexistent: ${id}`)
  return NextResponse.redirect(FALLBACK_URL, { status: 302 })
}

function logClick(req: Request, id: string, type: string, magazin: string, label: string) {
  const ua = req.headers.get('user-agent') || ''
  const referer = req.headers.get('referer') || ''
  const isMobile = /Mobile|Android|iPhone/i.test(ua)

  console.log(
    `[CLICK] ${new Date().toISOString()} | ${type}:${id} | ${magazin} | "${label}" | ${isMobile ? 'mobile' : 'desktop'} | ref:${referer}`
  )
}
