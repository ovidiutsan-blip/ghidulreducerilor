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
  Sparkles,
  Tag,
  RotateCcw,
  type LucideIcon,
} from 'lucide-react'

export type Category = {
  slug: string
  label: string
  icon: LucideIcon
  emoji: string
}

// Sincronizat cu valorile efective din deals.json (`getAllCategories()`).
// Orice slug nou care apare în deals trebuie adăugat aici, altfel
// `/categorie/[slug]` va returna 404 deși pagina e SSG-generată.
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
  { slug: 'beauty', label: 'Beauty', icon: Sparkles, emoji: '💄' },
  { slug: 'promotii', label: 'Promotii', icon: Tag, emoji: '🏷️' },
  { slug: 'resigilate', label: 'Resigilate', icon: RotateCcw, emoji: '📦' },
]

export function getCategoryBySlug(slug: string): Category | undefined {
  return CATEGORIES.find(c => c.slug === slug)
}

export const FAST_DELIVERY_STORES = ['emag']
