import { Metadata } from 'next'
import Link from 'next/link'
import Breadcrumb from '@/components/Breadcrumb'
import { getAllArticles } from '@/lib/blog'

export const metadata: Metadata = {
  title: 'Blog — Ghiduri, analize și calendare de reduceri',
  description: 'Ghiduri practice despre coduri de reducere, topuri magazine, calendar Black Friday și alte resurse pentru cumpărături online în România.',
  alternates: { canonical: '/blog' },
  openGraph: {
    title: 'Blog GhidulReducerilor.ro',
    description: 'Ghiduri, analize și calendare pentru cumpărători români în 2026.',
    url: '/blog',
    type: 'website',
  },
}

export default function BlogIndexPage() {
  const articles = getAllArticles()

  const blogListSchema = {
    '@context': 'https://schema.org',
    '@type': 'Blog',
    name: 'Blog GhidulReducerilor.ro',
    url: 'https://ghidulreducerilor.ro/blog',
    blogPost: articles.map(({ meta }) => ({
      '@type': 'BlogPosting',
      headline: meta.title,
      description: meta.description,
      datePublished: meta.publishedAt,
      dateModified: meta.updatedAt,
      url: `https://ghidulreducerilor.ro/blog/${meta.slug}`,
      author: { '@type': 'Organization', name: 'GhidulReducerilor.ro' },
    })),
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(blogListSchema) }}
      />

      <Breadcrumb items={[{ label: 'Blog' }]} />

      <header className="mb-10">
        <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-neutral-900 mb-3">
          Ghiduri & analize pentru cumpărători
        </h1>
        <p className="text-neutral-600 text-lg max-w-2xl">
          Articole despre cum să cumperi mai deștept online în România: ghiduri pentru coduri de
          reducere, topuri magazine, calendar sezonier și alte resurse verificate.
        </p>
      </header>

      <div className="space-y-6">
        {articles.map(({ meta }) => (
          <Link
            key={meta.slug}
            href={`/blog/${meta.slug}`}
            className="block group bg-white border border-neutral-200 rounded-2xl p-6 hover:border-brand-red hover:shadow-md transition-all"
          >
            <div className="flex gap-4 items-start">
              {meta.coverEmoji && (
                <div className="text-4xl shrink-0" aria-hidden>
                  {meta.coverEmoji}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <h2 className="font-display font-bold text-xl text-neutral-900 group-hover:text-brand-red transition-colors mb-2">
                  {meta.title}
                </h2>
                <p className="text-neutral-600 text-sm leading-relaxed mb-3">
                  {meta.excerpt}
                </p>
                <div className="flex items-center gap-3 text-xs text-neutral-500">
                  <time dateTime={meta.publishedAt}>
                    {new Date(meta.publishedAt).toLocaleDateString('ro-RO', {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric',
                    })}
                  </time>
                  <span>•</span>
                  <span>{meta.readingTimeMinutes} min citire</span>
                  {meta.tags.length > 0 && (
                    <>
                      <span>•</span>
                      <span className="flex gap-1">
                        {meta.tags.slice(0, 3).map(tag => (
                          <span key={tag} className="bg-neutral-100 px-2 py-0.5 rounded">
                            {tag}
                          </span>
                        ))}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {articles.length === 0 && (
        <p className="text-neutral-500 text-center py-12">
          Nu avem încă articole publicate. Revino în curând.
        </p>
      )}
    </div>
  )
}
