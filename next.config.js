/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      // eMAG CDN (**.akamaized.net acoperă s1emagst/s13emagst)
      { protocol: 'https', hostname: '**.emag.ro' },
      { protocol: 'https', hostname: '**.akamaized.net' },
      // Profitshare campaign images
      { protocol: 'https', hostname: 'app.profitshare.ro' },
      // Profitshare product feed images
      { protocol: 'http', hostname: 'profitsmart.ro' },
      { protocol: 'https', hostname: 'profitsmart.ro' },
      // evoMAG
      { protocol: 'https', hostname: '**.evomag.ro' },
      // NB: Next.js acceptă MAX 50 de intrări în remotePatterns (build-ul pică
      // peste limită). Notino/Answear/Decathlon/Dr.Max au fost scoase (magazine
      // neaprobate sau dezactivate, 0 imagini în deals.json) — re-adaugă doar
      // la reactivarea magazinului și verifică totalul cu
      // tests/test_image_hosts_allowlisted.py.
      // Watch24 (**.watch24.ro acoperă cdn.watch24.ro)
      { protocol: 'https', hostname: '**.watch24.ro' },
      { protocol: 'https', hostname: 'cdn.contentspeed.ro' },
      // Vegis (PS feed — **.vegis.ro acoperă cdn.vegis.ro)
      { protocol: 'https', hostname: '**.vegis.ro' },
      // Hiris (CDN cdnmp.net — **.cdnmp.net acoperă c.cdnmp.net)
      { protocol: 'https', hostname: '**.cdnmp.net' },
      { protocol: 'https', hostname: '**.hiris.ro' },
      // Alecoair (direct)
      { protocol: 'https', hostname: '**.alecoair.ro' },
      { protocol: 'https', hostname: 'alecoair.ro' },
      // Hotpick (direct)
      { protocol: 'https', hostname: '**.hotpick.ro' },
      { protocol: 'https', hostname: 'hotpick.ro' },
      // Mathaus (CDN)
      { protocol: 'https', hostname: '**.mathaus.ro' },
      { protocol: 'https', hostname: 'mathaus.ro' },
      // Gomag CDN (platforma comuna pentru streamstore + alte Gomag merchants)
      { protocol: 'https', hostname: 'gomagcdn.ro' },
      { protocol: 'https', hostname: '**.gomagcdn.ro' },
      // Streamstore domain fallback
      { protocol: 'https', hostname: '**.streamstore.ro' },
      { protocol: 'https', hostname: 'streamstore.ro' },
      // Case-smart (WordPress/WooCommerce, wp-content/uploads)
      { protocol: 'https', hostname: 'case-smart.ro' },
      { protocol: 'https', hostname: '**.case-smart.ro' },
      // Novodoors, Techstar, Forit (PS-imported merchants — check if on own domain)
      { protocol: 'https', hostname: '**.novodoors.ro' },
      { protocol: 'https', hostname: 'novodoors.ro' },
      { protocol: 'https', hostname: '**.techstar.ro' },
      { protocol: 'https', hostname: 'techstar.ro' },
      // SpringFarma (2Performant feed — **.springfarma.com acoperă www)
      { protocol: 'https', hostname: '**.springfarma.com' },
      // Somnart (2Performant feed — WordPress/WooCommerce)
      { protocol: 'https', hostname: 'somnart.ro' },
      { protocol: 'https', hostname: '**.somnart.ro' },
      // ImageKit CDN (casanewconcept și-a mutat imaginile aici; og:image de pe
      // paginile produs indică ik.imagekit.io/d3vpro/cnc/...)
      { protocol: 'https', hostname: 'ik.imagekit.io' },
      // Casa New Concept (2Performant feed — OpenCart image/catalog)
      { protocol: 'https', hostname: 'casanewconcept.ro' },
      { protocol: 'https', hostname: '**.casanewconcept.ro' },
      // Mobila Laguna (2Performant feed)
      { protocol: 'https', hostname: 'mobilalaguna.ro' },
      { protocol: 'https', hostname: '**.mobilalaguna.ro' },
      // Mobiro (2Performant feed — WordPress)
      { protocol: 'https', hostname: 'mobiro.ro' },
      { protocol: 'https', hostname: '**.mobiro.ro' },
      // Merchants PS noi (scan 2026-07-14): CITGrup, Navigatiiandroid,
      // Perfectbijoux, Startdecor, eMobili (Watch24 era deja allowlisted).
      // Host-urile sunt domeniile proprii; verifică guardrail-ul
      // tests/test_image_hosts_allowlisted.py după primul feed-run.
      { protocol: 'https', hostname: '**.citgrup.ro' },
      { protocol: 'https', hostname: 'citgrup.ro' },
      { protocol: 'https', hostname: '**.navigatiiandroid.ro' },
      { protocol: 'https', hostname: 'navigatiiandroid.ro' },
      { protocol: 'https', hostname: '**.perfectbijoux.ro' },
      { protocol: 'https', hostname: 'perfectbijoux.ro' },
      { protocol: 'https', hostname: '**.startdecor.ro' },
      { protocol: 'https', hostname: 'startdecor.ro' },
      { protocol: 'https', hostname: '**.emobili.ro' },
      { protocol: 'https', hostname: 'emobili.ro' },
      // Generic CDNs
      { protocol: 'https', hostname: '**.cloudfront.net' },
      { protocol: 'https', hostname: '**.shopify.com' },
    ],
  },
  // Redirects: pivot către /reduceri/[m] (codes.json deprecated 2026-04-29)
  // /coduri-promo + /cod-reducere → /reduceri (canonical URL change, 308 permanent)
  async redirects() {
    return [
      {
        source: '/coduri-promo/:magazin',
        destination: '/reduceri/:magazin',
        permanent: true,
      },
      {
        source: '/cod-reducere/:magazin',
        destination: '/reduceri/:magazin',
        permanent: true,
      },
      {
        source: '/cod-reducere',
        destination: '/deals',
        permanent: true,
      },
    ]
  },

  // Security headers
  async headers() {
    const isProd = process.env.NODE_ENV === 'production'
    // React dev mode needs `'unsafe-eval'` (source maps, error overlay).
    // In production React never calls eval — drop it.
    const scriptSrc = isProd
      ? "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com"
      : "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com https://www.google-analytics.com"

    return [
      {
        // Profitshare validation file - serve as text/plain
        source: '/2fbe74572bd296845e920501e42623f6',
        headers: [
          { key: 'Content-Type', value: 'text/plain' },
        ],
      },
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              scriptSrc,
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "img-src 'self' data: blob: https:",
              "font-src 'self' https://fonts.gstatic.com",
              "connect-src 'self' https://www.google-analytics.com https://api.brevo.com https://region1.google-analytics.com",
              "frame-ancestors 'none'",
            ].join('; '),
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig
