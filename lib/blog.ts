import type { ReactNode } from 'react'

export type BlogArticleMeta = {
  slug: string
  title: string
  description: string
  excerpt: string
  publishedAt: string // ISO date
  updatedAt: string // ISO date
  author?: string
  tags: string[]
  coverEmoji?: string
  readingTimeMinutes: number
}

export type BlogArticle = {
  meta: BlogArticleMeta
  Body: () => ReactNode
}

import { article as ceEsteUnCodReducere } from '@/app/blog/articles/ce-este-un-cod-reducere'
import { article as topMagazineRomania2026 } from '@/app/blog/articles/top-10-magazine-reduceri-romania-2026'
import { article as calendarBlackFriday2026 } from '@/app/blog/articles/calendar-black-friday-2026'
import { article as topReduceriSaptamana2026W17 } from '@/app/blog/articles/top-reduceri-saptamana-2026-w17'
import { article as topReduceriSaptamana2026W18 } from '@/app/blog/articles/top-reduceri-saptamana-2026-w18'
import { article as topReduceriSaptamana2026W19 } from '@/app/blog/articles/top-reduceri-saptamana-2026-w19'
import { article as topReduceriSaptamana2026W20 } from '@/app/blog/articles/top-reduceri-saptamana-2026-w20'
import { article as topReduceriSaptamana2026W21 } from '@/app/blog/articles/top-reduceri-saptamana-2026-w21'
import { article as topReduceriSaptamana2026W22 } from '@/app/blog/articles/top-reduceri-saptamana-2026-w22'
import { article as topReduceriSaptamana2026W23 } from '@/app/blog/articles/top-reduceri-saptamana-2026-w23'
import { article as topReduceriSaptamana2026W24 } from '@/app/blog/articles/top-reduceri-saptamana-2026-w24'

const REGISTRY: BlogArticle[] = [
  ceEsteUnCodReducere,
  topMagazineRomania2026,
  calendarBlackFriday2026,
  topReduceriSaptamana2026W17,
  topReduceriSaptamana2026W18,
  topReduceriSaptamana2026W19,
  topReduceriSaptamana2026W20,
  topReduceriSaptamana2026W21,
  topReduceriSaptamana2026W22,
  topReduceriSaptamana2026W23,
  topReduceriSaptamana2026W24,
]

export function getAllArticles(): BlogArticle[] {
  return [...REGISTRY].sort(
    (a, b) => new Date(b.meta.publishedAt).getTime() - new Date(a.meta.publishedAt).getTime()
  )
}

export function getArticleBySlug(slug: string): BlogArticle | undefined {
  return REGISTRY.find(a => a.meta.slug === slug)
}

export function getAllArticleSlugs(): string[] {
  return REGISTRY.map(a => a.meta.slug)
}

export function getRelatedArticles(slug: string, limit: number = 2): BlogArticle[] {
  const current = getArticleBySlug(slug)
  if (!current) return []
  const others = REGISTRY.filter(a => a.meta.slug !== slug)
  // Sort: articles sharing tags first, then newest
  const scored = others.map(a => ({
    a,
    tagOverlap: a.meta.tags.filter(t => current.meta.tags.includes(t)).length,
  }))
  scored.sort((x, y) => {
    if (y.tagOverlap !== x.tagOverlap) return y.tagOverlap - x.tagOverlap
    return new Date(y.a.meta.publishedAt).getTime() - new Date(x.a.meta.publishedAt).getTime()
  })
  return scored.slice(0, limit).map(s => s.a)
}
