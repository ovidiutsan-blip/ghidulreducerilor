import { Metadata } from 'next'
import Breadcrumb from '@/components/Breadcrumb'

export const metadata: Metadata = {
  title: 'Despre GhidulReducerilor.ro',
  description: 'Cine suntem, cum funcționează site-ul și politica de confidențialitate.',
  alternates: { canonical: '/despre' },
}

export default function DesprePage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Breadcrumb items={[{ label: 'Despre noi' }]} />

      <h1 className="font-display font-extrabold text-3xl sm:text-4xl text-neutral-900 mb-8">
        Despre GhidulReducerilor.ro
      </h1>

      <div className="prose prose-neutral max-w-none">
        <h2>Ce este GhidulReducerilor.ro?</h2>
        <p>
          GhidulReducerilor.ro este un site independent care strânge cele mai bune reduceri
          și coduri promoționale din România. Verificăm zilnic ofertele de la magazinele
          partenere pentru a-ți oferi doar reduceri reale și active.
        </p>

        <h2>Cum funcționează?</h2>
        <p>
          Căutăm și verificăm manual cele mai bune oferte de la magazine precum eMAG, Altex,
          Fashion Days și altele. Când găsim o reducere bună, o adăugăm pe site cu toate
          detaliile: preț original, preț redus și link direct către ofertă.
        </p>

        <h2>Cum ne susținem?</h2>
        <p>
          Acest site conține <strong>linkuri de afiliere</strong> prin rețeaua{' '}
          <a href="https://www.profitshare.ro" target="_blank" rel="noopener noreferrer">Profitshare.ro</a>.
          Asta înseamnă că, atunci când cumperi un produs prin link-urile de pe site-ul nostru,
          primim un comision mic de la magazin (între 2% și 15%, în funcție de produs).
        </p>
        <p>
          <strong>Important:</strong> Acest comision NU îți crește prețul. Plătești exact același
          preț ca și cum ai fi intrat direct pe site-ul magazinului. Este doar o modalitate prin
          care magazinele ne mulțumesc că le-am trimis un client.
        </p>

        <h2 id="confidentialitate">Politica de Confidențialitate</h2>
        <p>
          Respectăm confidențialitatea datelor tale personale conform Regulamentului General
          privind Protecția Datelor (GDPR).
        </p>

        <h3>Ce date colectăm</h3>
        <ul>
          <li><strong>Formularul de alerte email:</strong> Numele și adresa de email, doar dacă
          te abonezi voluntar. Aceste date sunt stocate în platforma Brevo (fostul Sendinblue)
          și sunt folosite exclusiv pentru a-ți trimite alerte cu reduceri.</li>
          <li><strong>Google Analytics:</strong> Colectăm date anonime despre trafic (pagini vizitate,
          dispozitiv, țară) pentru a îmbunătăți site-ul. Nu colectăm date cu caracter personal prin Analytics.</li>
        </ul>

        <h3>Drepturile tale</h3>
        <ul>
          <li>Poți solicita ștergerea datelor tale oricând prin email</li>
          <li>Te poți dezabona de la alertele email printr-un singur click</li>
          <li>Poți solicita o copie a datelor pe care le deținem despre tine</li>
        </ul>

        <h3>Contact</h3>
        <p>
          Pentru orice întrebări legate de datele tale personale sau funcționarea site-ului,
          ne poți contacta la adresa de email disponibilă în secțiunea de contact.
        </p>

        <h2>Disclaimer</h2>
        <p>
          Prețurile și disponibilitatea produselor se pot modifica fără notificare prealabilă.
          Verifică întotdeauna prețul final pe site-ul magazinului înainte de a plasa o comandă.
          GhidulReducerilor.ro nu este responsabil pentru tranzacțiile efectuate pe site-urile
          magazinelor partenere.
        </p>
      </div>
    </div>
  )
}
