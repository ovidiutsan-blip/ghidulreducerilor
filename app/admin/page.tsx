'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'

// ═══════════════════════════════════════════════
// Types
// ══════���════════════��═══════════════════════════

interface SystemStatus {
  timestamp: string
  deals?: { total: number; active: number; broken_links: number; avg_discount: number }
  codes?: { total: number; active: number }
  logs?: Record<string, boolean>
  config?: Record<string, boolean>
  scripts?: Record<string, boolean>
  env?: { required?: Record<string, boolean>; optional?: Record<string, boolean> } | Record<string, boolean>
}

interface AuditReport {
  timestamp?: string
  score?: number
  summary?: { total_checks: number; pass: number; fail: number; warn: number; total_issues: number }
  checks?: Array<{ check: string; status: string; issues: string[] }>
  status?: string
}

interface UpdateStatus {
  ultima_actualizare?: string
  success?: boolean
  duration_s?: number
  audit_score?: number
  repairs_applied?: number
  links_ok?: number
  links_broken?: number
  status?: string
}

// ═══════���═══════════════════════════════════════
// Components
// ════════════════════════════���══════════════════

function KpiCard({ label, value, sub, color }: {
  label: string; value: string | number; sub: string; color: 'green' | 'red' | 'orange' | 'blue'
}) {
  const colorMap = {
    green: { bar: 'bg-[#2A9D8F]', text: 'text-[#2A9D8F]' },
    red: { bar: 'bg-[#E63946]', text: 'text-[#E63946]' },
    orange: { bar: 'bg-[#F4A261]', text: 'text-[#F4A261]' },
    blue: { bar: 'bg-[#4A9EFF]', text: 'text-[#4A9EFF]' },
  }
  const c = colorMap[color]

  return (
    <div className="bg-[#1A2635] border border-[#2A3A50] rounded-xl p-5 relative overflow-hidden">
      <div className={`absolute top-0 left-0 right-0 h-[3px] ${c.bar}`} />
      <div className="text-xs text-[#7B92B2] uppercase tracking-wider mb-2">{label}</div>
      <div className={`text-3xl font-extrabold ${c.text}`}>{value}</div>
      <div className="text-xs text-[#7B92B2] mt-1">{sub}</div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pass: 'bg-[rgba(42,157,143,0.2)] text-[#2A9D8F]',
    fail: 'bg-[rgba(230,57,70,0.2)] text-[#E63946]',
    warn: 'bg-[rgba(244,162,97,0.2)] text-[#F4A261]',
    skip: 'bg-[rgba(123,146,178,0.2)] text-[#7B92B2]',
  }
  const labels: Record<string, string> = {
    pass: 'PASS', fail: 'FAIL', warn: 'WARN', skip: 'SKIP',
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${styles[status] || styles.skip}`}>
      {labels[status] || status}
    </span>
  )
}

// ═══════════════════════════════════════════════
// Main Dashboard
// ═══════════════════════════════════════════════

export default function AdminDashboard() {
  const router = useRouter()
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [auditReport, setAuditReport] = useState<AuditReport | null>(null)
  const [updateStatus, setUpdateStatus] = useState<UpdateStatus | null>(null)
  const [logMessages, setLogMessages] = useState<Array<{ type: string; msg: string; time: string }>>([])

  const log = useCallback((type: string, msg: string) => {
    setLogMessages(prev => [...prev.slice(-50), {
      type,
      msg,
      time: new Date().toLocaleTimeString('ro-RO')
    }])
  }, [])

  const apiFetch = useCallback(async (url: string) => {
    const resp = await fetch(url)
    if (resp.status === 401) {
      router.push('/admin/login')
      return null
    }
    return resp.json()
  }, [router])

  // Load all data
  const loadData = useCallback(async () => {
    try {
      const [status, audit, update] = await Promise.all([
        apiFetch('/api/admin/status'),
        apiFetch('/api/admin/audit'),
        apiFetch('/api/admin/auto-update'),
      ])
      if (status) setSystemStatus(status)
      if (audit) setAuditReport(audit)
      if (update) setUpdateStatus(update)
      log('ok', 'Date incarcate cu succes')
    } catch {
      log('err', 'Eroare la incarcarea datelor — verificati autentificarea')
      router.push('/admin/login')
    }
  }, [apiFetch, log, router])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 60000)
    return () => clearInterval(interval)
  }, [loadData])

  async function handleLogout() {
    await fetch('/api/admin/auth', { method: 'DELETE' })
    router.push('/admin/login')
  }

  const deals = systemStatus?.deals
  const auditScore = auditReport?.score ?? updateStatus?.audit_score ?? '—'

  return (
    <>
      {/* HEADER */}
      <header className="bg-[#1D3557] px-6 py-4 flex items-center justify-between border-b-2 border-[#E63946]">
        <h1 className="text-lg font-bold">
          <span className="text-[#E63946]">Ghidul Reducerilor</span> — Control Panel
        </h1>
        <div className="flex items-center gap-3">
          <span className="bg-[#2A9D8F] text-white px-3 py-1 rounded-full text-xs font-semibold">
            Sistem activ
          </span>
          <button onClick={handleLogout} className="text-xs text-[#7B92B2] hover:text-white">
            Logout
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-6">

        {/* KPI CARDS */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <KpiCard
            label="Oferte Active"
            value={deals?.active ?? '—'}
            sub={`din ${deals?.total ?? '?'} total`}
            color="green"
          />
          <KpiCard
            label="Scor Audit"
            value={auditScore !== '—' ? `${auditScore}/100` : '—'}
            sub={auditReport?.timestamp ? `Ultimul: ${new Date(auditReport.timestamp).toLocaleDateString('ro-RO')}` : 'Niciun audit'}
            color="blue"
          />
          <KpiCard
            label="Linkuri Rupte"
            value={deals?.broken_links ?? updateStatus?.links_broken ?? '—'}
            sub="Necesita atentie"
            color="orange"
          />
          <KpiCard
            label="Reparatii Aplicate"
            value={updateStatus?.repairs_applied ?? '—'}
            sub="Ultima actualizare"
            color="red"
          />
        </div>

        {/* ACTIONS — runs in GitHub Actions, not from this dashboard */}
        <div className="bg-[#1A2635] border border-[#2A3A50] rounded-xl mb-6 p-5 text-sm text-[#7B92B2]">
          <p className="mb-2">
            <span className="text-[#E8F0FE] font-semibold">Pipeline-ul rulează în GitHub Actions.</span>
          </p>
          <p>
            Audit-ul, auto-update, link-check și auto-repair sunt declanșate din workflow-ul{' '}
            <code className="text-[#4A9EFF]">.github/workflows/daily-pipeline.yml</code> (zilnic, 06:00 RO).
            Vezi rezultatele în GitHub → tab Actions.
          </p>
        </div>

        {/* TWO-COLUMN PANELS */}
        <div className="grid md:grid-cols-2 gap-5 mb-6">

          {/* UPDATE STATUS */}
          <div className="bg-[#1A2635] border border-[#2A3A50] rounded-xl">
            <div className="px-5 py-4 border-b border-[#2A3A50] font-bold text-sm">
              Status Auto-Update
            </div>
            <div className="p-5 space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-[#7B92B2]">Ultima actualizare:</span>
                <span className="font-semibold">
                  {updateStatus?.ultima_actualizare
                    ? new Date(updateStatus.ultima_actualizare).toLocaleString('ro-RO')
                    : 'Niciodata'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#7B92B2]">Status:</span>
                <span className={updateStatus?.success ? 'text-[#2A9D8F]' : 'text-[#E63946]'}>
                  {updateStatus?.success === undefined ? '—' : updateStatus.success ? 'Succes' : 'Erori'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#7B92B2]">Durata:</span>
                <span>{updateStatus?.duration_s ? `${updateStatus.duration_s}s` : '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#7B92B2]">Linkuri OK / Rupte:</span>
                <span>
                  <span className="text-[#2A9D8F]">{updateStatus?.links_ok ?? '—'}</span>
                  {' / '}
                  <span className="text-[#E63946]">{updateStatus?.links_broken ?? '—'}</span>
                </span>
              </div>
            </div>
          </div>

          {/* AUDIT RESULTS */}
          <div className="bg-[#1A2635] border border-[#2A3A50] rounded-xl">
            <div className="px-5 py-4 border-b border-[#2A3A50] font-bold text-sm">
              Rezultate Audit
            </div>
            <div className="p-5">
              {auditReport?.checks ? (
                <div className="space-y-2">
                  {auditReport.checks.map((check) => (
                    <div key={check.check} className="flex items-center justify-between text-sm">
                      <span>{check.check}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-[#7B92B2] text-xs">{check.issues.length} issues</span>
                        <StatusBadge status={check.status} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[#7B92B2] text-sm text-center py-4">
                  Niciun audit rulat. Apasa &quot;Audit Complet&quot;.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* ENVIRONMENT STATUS */}
        <div className="bg-[#1A2635] border border-[#2A3A50] rounded-xl mb-6">
          <div className="px-5 py-4 border-b border-[#2A3A50] font-bold text-sm">
            Status Sistem
          </div>
          <div className="p-5 grid md:grid-cols-3 gap-6 text-sm">
            {/* Scripts */}
            <div>
              <h3 className="text-xs text-[#7B92B2] uppercase tracking-wider mb-2">Scripturi Python</h3>
              {systemStatus?.scripts ? Object.entries(systemStatus.scripts).map(([name, exists]) => (
                <div key={name} className="flex justify-between py-1">
                  <span className="text-[#7B92B2]">{name}</span>
                  <span className={exists ? 'text-[#2A9D8F]' : 'text-[#E63946]'}>
                    {exists ? 'OK' : 'LIPSA'}
                  </span>
                </div>
              )) : <span className="text-[#7B92B2]">Se incarca...</span>}
            </div>

            {/* Config */}
            <div>
              <h3 className="text-xs text-[#7B92B2] uppercase tracking-wider mb-2">Fisiere Config</h3>
              {systemStatus?.config ? Object.entries(systemStatus.config).map(([name, exists]) => (
                <div key={name} className="flex justify-between py-1">
                  <span className="text-[#7B92B2]">{name}</span>
                  <span className={exists ? 'text-[#2A9D8F]' : 'text-[#E63946]'}>
                    {exists ? 'OK' : 'LIPSA'}
                  </span>
                </div>
              )) : <span className="text-[#7B92B2]">Se incarca...</span>}
            </div>

            {/* Env Vars */}
            <div>
              <h3 className="text-xs text-[#7B92B2] uppercase tracking-wider mb-2">Variabile Mediu</h3>
              {systemStatus?.env ? (() => {
                const env = systemStatus.env
                // Support both old flat format and new required/optional format
                const required = (env as any).required || {}
                const optional = (env as any).optional || {}
                const hasGroups = Object.keys(required).length > 0 || Object.keys(optional).length > 0

                if (!hasGroups) {
                  // Flat format fallback
                  return Object.entries(env).map(([name, set]) => (
                    <div key={name} className="flex justify-between py-1">
                      <span className="text-[#7B92B2]">{name}</span>
                      <span className={set ? 'text-[#2A9D8F]' : 'text-[#F4A261]'}>
                        {set ? 'SET' : 'LIPSA'}
                      </span>
                    </div>
                  ))
                }

                return (
                  <>
                    {Object.entries(required).map(([name, set]) => (
                      <div key={name} className="flex justify-between py-1">
                        <span className="text-[#7B92B2]">{name}</span>
                        <span className={set ? 'text-[#2A9D8F]' : 'text-[#E63946]'}>
                          {set ? 'SET' : 'LIPSA'}
                        </span>
                      </div>
                    ))}
                    {Object.keys(optional).length > 0 && (
                      <>
                        <div className="text-[10px] text-[#7B92B2] uppercase tracking-wider mt-3 mb-1 opacity-60">Optional (social media)</div>
                        {Object.entries(optional).map(([name, set]) => (
                          <div key={name} className="flex justify-between py-1 opacity-60">
                            <span className="text-[#7B92B2]">{name}</span>
                            <span className={set ? 'text-[#2A9D8F]' : 'text-[#7B92B2]'}>
                              {set ? 'SET' : 'N/A'}
                            </span>
                          </div>
                        ))}
                      </>
                    )}
                  </>
                )
              })() : <span className="text-[#7B92B2]">Se incarca...</span>}
            </div>
          </div>
        </div>

        {/* LOG */}
        <div className="bg-[#1A2635] border border-[#2A3A50] rounded-xl">
          <div className="px-5 py-4 border-b border-[#2A3A50] flex items-center justify-between">
            <span className="font-bold text-sm">Log Sistem</span>
            <button
              onClick={() => setLogMessages([])}
              className="text-xs text-[#7B92B2] hover:text-white px-2 py-1 bg-[#2A3A50] rounded"
            >
              Curata
            </button>
          </div>
          <div className="p-5">
            <div className="bg-[#0A0F15] rounded-lg p-4 font-mono text-xs h-48 overflow-y-auto">
              {logMessages.length === 0 && (
                <div className="text-[#4A9EFF]">[SISTEM] Dashboard pornit</div>
              )}
              {logMessages.map((msg, i) => {
                const colorMap: Record<string, string> = {
                  info: 'text-[#4A9EFF]', ok: 'text-[#2A9D8F]',
                  warn: 'text-[#F4A261]', err: 'text-[#E63946]',
                }
                return (
                  <div key={i} className={colorMap[msg.type] || 'text-[#4A9EFF]'}>
                    [{msg.time}] {msg.msg}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

      </div>
    </>
  )
}
