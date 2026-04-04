#!/usr/bin/env node
/**
 * Sincronizare produse Profitshare → data/deals.json
 *
 * Flux:
 *  1. Conectare API cu credentiale din .env
 *  2. Dacă PROFITSHARE_ADVERTISER_ID lipsește → afișează lista advertiseri, exit
 *  3. Extrage produse cu paginare automată (produsele vin cu affiliate_link inclus)
 *  4. Merge în data/deals.json (add/update/deactivate)
 *
 * Notă: API-ul returnează produse de la TOȚI advertiserii dacă nu se specifică filtru.
 *       eMAG nu are feed de produse — folosește scraper-ul separat pentru eMAG.
 *       Setează PROFITSHARE_ADVERTISER_ID=all pentru toți advertiserii.
 *
 * Usage:
 *   npm run sync:profitshare
 *   node scripts/sync-profitshare.js
 */

const path = require('path')
const fs = require('fs')

// Load .env from project root
;['.env', '.env.local'].forEach(envFile => {
  const p = path.join(__dirname, '..', envFile)
  if (fs.existsSync(p)) {
    fs.readFileSync(p, 'utf-8').split('\n').forEach(line => {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith('#')) return
      const eqIndex = trimmed.indexOf('=')
      if (eqIndex === -1) return
      const key = trimmed.substring(0, eqIndex).trim()
      const value = trimmed.substring(eqIndex + 1).trim()
      if (!process.env[key]) process.env[key] = value
    })
  }
})

const { ProfitshareClient } = require('../lib/profitshare-client')

const API_USER = process.env.PROFITSHARE_API_USER
const API_KEY = process.env.PROFITSHARE_API_KEY
const ADVERTISER_ID = process.env.PROFITSHARE_ADVERTISER_ID
const MAX_PAGES = parseInt(process.env.PROFITSHARE_MAX_PAGES || '50', 10)

const DEALS_PATH = path.join(__dirname, '..', 'data', 'deals.json')

// --- Helpers ---

function slugify(text) {
  return text
    .toString()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 80)
}

function calcDiscount(originalPrice, reducedPrice) {
  if (!originalPrice || originalPrice <= reducedPrice) return 0
  return Math.round(((originalPrice - reducedPrice) / originalPrice) * 100)
}

function advertiserSlug(name) {
  return slugify(name).replace(/-ro$/, '').replace(/-com$/, '')
}

function normalizeAffiliateLink(link) {
  if (!link) return ''
  // Ensure https protocol
  if (link.startsWith('//')) link = 'https:' + link
  return link.replace('http://profitshare.ro', 'https://profitshare.ro')
}

// --- Main ---

async function main() {
  console.log('🚀 Profitshare Sync — Node.js')
  console.log(`   API User: ${API_USER}`)
  console.log(`   API Key:  ${API_KEY ? API_KEY.substring(0, 8) + '...' : 'LIPSĂ!'}`)
  console.log()

  if (!API_USER || !API_KEY) {
    console.error('❌ Lipsesc credențialele Profitshare!')
    console.error('   Setează PROFITSHARE_API_USER și PROFITSHARE_API_KEY în .env')
    process.exit(1)
  }

  const client = new ProfitshareClient(API_USER, API_KEY)

  // Step 1: Test connection + get advertisers
  console.log('🔌 Test conexiune API...')
  let advertisers
  try {
    advertisers = await client.getAdvertisersList()
    console.log(`   ✅ Conectat! ${advertisers.length} advertiseri.\n`)
  } catch (err) {
    console.error(`   ❌ Eroare conexiune: ${err.message}`)
    process.exit(1)
  }

  // Step 2: If no ADVERTISER_ID, show list and exit
  if (!ADVERTISER_ID) {
    console.log('📋 Lista advertiseri cu produse disponibile:')
    console.log('─'.repeat(70))
    advertisers
      .filter(a => a.commissions?.affiliate_statuses?.approved === 'yes')
      .forEach(adv => {
        const status = adv.commissions?.affiliate_statuses?.active === 'yes' ? '✅' : '⏳'
        console.log(`   ${status} ID: ${String(adv.id).padEnd(8)} | ${adv.name} (${adv.category || ''})`)
      })
    console.log('─'.repeat(70))
    console.log('\n⚠️  Setează PROFITSHARE_ADVERTISER_ID în .env cu ID-ul dorit, apoi rerulează.')
    console.log('   Pentru toți advertiserii: PROFITSHARE_ADVERTISER_ID=all')
    console.log('   Pentru un singur magazin: PROFITSHARE_ADVERTISER_ID=165505')
    process.exit(0)
  }

  // Step 3: Get products with pagination
  // API returnează produse cu affiliate_link inclus
  const advFilter = ADVERTISER_ID === 'all' ? null : ADVERTISER_ID
  console.log(`📦 Extrag produse${advFilter ? ` pentru advertiser ID: ${advFilter}` : ' (toți advertiserii)'}...`)

  let allProducts = []
  let page = 1

  // First page to get total_pages
  let firstResult
  try {
    firstResult = await client.getProducts(advFilter, 1)
  } catch (err) {
    // eMAG and some advertisers don't have product feeds
    if (err.message.includes('InvalidAdvertisers')) {
      console.log(`   ⚠️  Advertiser-ul ${advFilter} nu oferă feed de produse prin API.`)
      console.log('   Opțiuni:')
      console.log('   1. Descarcă feed XML din dashboard Profitshare → Feed-uri de produse')
      console.log('   2. Pune fișierul XML în data/feeds/ și rulează: npm run sync:feed')
      console.log('   3. Setează PROFITSHARE_ADVERTISER_ID=all pentru toți advertiserii cu feed')
      process.exit(0)
    }
    throw err
  }

  const totalPages = Math.min(firstResult.totalPages, MAX_PAGES)
  allProducts = allProducts.concat(firstResult.products)
  console.log(`   Pagina 1/${totalPages}: ${firstResult.products.length} produse`)

  // Remaining pages
  for (page = 2; page <= totalPages; page++) {
    try {
      const result = await client.getProducts(advFilter, page)
      if (result.products.length === 0) break

      allProducts = allProducts.concat(result.products)
      console.log(`   Pagina ${page}/${totalPages}: ${result.products.length} produse (total: ${allProducts.length})`)

      // Delay between pages to respect rate limits
      await new Promise(r => setTimeout(r, 300))
    } catch (err) {
      console.error(`   ❌ Eroare pagina ${page}: ${err.message}`)
      break
    }
  }

  if (allProducts.length === 0) {
    console.log('   ⚠️  Niciun produs găsit.')
    process.exit(0)
  }

  console.log(`\n   ✅ Total: ${allProducts.length} produse extrase.\n`)

  // Step 4: Build deal objects
  // API-ul returnează deja affiliate_link — nu e nevoie de generare separată
  const today = new Date().toISOString().split('T')[0]

  const newDeals = allProducts.map(prod => {
    const productUrl = prod.link || ''
    const priceVat = parseFloat(prod.price_vat || 0)
    const price = parseFloat(prod.price || 0)
    const priceDiscounted = prod.price_discounted ? parseFloat(prod.price_discounted) : 0
    const imageUrl = prod.image_original || prod.image || ''
    const affiliateLink = normalizeAffiliateLink(prod.affiliate_link)
    const advSlug = advertiserSlug(prod.advertiser_name || 'unknown')
    const partNumber = prod.part_number || slugify(prod.name || '').substring(0, 20)

    // Determine prices: if there's a discounted price, use price_vat as original
    const pretOriginal = priceDiscounted > 0 ? priceVat : priceVat
    const pretRedus = priceDiscounted > 0 ? priceDiscounted : price

    return {
      id: `ps-${advSlug}-${partNumber}`,
      slug: slugify(prod.name || ''),
      magazin: advSlug,
      titlu: prod.name || '',
      pret_original: pretOriginal,
      pret_redus: pretRedus,
      procent_reducere: calcDiscount(pretOriginal, pretRedus),
      imagine_url: imageUrl,
      product_url: productUrl,
      link_afiliat: affiliateLink || productUrl,
      categorie: prod.category_name || 'general',
      data_adaugare: today,
      activ: true,
    }
  }).filter(d => d.titlu && d.pret_redus > 0 && d.link_afiliat)

  console.log(`📊 Produse valide construite: ${newDeals.length}`)

  // Step 5: Merge with existing deals.json
  let existingDeals = []
  if (fs.existsSync(DEALS_PATH)) {
    try {
      existingDeals = JSON.parse(fs.readFileSync(DEALS_PATH, 'utf-8'))
    } catch {
      console.log('   ⚠️  deals.json invalid, pornesc de la zero.')
    }
  }

  // Separate PS deals from non-PS deals
  const nonPsDeals = existingDeals.filter(d => !d.id.startsWith('ps-'))
  const oldPsDeals = existingDeals.filter(d => d.id.startsWith('ps-'))
  const oldPsMap = new Map(oldPsDeals.map(d => [d.id, d]))
  const newPsMap = new Map(newDeals.map(d => [d.id, d]))

  let added = 0
  let updated = 0
  let deactivated = 0

  const mergedPsDeals = []

  // Add new or update existing
  for (const deal of newDeals) {
    const old = oldPsMap.get(deal.id)
    if (!old) {
      mergedPsDeals.push(deal)
      added++
    } else if (old.pret_redus !== deal.pret_redus || old.pret_original !== deal.pret_original) {
      mergedPsDeals.push({ ...old, ...deal, data_adaugare: old.data_adaugare })
      updated++
    } else {
      mergedPsDeals.push({ ...old, activ: true })
    }
  }

  // Deactivate removed products
  for (const [id, old] of oldPsMap) {
    if (!newPsMap.has(id)) {
      if (old.activ) {
        mergedPsDeals.push({ ...old, activ: false })
        deactivated++
      } else {
        mergedPsDeals.push(old)
      }
    }
  }

  // Step 6: Save
  const finalDeals = [...nonPsDeals, ...mergedPsDeals]
  fs.writeFileSync(DEALS_PATH, JSON.stringify(finalDeals, null, 2), 'utf-8')

  console.log()
  console.log('─'.repeat(50))
  console.log('✅ Sincronizare completă!')
  console.log(`   ✓ ${added} adăugate`)
  console.log(`   ✓ ${updated} actualizate`)
  console.log(`   ✗ ${deactivated} dezactivate`)
  console.log(`   📁 Salvat: ${DEALS_PATH}`)
  console.log(`   📦 Total deals.json: ${finalDeals.length} produse`)
  console.log('─'.repeat(50))
}

main().catch(err => {
  console.error('❌ Eroare fatală:', err.message)
  process.exit(1)
})
