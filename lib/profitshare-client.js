/**
 * Profitshare API Client — Node.js
 *
 * Autentificare HMAC-SHA1 conform documentației Profitshare.
 * Base URL: http://api.profitshare.ro
 */

const crypto = require('crypto')
const https = require('https')
const MAX_RETRIES = 3
const RETRY_DELAY_MS = 1000

class ProfitshareClient {
  constructor(apiUser, apiKey) {
    if (!apiUser || !apiKey) {
      throw new Error('ProfitshareClient: apiUser și apiKey sunt obligatorii')
    }
    this.apiUser = apiUser
    this.apiKey = apiKey
  }

  /**
   * Construiește headerele de autentificare HMAC-SHA1
   * Semnătura: METHOD + endpoint + '/?' + queryString + '/' + api_user + date
   */
  _buildAuth(method, endpoint, queryString = '') {
    const date = new Date().toUTCString()
    const signatureString = `${method}${endpoint}?${queryString}/${this.apiUser}${date}`
    const auth = crypto
      .createHmac('sha1', this.apiKey)
      .update(signatureString)
      .digest('hex')

    return {
      'Date': date,
      'X-PS-Client': this.apiUser,
      'X-PS-Accept': 'json',
      'X-PS-Auth': auth,
      'Content-Type': 'application/x-www-form-urlencoded',
    }
  }

  /**
   * Execută un request HTTP cu retry logic
   */
  async _request(method, endpoint, queryString = '', body = '') {
    let lastError

    for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
      try {
        const headers = this._buildAuth(method, endpoint, queryString)
        const path = `/${endpoint}?${queryString}`
        const result = await this._httpRequest(method, path, headers, body)
        return result
      } catch (err) {
        lastError = err
        if (attempt < MAX_RETRIES) {
          console.log(`  Retry ${attempt}/${MAX_RETRIES} pentru ${endpoint}...`)
          await new Promise(r => setTimeout(r, RETRY_DELAY_MS))
        }
      }
    }

    throw lastError
  }

  /**
   * Low-level HTTP request (Node.js built-in)
   */
  _httpRequest(method, path, headers, body) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: 'api.profitshare.ro',
        port: 443,
        path,
        method,
        headers,
        timeout: 30000,
      }

      const req = https.request(options, (res) => {
        let data = ''
        res.on('data', chunk => { data += chunk })
        res.on('end', () => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            try {
              resolve(JSON.parse(data))
            } catch {
              resolve(data)
            }
          } else {
            reject(new Error(`API ${res.statusCode}: ${data.substring(0, 500)}`))
          }
        })
      })

      req.on('error', reject)
      req.on('timeout', () => {
        req.destroy()
        reject(new Error('Request timeout'))
      })

      if (body) {
        req.write(body)
      }
      req.end()
    })
  }

  /**
   * GET /affiliate-advertisers/ — Lista advertiseri activi
   */
  async getAdvertisersList() {
    const data = await this._request('GET', 'affiliate-advertisers/', '')
    const result = data.result || data
    // API returns object {id: {...}, id: {...}} — convert to array
    if (result && !Array.isArray(result)) {
      return Object.values(result)
    }
    return result
  }

  /**
   * GET /affiliate-products/ — Produse de la un advertiser
   * @param {string|number} advertiserIds - ID advertiser (sau comma-separated)
   * @param {number} page - Pagina (default 1)
   */
  async getProducts(advertiserIds, page = 1) {
    const qs = advertiserIds
      ? `filters[advertiser]=${advertiserIds}&page=${page}`
      : `page=${page}`
    const data = await this._request('GET', 'affiliate-products/', qs)
    const result = data.result || data
    return {
      currentPage: result.current_page || page,
      totalPages: result.total_pages || 0,
      products: result.products || [],
    }
  }

  /**
   * POST /affiliate-links/ — Generare linkuri de afiliere
   * @param {Array<{name: string, url: string}>} links - [{name, url}]
   * @returns {Array<{name: string, url: string, ps_url: string}>}
   */
  async generateAffiliateLinks(links) {
    const params = new URLSearchParams()
    links.forEach((link, i) => {
      params.append(`${i}[name]`, link.name)
      params.append(`${i}[url]`, link.url)
    })

    const body = params.toString()
    const data = await this._request('POST', 'affiliate-links/', '', body)
    return data.result || data
  }
}

module.exports = { ProfitshareClient }
