const STORAGE_KEY = 'ghidulreducerilor_recent'
const MAX_ITEMS = 10

export function getRecentlyViewed(): string[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function addRecentlyViewed(dealId: string): void {
  if (typeof window === 'undefined') return
  try {
    const current = getRecentlyViewed().filter(id => id !== dealId)
    current.unshift(dealId)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(current.slice(0, MAX_ITEMS)))
  } catch {}
}
