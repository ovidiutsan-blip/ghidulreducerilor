// Formatează prețul în lei românești
export function formatPrice(price: number): string {
  return new Intl.NumberFormat('ro-RO', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(price) + ' lei'
}

// Returnează luna și anul curent în română
export function getCurrentMonthYear(): string {
  const months = [
    'Ianuarie', 'Februarie', 'Martie', 'Aprilie', 'Mai', 'Iunie',
    'Iulie', 'August', 'Septembrie', 'Octombrie', 'Noiembrie', 'Decembrie',
  ]
  const now = new Date()
  return `${months[now.getMonth()]} ${now.getFullYear()}`
}

// Verifică dacă un cod promoțional este expirat
export function isExpired(dateString: string): boolean {
  return new Date(dateString) < new Date()
}

// Copiază text în clipboard
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}
