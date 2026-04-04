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
    ],
  },

  // Security headers
  async headers() {
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
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com https://www.google-analytics.com",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "img-src 'self' data: blob: https: http:",
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
