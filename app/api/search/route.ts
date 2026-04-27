import { NextRequest, NextResponse } from 'next/server'
import dealsData from '@/data/deals.json'
import type { Deal } from '@/lib/data'

const allDeals = (dealsData as Deal[]).filter(d => d.activ)

export type SearchResult = {
  id: string
  titlu: string
  imagine_url: string
  pret_redus: number
  pret_original: number
  procent_reducere: number
}

export async function GET(req: NextRequest) {
  const q = (req.nextUrl.searchParams.get('q') || '').trim().toLowerCase()
  const limit = Math.min(parseInt(req.nextUrl.searchParams.get('limit') || '10', 10) || 10, 25)

  if (q.length < 2) {
    return NextResponse.json({ results: [] satisfies SearchResult[] })
  }

  const results: SearchResult[] = []
  for (const d of allDeals) {
    if (d.titlu.toLowerCase().includes(q) || d.categorie.toLowerCase().includes(q)) {
      results.push({
        id: d.id,
        titlu: d.titlu,
        imagine_url: d.imagine_url,
        pret_redus: d.pret_redus,
        pret_original: d.pret_original,
        procent_reducere: d.procent_reducere,
      })
      if (results.length >= limit) break
    }
  }

  return NextResponse.json(
    { results },
    {
      headers: {
        'Cache-Control': 'public, s-maxage=300, stale-while-revalidate=86400',
      },
    }
  )
}
