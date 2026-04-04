import { NextRequest, NextResponse } from 'next/server'
import { isApiAuthorized } from '@/lib/admin-auth'
import path from 'path'
import fs from 'fs/promises'

const ROOT = process.cwd()

/**
 * GET /api/admin/audit — Latest audit report
 */
export async function GET(req: NextRequest) {
  if (!isApiAuthorized(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const latestPath = path.join(ROOT, 'logs', 'audit_full_latest.json')
    const content = await fs.readFile(latestPath, 'utf-8')
    return NextResponse.json(JSON.parse(content))
  } catch {
    return NextResponse.json({
      status: 'no_report',
      message: 'No audit report found. Run: python scripts/audit_full.py'
    })
  }
}
