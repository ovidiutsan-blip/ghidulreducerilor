import { ImageResponse } from 'next/og'

export const runtime = 'edge'

export async function GET() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '1200px',
          height: '630px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'linear-gradient(135deg, #171717 0%, #262626 50%, #171717 100%)',
          fontFamily: 'system-ui, sans-serif',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Background decorative circles */}
        <div
          style={{
            position: 'absolute',
            top: '-100px',
            right: '-100px',
            width: '400px',
            height: '400px',
            borderRadius: '50%',
            background: 'rgba(232, 38, 42, 0.08)',
            display: 'flex',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: '-80px',
            left: '-80px',
            width: '300px',
            height: '300px',
            borderRadius: '50%',
            background: 'rgba(232, 38, 42, 0.06)',
            display: 'flex',
          }}
        />

        {/* Logo badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '80px',
            height: '80px',
            borderRadius: '20px',
            background: '#E8262A',
            marginBottom: '28px',
          }}
        >
          <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
            <line x1="7" y1="7" x2="7.01" y2="7"/>
          </svg>
        </div>

        {/* Main title */}
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: '0px',
            marginBottom: '16px',
          }}
        >
          <span
            style={{
              fontSize: '64px',
              fontWeight: '800',
              color: '#ffffff',
              letterSpacing: '-1px',
            }}
          >
            Ghidul
          </span>
          <span
            style={{
              fontSize: '64px',
              fontWeight: '800',
              color: '#E8262A',
              letterSpacing: '-1px',
            }}
          >
            Reducerilor
          </span>
          <span
            style={{
              fontSize: '64px',
              fontWeight: '800',
              color: '#ffffff',
              letterSpacing: '-1px',
            }}
          >
            .ro
          </span>
        </div>

        {/* Tagline */}
        <p
          style={{
            fontSize: '26px',
            color: '#a3a3a3',
            textAlign: 'center',
            maxWidth: '700px',
            margin: '0 0 40px 0',
            lineHeight: '1.4',
          }}
        >
          Cele mai bune reduceri și coduri promoționale din România
        </p>

        {/* Store badges */}
        <div
          style={{
            display: 'flex',
            gap: '12px',
            flexWrap: 'nowrap',
          }}
        >
          {['🛒 eMAG', '📱 Telefoane', '💻 Laptopuri', '📺 TV & Audio', '🏠 Casa'].map((store) => (
            <div
              key={store}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '10px 20px',
                borderRadius: '100px',
                background: 'rgba(255,255,255,0.08)',
                border: '1px solid rgba(255,255,255,0.12)',
                color: '#e5e5e5',
                fontSize: '18px',
                fontWeight: '500',
              }}
            >
              {store}
            </div>
          ))}
        </div>

        {/* Bottom tagline */}
        <div
          style={{
            position: 'absolute',
            bottom: '32px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            color: '#525252',
            fontSize: '16px',
          }}
        >
          <span>✓ Verificate zilnic</span>
          <span style={{ margin: '0 8px' }}>·</span>
          <span>✓ Gratuit</span>
          <span style={{ margin: '0 8px' }}>·</span>
          <span>✓ Fără spam</span>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
      // Imaginea e statică (nu primește query params), deci poate fi cache-uită agresiv
      // pe CDN pentru un an. Se invalidează automat la următorul deploy.
      headers: {
        'Cache-Control': 'public, max-age=31536000, s-maxage=31536000, immutable',
      },
    }
  )
}
