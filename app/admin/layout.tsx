import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Admin — GhidulReducerilor.ro',
  robots: { index: false, follow: false },
}

/**
 * Admin layout hides the main site nav/footer via CSS.
 * This avoids refactoring the root layout into route groups.
 */
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {/* Hide main site chrome (Navbar, Footer, CookieConsent, SocialProof) */}
      <style dangerouslySetInnerHTML={{ __html: `
        body > nav.sticky, body > footer.bg-neutral-900 { display: none !important; }
        body > div[class*="fixed"] { display: none !important; }
        body { background: #0F1923 !important; }
        body > main { flex: none !important; padding: 0 !important; }
      ` }} />
      <div className="min-h-screen bg-[#0F1923] text-[#E8F0FE]">
        {children}
      </div>
    </>
  )
}
