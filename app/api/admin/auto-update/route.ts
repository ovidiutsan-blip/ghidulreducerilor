import { NextRequest, NextResponse } from 'next/server'
import { isApiAuthorized } from '@/lib/admin-auth'
import path from 'path'
import fs from 'fs/promises'

const ROOT = process.cwd()

/**
 * GET /api/admin/auto-update — Latest auto-update status
 */
export async function GET(req: NextRequest) {
  if (!isApiAuthorized(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  try {
    const statusPath = path.join(ROOT, 'data', 'update_status.json')
    const content = await fs.readFile(statusPath, 'utf-8')
    return NextResponse.json(JSON.parse(content))
  } catch {
    return NextResponse.json({
      status: 'no_data',
      message: 'No update status found. The auto-update has not been run yet.'
    })
  }
}
