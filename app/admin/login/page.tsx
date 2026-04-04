'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function AdminLogin() {
  const [token, setToken] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const resp = await fetch('/api/admin/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token }),
      })

      if (resp.ok) {
        router.push('/admin')
      } else {
        setError('Token invalid')
      }
    } catch {
      setError('Eroare de conexiune')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="bg-[#1A2635] border border-[#2A3A50] rounded-2xl p-8">
          <h1 className="text-xl font-bold text-center mb-2">
            <span className="text-[#E63946]">Ghidul Reducerilor</span>
          </h1>
          <p className="text-sm text-[#7B92B2] text-center mb-6">Admin Panel</p>

          <form onSubmit={handleSubmit}>
            <label className="block text-xs text-[#7B92B2] uppercase tracking-wider mb-2">
              Admin Token
            </label>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              className="w-full px-4 py-3 bg-[#0F1923] border border-[#2A3A50] rounded-lg text-[#E8F0FE] placeholder-[#7B92B2] focus:border-[#E63946] focus:outline-none"
              placeholder="Introdu token-ul admin"
              required
            />

            {error && (
              <p className="text-[#E63946] text-sm mt-2">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-4 py-3 bg-[#E63946] hover:bg-[#c53030] text-white font-semibold rounded-lg transition-colors disabled:opacity-50"
            >
              {loading ? 'Se verifica...' : 'Autentificare'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
