import { NextRequest, NextResponse } from 'next/server'
import { verifyAdminToken, createSessionResponse, createLogoutResponse } from '@/lib/admin-auth'
import { checkRateLimit, clientIp } from '@/lib/rate-limit'

const LOGIN_LIMIT = 5
const LOGIN_WINDOW_MS = 15 * 60 * 1000

/**
 * POST /api/admin/auth — Login
 * Body: { token: "..." }
 */
export async function POST(req: NextRequest) {
  const ip = clientIp(req)
  const rl = checkRateLimit(`admin-auth:${ip}`, LOGIN_LIMIT, LOGIN_WINDOW_MS)
  if (!rl.ok) {
    return NextResponse.json(
      { error: 'Too many attempts' },
      { status: 429, headers: { 'Retry-After': String(rl.retryAfterSec) } }
    )
  }

  let token: unknown
  try {
    const body = await req.json()
    token = body?.token
  } catch {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  }

  if (!token || typeof token !== 'string') {
    return NextResponse.json({ error: 'Token required' }, { status: 400 })
  }

  if (!verifyAdminToken(token)) {
    return NextResponse.json({ error: 'Invalid token' }, { status: 401 })
  }

  const resp = createSessionResponse()
  if (!resp) {
    return NextResponse.json({ error: 'Server misconfigured' }, { status: 500 })
  }
  return resp
}

/**
 * DELETE /api/admin/auth — Logout
 */
export async function DELETE() {
  return createLogoutResponse()
}
