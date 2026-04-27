/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      // eMAG CDN
      { protocol: 'https', hostname: 's13emagst.akamaized.net' },
      { protocol: 'https', hostname: 's1emagst.akamaized.net' },
      { protocol: 'https', hostname: '**.emag.ro' },
      { protocol: 'https', hostname: '**.akamaized.net' },
      // Profitshare campaign images
      { protocol: 'https', hostname: 'app.profitshare.ro' },
      // Profitshare product feed images
      { protocol: 'http', hostname: 'profitsmart.ro' },
      { protocol: 'https', hostname: 'profitsmart.ro' },
      // FashionDays
      { protocol: 'https', hostname: '**.fashiondays.ro' },
      { protocol: 'https', hostname: '**.fashioncdn.ro' },
      // Elefant.ro
      { protocol: 'https', hostname: '**.elefant.ro' },
      { protocol: 'https', hostname: '**.elefant.cdn' },
      // evoMAG
      { protocol: 'https', hostname: '**.evomag.ro' },
      // Notino (when approved)
      { protocol: 'https', hostname: '**.notino.ro' },
      { protocol: 'https', hostname: '**.notinoimg.com' },
      // Answear (when approved)
      { protocol: 'https', hostname: '**.answear.ro' },
      // Decathlon (when approved)
      { protocol: 'https', hostname: '**.decathlon.ro' },
      { protocol: 'https', hostname: '**.decathloncoach.com' },
      // Dr.Max (when approved)
      { protocol: 'https', hostname: '**.drmax.ro' },
      // Watch24
      { protocol: 'https', hostname: '**.watch24.ro' },
      { protocol: 'https', hostname: 'cdn.watch24.ro' },
      // ForIT
      { protocol: 'https', hostname: '**.forit.ro' },
      // Fornello
      { protocol: 'https', hostname: '**.fornello.ro' },
      { protocol: 'https', hostname: 'cdn.contentspeed.ro' },
      // Vegis (PS feed — cdn.vegis.ro + lazy-loader)
      { protocol: 'https', hostname: 'cdn.vegis.ro' },
      { protocol: 'https', hostname: '**.vegis.ro' },
      // Hiris (CDN cdnmp.net — Gomag/Magento platform)
      { protocol: 'https', hostname: 'c.cdnmp.net' },
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
      // SpringFarma (2Performant feed — Magento CDN)
      { protocol: 'https', hostname: 'www.springfarma.com' },
      { protocol: 'https', hostname: '**.springfarma.com' },
      // Generic CDNs
      { protocol: 'https', hostname: '**.cloudfront.net' },
      { protocol: 'https', hostname: '**.shopify.com' },
    ],
  },
  // Redirects: /coduri-promo → /cod-reducere (canonical URL change)
  async redirects() {
    return [
      {
        source: '/coduri-promo/:magazin',
        destination: '/cod-reducere/:magazin',
        permanent: true, // 301 — transferă PageRank
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
