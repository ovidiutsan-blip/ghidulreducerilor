import { NextRequest, NextResponse } from 'next/server'
import { verifyAdminToken, createSessionResponse, createLogoutResponse } from '@/lib/admin-auth'

/**
 * POST /api/admin/auth — Login
 * Body: { token: "..." }
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const token = body?.token

    if (!token || typeof token !== 'string') {
      return NextResponse.json({ error: 'Token required' }, { status: 400 })
    }

    if (!verifyAdminToken(token)) {
      return NextResponse.json({ error: 'Invalid token' }, { status: 401 })
    }

    return createSessionResponse(token)
  } catch {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  }
}

/**
 * DELETE /api/admin/auth — Logout
 */
export async function DELETE() {
  return createLogoutResponse()
}
