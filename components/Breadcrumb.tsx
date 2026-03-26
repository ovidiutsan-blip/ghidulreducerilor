import Link from 'next/link'
import { ChevronRight, Home } from 'lucide-react'

type BreadcrumbItem = {
  label: string
  href?: string
}

export default function Breadcrumb({ items }: { items: BreadcrumbItem[] }) {
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Acasă', item: 'https://ghidulreducerilor.ro' },
      ...items.map((item, i) => ({
        '@type': 'ListItem',
        position: i + 2,
        name: item.label,
        ...(item.href ? { item: `https://ghidulreducerilor.ro${item.href}` } : {}),
      })),
    ],
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-sm text-neutral-500 mb-6 flex-wrap">
        <Link href="/" className="hover:text-brand-red transition-colors">
          <Home className="w-4 h-4" />
        </Link>
        {items.map((item, i) => (
          <span key={i} className="flex items-center gap-1.5">
            <ChevronRight className="w-3.5 h-3.5 text-neutral-300" />
            {item.href ? (
              <Link href={item.href} className="hover:text-brand-red transition-colors">
                {item.label}
              </Link>
            ) : (
              <span className="text-neutral-800 font-medium">{item.label}</span>
            )}
          </span>
        ))}
      </nav>
    </>
  )
}
