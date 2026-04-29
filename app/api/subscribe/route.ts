import { NextRequest, NextResponse } from 'next/server'
import { checkRateLimit, clientIp } from '@/lib/rate-limit'

const SUBSCRIBE_LIMIT = 5
const SUBSCRIBE_WINDOW_MS = 15 * 60 * 1000

// POST /api/subscribe — adaugă contact în Brevo (Sendinblue)
export async function POST(request: NextRequest) {
  try {
    const ip = clientIp(request)
    const rl = checkRateLimit(`subscribe:${ip}`, SUBSCRIBE_LIMIT, SUBSCRIBE_WINDOW_MS)
    if (!rl.ok) {
      return NextResponse.json(
        { error: 'Prea multe cereri. Încearcă din nou mai târziu.' },
        { status: 429, headers: { 'Retry-After': String(rl.retryAfterSec) } }
      )
    }

    const body = await request.json()
    const { nume, email, magazin, gdpr_consent, consented_at, website } = body

    // Honeypot: clientul real nu vede acest câmp; botii îl completează → silent OK
    if (typeof website === 'string' && website.trim().length > 0) {
      return NextResponse.json({ success: true })
    }

    if (!email || !nume) {
      return NextResponse.json(
        { error: 'Numele și emailul sunt obligatorii' },
        { status: 400 }
      )
    }

    // Validare email format (server-side)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'Format email invalid' },
        { status: 400 }
      )
    }

    const apiKey = process.env.BREVO_API_KEY
    const listId = Number(process.env.BREVO_LIST_ID) || 2

    // Dacă nu avem cheie Brevo, logăm și returnăm succes (pentru development)
    if (!apiKey || apiKey === 'your-brevo-api-key-here') {
      console.log('[DEV] Abonare email:', { nume, email, magazin })
      return NextResponse.json({ success: true, dev: true })
    }

    // Trimite contactul la Brevo API
    const brevoRes = await fetch('https://api.brevo.com/v3/contacts', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'api-key': apiKey,
      },
      body: JSON.stringify({
        email,
        attributes: {
          FIRSTNAME: nume,
          MAGAZIN_PREFERAT: magazin || 'toate',
          GDPR_CONSENT: gdpr_consent ? 'yes' : 'no',
          CONSENT_DATE: consented_at || new Date().toISOString(),
        },
        listIds: [listId],
        updateEnabled: true,
      }),
    })

    if (!brevoRes.ok) {
      const errData = await brevoRes.json()
      // Contact deja existent — tratăm ca succes
      if (errData.code === 'duplicate_parameter') {
        return NextResponse.json({ success: true, existing: true })
      }
      console.error('Brevo error:', errData)
      return NextResponse.json(
        { error: 'Eroare la procesarea abonării. Încearcă din nou.' },
        { status: 500 }
      )
    }

    console.log(`[SUBSCRIBE] ${new Date().toISOString()} | ${email} | magazin: ${magazin || 'toate'} | gdpr: ${gdpr_consent}`)
    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Subscribe error:', error)
    return NextResponse.json(
      { error: 'Eroare server. Încearcă din nou.' },
      { status: 500 }
    )
  }
}
