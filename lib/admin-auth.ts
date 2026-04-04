import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'

const COOKIE_NAME = 'admin_session'
const COOKIE_MAX_AGE = 60 * 60 * 24 // 24 hours

/**
 * Verify admin token against env variable.
 */
export function verifyAdminToken(token: string): boolean {
  const secret = process.env.ADMIN_SECRET_TOKEN
  if (!secret) return false
  return token === secret
}

/**
 * Check if request has valid admin session (cookie-based, for pages).
 */
export async function isAdminAuthenticated(): Promise<boolean> {
  const cookieStore = await cookies()
  const session = cookieStore.get(COOKIE_NAME)
  if (!session?.value) return false
  return verifyAdminToken(session.value)
}

/**
 * Check if API request is authorized (header or cookie).
 */
export function isApiAuthorized(req: NextRequest): boolean {
  // Check header first (for API calls from scripts)
  const headerToken = req.headers.get('x-admin-token')
  if (headerToken && verifyAdminToken(headerToken)) return true

  // Check cookie (for dashboard UI)
  const cookieToken = req.cookies.get(COOKIE_NAME)?.value
  if (cookieToken && verifyAdminToken(cookieToken)) return true

  return false
}

/**
 * Create admin session response with cookie.
 */
export function createSessionResponse(token: string): NextResponse {
  const resp = NextResponse.json({ success: true })
  resp.cookies.set(COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: COOKIE_MAX_AGE,
    path: '/'
  })
  return resp
}

/**
 * Create logout response (clear cookie).
 */
export function createLogoutResponse(): NextResponse {
  const resp = NextResponse.json({ success: true })
  resp.cookies.delete(COOKIE_NAME)
  return resp
}
