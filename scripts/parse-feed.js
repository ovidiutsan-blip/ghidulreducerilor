#!/usr/bin/env node
/**
 * Parser feed XML Profitshare → merge în data/deals.json
 *
 * Detectează automat fișiere .xml din data/feeds/ și le procesează.
 * Generează linkuri de afiliere prin API pentru URL-urile din feed.
 *
 * Usage:
 *   npm run sync:feed
 *   node scripts/parse-feed.js
 */

const path = require('path')
const fs = require('fs')

// Load .env
const envPath = path.join(__dirname, '..', '.env')
if (fs.existsSync(envPath)) {
  fs.readFileSync(envPath, 'utf-8').split('\n').forEach(line => {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) return
    const eqIndex = trimmed.indexOf('=')
    if (eqIndex === -1) return
    const key = trimmed.substring(0, eqIndex).trim()
    const value = trimmed.substring(eqIndex + 1).trim()
    if (!process.env[key]) process.env[key] = value
  })
}

const { ProfitshareClient } = require('../lib/profitshare-client')

const FEEDS_DIR = path.join(__dirname, '..', 'data', 'feeds')
const DEALS_PATH = path.join(__dirname, '..', 'data', 'deals.json')
const BATCH_SIZE = 10

function slugify(text) {
  return text.toString().normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 80)
}

function calcDiscount(original, reduced) {
  if (!original || original <= reduced) return 0
  return Math.round(((original - reduced) / original) * 100)
}

/**
 * Simple XML parser — extracts product items from Profitshare feed XML
 * Handles <product> or <item> elements with common child tags
 */
function parseXmlProducts(xmlContent) {
  const products = []
  // Match <product>...</product> or <item>...</item> blocks
  const itemRegex = /<(?:product|item)\b[^>]*>([\s\S]*?)<\/(?:product|item)>/gi
  let match

  while ((match = itemRegex.exec(xmlContent)) !== null) {
    const block = match[1]
    const get = (tag) => {
      const tagMatch = block.match(new RegExp(`<${tag}[^>]*>(?:<!\\[CDATA\\[)?(.*?)(?:\\]\\]>)?<\\/${tag}>`, 'is'))
      return tagMatch ? tagMatch[1].trim() : ''
    }

    products.push({
      name: get('name') || get('title') || get('product_name'),
      price: get('price') || get('price_new'),
      old_price: get('old_price') || get('price_old') || get('original_price'),
      product_url: get('url') || get('product_url') || get('link'),
      image_url: get('image') || get('image_url') || get('picture') || get('img'),
      category: get('category') || get('category_name'),
      id: get('id') || get('product_id'),
      availability: get('availability') || get('stock') || 'in stock',
      advertiser: get('advertiser') || get('shop') || get('merchant'),
    })
  }

  return products.filter(p => p.name && p.product_url)
}

async function main() {
  console.log('📄 Profitshare Feed Parser\n')

  // Check if feeds directory exists
  if (!fs.existsSync(FEEDS_DIR)) {
    console.log(`   ⚠️  Directorul ${FEEDS_DIR} nu există.`)
    console.log('   Creează data/feeds/ și adaugă fișiere .xml de la Profitshare.')
    fs.mkdirSync(FEEDS_DIR, { recursive: true })
    console.log('   ✅ Directorul data/feeds/ a fost creat.')
    process.exit(0)
  }

  // Find XML files
  const xmlFiles = fs.readdirSync(FEEDS_DIR).filter(f => f.endsWith('.xml'))

  if (xmlFiles.length === 0) {
    console.log('   ⚠️  Niciun fișier .xml găsit în data/feeds/')
    console.log('   Descarcă un feed XML din dashboard Profitshare → Feed-uri de produse.')
    process.exit(0)
  }

  console.log(`   Găsite ${xmlFiles.length} fișiere XML.\n`)

  // Initialize API client for link generation
  const apiUser = process.env.PROFITSHARE_API_USER
  const apiKey = process.env.PROFITSHARE_API_KEY
  let client = null
  if (apiUser && apiKey) {
    client = new ProfitshareClient(apiUser, apiKey)
  } else {
    console.log('   ⚠️  Credentiale API lipsesc — linkurile nu vor fi generate.')
    console.log('   Produsele vor folosi URL-ul original din feed.\n')
  }

  const today = new Date().toISOString().split('T')[0]
  let allFeedDeals = []

  for (const xmlFile of xmlFiles) {
    const filePath = path.join(FEEDS_DIR, xmlFile)
    console.log(`📦 Procesez: ${xmlFile}`)

    const xmlContent = fs.readFileSync(filePath, 'utf-8')
    const products = parseXmlProducts(xmlContent)
    console.log(`   ${products.length} produse extrase.`)

    if (products.length === 0) continue

    // Generate affiliate links if client available
    const linkMap = new Map()
    if (client) {
      const linksToGenerate = products
        .filter(p => p.product_url && !p.product_url.includes('profitshare.ro'))
        .map((p, i) => ({ name: `feed-${i}`, url: p.product_url }))

      for (let i = 0; i < linksToGenerate.length; i += BATCH_SIZE) {
        const batch = linksToGenerate.slice(i, i + BATCH_SIZE)
        try {
          const results = await client.generateAffiliateLinks(batch)
          if (Array.isArray(results)) {
            results.forEach(r => {
              const psUrl = (r.ps_url || r.affiliate_url || '')
                .replace('http://profitshare.ro', 'https://profitshare.ro')
              if (psUrl) {
                const orig = batch.find(b => b.name === r.name)
                if (orig) linkMap.set(orig.url, psUrl)
              }
            })
          }
        } catch (err) {
          console.error(`   ❌ Eroare linkuri batch: ${err.message}`)
        }
        if (i + BATCH_SIZE < linksToGenerate.length) {
          await new Promise(r => setTimeout(r, 500))
        }
      }
      console.log(`   🔗 ${linkMap.size} linkuri de afiliere generate.`)
    }

    // Build deal objects
    const feedName = xmlFile.replace('.xml', '')
    products.forEach(prod => {
      const original = parseFloat(prod.old_price || prod.price || 0)
      const reduced = parseFloat(prod.price || 0)
      const advSlug = slugify(prod.advertiser || feedName)

      allFeedDeals.push({
        id: `feed-${advSlug}-${prod.id || slugify(prod.name).substring(0, 20)}`,
        slug: slugify(prod.name),
        magazin: advSlug,
        titlu: prod.name,
        pret_original: original > reduced ? original : reduced,
        pret_redus: reduced,
        procent_reducere: calcDiscount(original > reduced ? original : reduced, reduced),
        imagine_url: prod.image_url,
        product_url: prod.product_url,
        link_afiliat: linkMap.get(prod.product_url) || prod.product_url,
        categorie: prod.category || 'general',
        data_adaugare: today,
        activ: prod.availability !== 'out of stock',
      })
    })
  }

  allFeedDeals = allFeedDeals.filter(d => d.titlu && d.pret_redus > 0)
  console.log(`\n📊 Total produse din feed-uri: ${allFeedDeals.length}`)

  // Merge with existing deals.json
  let existingDeals = []
  if (fs.existsSync(DEALS_PATH)) {
    try {
      existingDeals = JSON.parse(fs.readFileSync(DEALS_PATH, 'utf-8'))
    } catch {
      console.log('   ⚠️  deals.json invalid.')
    }
  }

  // Remove old feed deals, keep everything else
  const nonFeedDeals = existingDeals.filter(d => !d.id.startsWith('feed-'))
  const finalDeals = [...nonFeedDeals, ...allFeedDeals]

  fs.writeFileSync(DEALS_PATH, JSON.stringify(finalDeals, null, 2), 'utf-8')

  console.log(`\n✅ Salvat ${DEALS_PATH}`)
  console.log(`   📦 Total: ${finalDeals.length} produse (${allFeedDeals.length} din feed-uri)`)
}

main().catch(err => {
  console.error('❌ Eroare fatală:', err.message)
  process.exit(1)
})
