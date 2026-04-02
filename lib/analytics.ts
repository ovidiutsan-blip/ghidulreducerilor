// Google Analytics 4 event tracking

function track(eventName: string, params: Record<string, any>) {
  if (typeof window !== 'undefined' && (window as any).gtag) {
    ;(window as any).gtag('event', eventName, params)
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
