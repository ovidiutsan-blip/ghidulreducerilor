import {
  Laptop,
  Watch,
  Tablet,
  Headphones,
  Home,
  Cpu,
  Clock,
  Tv,
  Heart,
  type LucideIcon,
} from 'lucide-react'

export type Category = {
  slug: string
  label: string
  icon: LucideIcon
  emoji: string
}

export const CATEGORIES: Category[] = [
  { slug: 'laptopuri', label: 'Laptopuri', icon: Laptop, emoji: '💻' },
  { slug: 'smartwatch', label: 'Smartwatch', icon: Watch, emoji: '⌚' },
  { slug: 'tablete', label: 'Tablete', icon: Tablet, emoji: '📱' },
  { slug: 'casti', label: 'Casti', icon: Headphones, emoji: '🎧' },
  { slug: 'farmacie-sanatate', label: 'Sanatate', icon: Heart, emoji: '💊' },
  { slug: 'casa-gradina', label: 'Casa & Gradina', icon: Home, emoji: '🏠' },
  { slug: 'electronice', label: 'Electronice', icon: Cpu, emoji: '🔌' },
  { slug: 'ceasuri', label: 'Ceasuri', icon: Clock, emoji: '⏰' },
  { slug: 'televizoare', label: 'Televizoare', icon: Tv, emoji: '📺' },
]

export function getCategoryBySlug(slug: string): Category | undefined {
  return CATEGORIES.find(c => c.slug === slug)
}

export const FAST_DELIVERY_STORES = ['emag']
