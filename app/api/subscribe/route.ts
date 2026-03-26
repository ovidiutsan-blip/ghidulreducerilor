import { NextRequest, NextResponse } from 'next/server'

// POST /api/subscribe — adaugă contact în Brevo (Sendinblue)
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { nume, email, magazin } = body

    if (!email || !nume) {
      return NextResponse.json(
        { error: 'Numele și emailul sunt obligatorii' },
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

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Subscribe error:', error)
    return NextResponse.json(
      { error: 'Eroare server. Încearcă din nou.' },
      { status: 500 }
    )
  }
}
