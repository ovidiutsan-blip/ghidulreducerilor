/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'images.unsplash.com' },
      { protocol: 'https', hostname: 'via.placeholder.com' },
      { protocol: 'https', hostname: 's13emagst.akamaized.net' },
      { protocol: 'https', hostname: '**.emag.ro' },
      { protocol: 'https', hostname: '**.notino.ro' },
      { protocol: 'https', hostname: 'cdn.notinoimg.com' },
      { protocol: 'https', hostname: '**.answear.ro' },
      { protocol: 'https', hostname: '**.decathlon.ro' },
      { protocol: 'https', hostname: '**.catena.ro' },
      { protocol: 'https', hostname: '**.cel.ro' },
      { protocol: 'https', hostname: '**.pcgarage.ro' },
      { protocol: 'https', hostname: '**.vexio.ro' },
      { protocol: 'https', hostname: '**.libris.ro' },
      { protocol: 'https', hostname: '**.fornello.ro' },
      { protocol: 'https', hostname: '**.forit.ro' },
      { protocol: 'https', hostname: '**.akamaized.net' },
      { protocol: 'https', hostname: '**.cloudfront.net' },
    ],
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
}

module.exports = nextConfig
