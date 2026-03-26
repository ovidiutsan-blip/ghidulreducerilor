import type { Metadata } from 'next'
import Navbar from '@/components/Navbar'
import Footer from '@/components/Footer'
import './globals.css'

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://ghidulreducerilor.ro'),
  title: {
    default: 'GhidulReducerilor.ro — Reduceri și Coduri Promoționale România',
    template: '%s | GhidulReducerilor.ro',
  },
  description: 'Cele mai bune reduceri, oferte și coduri promoționale din România. eMAG, Altex, Fashion Days și alte magazine — verificate zilnic.',
  openGraph: {
    type: 'website',
    locale: 'ro_RO',
    siteName: 'GhidulReducerilor.ro',
    title: 'GhidulReducerilor.ro — Reduceri și Coduri Promoționale România',
    description: 'Cele mai bune reduceri, oferte și coduri promoționale din România. Verificate zilnic.',
  },
  twitter: {
    card: 'summary_large_image',
  },
  robots: {
    index: true,
    follow: true,
  },
  alternates: {
    canonical: '/',
  },
}

// Google Analytics 4 — activează după ce obții Measurement ID
function Analytics() {
  const gaId = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID
  if (!gaId || gaId === 'G-XXXXXXXXXX') return null

  return (
    <>
      <script async src={`https://www.googletagmanager.com/gtag/js?id=${gaId}`} />
      <script
        dangerouslySetInnerHTML={{
          __html: `window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${gaId}');`,
        }}
      />
    </>
  )
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ro">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#E8262A" />
        <Analytics />
      </head>
      <body className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  )
}
