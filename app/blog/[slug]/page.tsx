import { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import Breadcrumb from '@/components/Breadcrumb'
import { getAllArticleSlugs, getArticleBySlug, getRelatedArticles } from '@/lib/blog'

type Props = { params: { slug: string } }

export function generateStaticParams() {
  return getAllArticleSlugs().map(slug => ({ slug }))
}

export function generateMetadata({ params }: Props): Metadata {
  const article = getArticleBySlug(params.slug)
  if (!article) {
    return { title: 'Articol inexistent' }
  }
  const { meta } = article
  return {
    title: meta.title,
    description: meta.description,
    alternates: { canonical: `/blog/${meta.slug}` },
    openGraph: {
      title: meta.title,
      description: meta.description,
      url: `/blog/${meta.slug}`,
      type: 'article',
      publishedTime: meta.publishedAt,
      modifiedTime: meta.updatedAt,
      authors: meta.author ? [meta.author] : undefined,
      tags: meta.tags,
    },
    twitter: {
      card: 'summary_large_image',
      title: meta.title,
      description: meta.description,
    },
  }
}

export default function BlogArticlePage({ params }: Props) {
  const article = getArticleBySlug(params.slug)
  if (!article) notFound()
  const { meta, Body } = article
  const related = getRelatedArticles(params.slug, 2)

  const articleSchema = {
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: meta.title,
    description: meta.description,
    datePublished: meta.publishedAt,
    dateModified: meta.updatedAt,
    author: {
      '@type': meta.author ? 'Person' : 'Organization',
      name: meta.author || 'GhidulReducerilor.ro',
    },
    publisher: {
      '@type': 'Organization',
      name: 'GhidulReducerilor.ro',
      logo: {
        '@type': 'ImageObject',
        url: 'https://ghidulreducerilor.ro/logo.png',
      },
    },
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': `https://ghidulreducerilor.ro/blog/${meta.slug}`,
    },
    keywords: meta.tags.join(', '),
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleSchema) }}
      />

      <Breadcrumb
        items={[
          { label: 'Blog', href: '/blog' },
          { label: meta.title },
        ]}
      />

      <article>
        <header className="mb-8">
          {meta.coverEmoji && (
            <div className="text-5xl mb-4" aria-hidden>
              {meta.coverEmoji}
            </div>
          )}
          <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-neutral-900 mb-4">
            {meta.title}
          </h1>
          <div className="flex flex-wrap items-center gap-3 text-sm text-neutral-500">
            <time dateTime={meta.publishedAt}>
              Publicat{' '}
              {new Date(meta.publishedAt).toLocaleDateString('ro-RO', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
              })}
            </time>
            {meta.updatedAt !== meta.publishedAt && (
              <>
                <span>•</span>
                <time dateTime={meta.updatedAt}>
                  Actualizat{' '}
                  {new Date(meta.updatedAt).toLocaleDateString('ro-RO', {
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                  })}
                </time>
              </>
            )}
            <span>•</span>
            <span>{meta.readingTimeMinutes} min citire</span>
            {meta.author && (
              <>
                <span>•</span>
                <span>de {meta.author}</span>
              </>
            )}
          </div>
        </header>

        <div className="prose prose-neutral max-w-none prose-a:text-brand-red prose-a:no-underline hover:prose-a:underline">
          <Body />
        </div>

        {meta.tags.length > 0 && (
          <div className="mt-10 pt-6 border-t border-neutral-200">
            <div className="flex flex-wrap gap-2">
              {meta.tags.map(tag => (
                <span
                  key={tag}
                  className="inline-block bg-neutral-100 text-neutral-700 text-xs px-3 py-1 rounded-full"
                >
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </article>

      {related.length > 0 && (
        <aside className="mt-12 pt-8 border-t border-neutral-200">
          <h2 className="font-display font-bold text-xl text-neutral-900 mb-5">
            Articole similare
          </h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {related.map(({ meta: r }) => (
              <Link
                key={r.slug}
                href={`/blog/${r.slug}`}
                className="block bg-white border border-neutral-200 rounded-xl p-4 hover:border-brand-red hover:shadow-sm transition-all"
              >
                {r.coverEmoji && (
                  <div className="text-2xl mb-2" aria-hidden>
                    {r.coverEmoji}
                  </div>
                )}
                <h3 className="font-display font-semibold text-base text-neutral-900 mb-1">
                  {r.title}
                </h3>
                <p className="text-sm text-neutral-600 line-clamp-2">{r.excerpt}</p>
              </Link>
            ))}
          </div>
        </aside>
      )}
    </div>
  )
}
