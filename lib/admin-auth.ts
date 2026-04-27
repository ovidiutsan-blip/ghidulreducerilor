import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'
import { createHmac, randomBytes, timingSafeEqual } from 'crypto'

const COOKIE_NAME = 'admin_session'
const COOKIE_MAX_AGE = 60 * 60 * 24 // 24 hours

function getSecret(): string | null {
  return process.env.ADMIN_SECRET_TOKEN || null
}

function timingSafeEqualString(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  return timingSafeEqual(Buffer.from(a), Buffer.from(b))
}

/**
 * Verify a raw admin token against ADMIN_SECRET_TOKEN with timing-safe comparison.
 * Used at login and for x-admin-token header (scripts).
 */
export function verifyAdminToken(token: string): boolean {
  const secret = getSecret()
  if (!secret) return false
  return timingSafeEqualString(token, secret)
}

function signSession(sessionId: string, secret: string): string {
  return createHmac('sha256', secret).update(sessionId).digest('base64url')
}

/**
 * Build a session cookie value: `<sessionId>.<HMAC-SHA256(sessionId, ADMIN_SECRET_TOKEN)>`.
 * The cookie never contains the secret itself.
 */
function createSessionCookieValue(): string | null {
  const secret = getSecret()
  if (!secret) return null
  const sessionId = randomBytes(32).toString('base64url')
  const signature = signSession(sessionId, secret)
  return `${sessionId}.${signature}`
}

function verifySessionCookieValue(cookieValue: string): boolean {
  const secret = getSecret()
  if (!secret) return false
  const dot = cookieValue.indexOf('.')
  if (dot <= 0) return false
  const sessionId = cookieValue.slice(0, dot)
  const signature = cookieValue.slice(dot + 1)
  if (!sessionId || !signature) return false
  const expected = signSession(sessionId, secret)
  return timingSafeEqualString(signature, expected)
}

/**
 * Check session cookie via Next.js cookies() helper. Used by server components / pages.
 */
export async function isAdminAuthenticated(): Promise<boolean> {
  const cookieStore = await cookies()
  const session = cookieStore.get(COOKIE_NAME)
  if (!session?.value) return false
  return verifySessionCookieValue(session.value)
}

/**
 * Authorize an API request — accepts either an `x-admin-token` header (raw secret, for
 * server-to-server scripts) or a signed session cookie (browser dashboard).
 */
export function isApiAuthorized(req: NextRequest): boolean {
  const headerToken = req.headers.get('x-admin-token')
  if (headerToken && verifyAdminToken(headerToken)) return true

  const sessionCookie = req.cookies.get(COOKIE_NAME)?.value
  if (sessionCookie && verifySessionCookieValue(sessionCookie)) return true

  return false
}

/**
 * Issue a signed session cookie after a successful login. Returns null if the secret
 * is missing (caller must respond with an error).
 */
export function createSessionResponse(): NextResponse | null {
  const value = createSessionCookieValue()
  if (!value) return null
  const resp = NextResponse.json({ success: true })
  resp.cookies.set(COOKIE_NAME, value, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: COOKIE_MAX_AGE,
    path: '/',
  })
  return resp
}

export function createLogoutResponse(): NextResponse {
  const resp = NextResponse.json({ success: true })
  resp.cookies.delete(COOKIE_NAME)
  return resp
}
