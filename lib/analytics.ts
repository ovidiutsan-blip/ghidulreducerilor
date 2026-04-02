// GA4 event tracking helpers

declare global {
  interface Window {
    gtag?: (...args: any[]) => void
  }
}

function track(eventName: string, params: Record<string, any> = {}) {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', eventName, params)
  }
}

export function trackOfferClick(dealId: string, magazin: string, titlu: string, pretRedus: number, reducere: number) {
  track('offer_click', {
    item_id: dealId,
    item_name: titlu,
    item_brand: magazin,
    price: pretRedus,
    discount: reducere,
  })
}

export function trackVoucherCopy(codeId: string, magazin: string, cod: string) {
  track('voucher_copy', {
    item_id: codeId,
    item_brand: magazin,
    coupon: cod,
  })
}

export function trackNewsletterSubscribe(source: string) {
  track('newsletter_subscribe', { source })
}

export function trackStoreView(magazin: string) {
  track('store_view', { item_brand: magazin })
}
