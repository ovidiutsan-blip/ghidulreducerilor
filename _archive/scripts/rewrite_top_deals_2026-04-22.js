#!/usr/bin/env node
/**
 * Task #9 — P2.5 Re-scriere top 24 descrieri oferte (2026-04-22)
 *
 * Pentru fiecare deal din PATCH:
 *  - `titlu_original` = titlul scraped (preservat pentru traceability)
 *  - `titlu` + `title` = titlu SEO curat (Title Case, brand + categorie)
 *  - `descriere` = meta-friendly ~130-160 char, include long-tail "reducere [magazin] 2026"
 *
 * Run: node scripts/rewrite_top_deals_2026-04-22.js
 */
const fs = require('fs');
const path = require('path');

const DEALS_PATH = path.join(__dirname, '..', 'data', 'deals.json');

const PATCH = {
  'watch24-6f8ca269': {
    titlu: 'Ceas damă Rotate Dial AA-5',
    descriere: 'Ceas damă quartz Rotate Dial AA-5 cu disc rotativ, reducere 75% pe watch24 în 2026 — de la 100 lei la 25 lei, livrare rapidă.',
  },
  'watch24-33b29aaa': {
    titlu: 'Ceas bărbătesc Curren Superslim auriu-alb',
    descriere: 'Ceas Curren Superslim pentru bărbați, carcasă slim auriu-alb, reducere 70% pe watch24 în 2026 — de la 200 lei la 59 lei.',
  },
  'ps-streamstore-licenta-autocad-architecture-2023-2026-f-72504370': {
    titlu: 'Licență AutoCAD Architecture 2023-2026, 1 dispozitiv, Windows/MacOS',
    descriere: 'Licență AutoCAD Architecture 2023-2026 Full pentru 1 dispozitiv Windows sau MacOS, reducere 67% pe streamstore 2026 — software CAD profesional la 329 lei.',
  },
  'ps-alecoair-resigilat-umidificator-cu-ultrasunete-du-1-DXHU12': {
    titlu: 'Umidificator Duux Beam Mini 2 Black WiFi (resigilat)',
    descriere: 'Umidificator ultrasunete Duux Beam Mini 2 Black WiFi, resigilat, pentru 30 mp, reducere 65% pe AlecoAir 2026 — de la 697 lei la 247 lei.',
  },
  'ps-streamstore-licenta-autocad-architecture-2023-2026-f-72504270': {
    titlu: 'Licență AutoCAD Architecture 2023-2026, 1 dispozitiv (Student Edition)',
    descriere: 'Licență AutoCAD Architecture 2023-2026 Student Edition pentru 1 dispozitiv, reducere 65% pe streamstore 2026 — 123 lei de la 349 lei, Windows/MacOS.',
  },
  'ps-hiris-salvatore-ferragamo-signorina-libera-apa-46674': {
    titlu: 'Salvatore Ferragamo Signorina Libera EDP 30ml + loțiune corp 50ml',
    descriere: 'Parfum Salvatore Ferragamo Signorina Libera EDP 30ml + loțiune corp 50ml, reducere 59% pe Hiris 2026 — set beauty femei la 189 lei.',
  },
  'ps-alecoair-resigilat-umidificator-cu-ultrasunete-du-1-DXHU13': {
    titlu: 'Umidificator Duux Beam Mini 2 White WiFi (resigilat)',
    descriere: 'Umidificator ultrasunete Duux Beam Mini 2 White WiFi, resigilat, pentru 30 mp, reducere 59% pe AlecoAir 2026 — 288 lei față de 699 lei.',
  },
  'vegis-24fbf972': {
    titlu: 'Pachet 2× Cremă de fistic 20%, fără gluten, 180g',
    descriere: 'Pachet duo cremă de fistic 20% fără gluten 180g + 180g, reducere 52% pe Vegis 2026 — de la 93 lei la 44,64 lei pentru aport proteic sănătos.',
  },
  'vegis-fd2fc7cb': {
    titlu: 'Bere Bundaberg cu ghimbir și scorțișoară, fără alcool, 375ml',
    descriere: 'Bere artizanală Bundaberg cu ghimbir și scorțișoară, fără alcool, 375ml, reducere 50% pe Vegis 2026 — 6,94 lei, aromă premium din Australia.',
  },
  'vegis-abc302d5': {
    titlu: 'Cremă de fistic 20%, fără gluten, 180g',
    descriere: 'Cremă de fistic natural 20% fără gluten 180g, reducere 50% pe Vegis 2026 — 23 lei față de 46 lei, perfectă pentru mic dejun sănătos.',
  },
  'ps-hiris-parfum-de-camera-rituals-amsterdam-colle-46669': {
    titlu: 'Parfum de cameră Rituals Amsterdam Dutch Tulip & Yuzu 70ml',
    descriere: 'Parfum de cameră Rituals Amsterdam Collection Dutch Tulip & Yuzu 70ml, reducere 47% pe Hiris 2026 — aromă premium pentru casă la 90 lei.',
  },
  'ps-techstar-membrana-cauciuc-pad-2-butoane-pentru-ch-4303': {
    titlu: 'Membrană cauciuc cheie auto Smart Fortwo/City/Roadster, 2 butoane, portocalie',
    descriere: 'Membrană cauciuc pentru cheie auto Smart Fortwo/City/Roadster, 2 butoane portocalie, reducere 46% pe Techstar 2026 — piesă schimb la 10,72 lei.',
  },
  'forit-e381a8bd': {
    titlu: 'Aspirator vertical fără fir R20 Ultra AquaCycle VRV57F-AC (funcție mop)',
    descriere: 'Aspirator vertical fără fir R20 Ultra cu funcție mop, filtru HEPA, rezervor 0,6L, reducere 44% pe Forit 2026 — 1368 lei față de 2426 lei.',
  },
  'ps-mathaus-set-masina-de-gaurit-si-insurubat-cu-per-11195522': {
    titlu: 'Set Hyundai HD20X-60TT + șurubelniță impact brushless IW20X-350Nm, 2 acumulatori 20V',
    descriere: 'Set bricolaj Hyundai: mașină găurit HD20X-60TT + șurubelniță impact IW20X-350Nm brushless, 2 acumulatori 20V, reducere 39% pe MatHaus 2026 la 825 lei.',
  },
  'emag-38c90fab': {
    titlu: 'Telefon OPPO Reno13 Pro 5G, Dual SIM, 12GB RAM, 512GB, Graphite Grey',
    descriere: 'Telefon OPPO Reno13 Pro 5G Dual SIM 12GB/512GB Graphite Grey, reducere 38% pe eMAG 2026 — de la 3863 lei la 2411 lei, flagship OPPO 2026.',
  },
  'ps-mathaus-set-masina-de-gaurit-si-insurubat-cu-per-11195523': {
    titlu: 'Set Hyundai HD20X-60TT + fierăstrău pendular JS20S-24, acumulatori 20V',
    descriere: 'Set Hyundai mașină găurit HD20X-60TT + fierăstrău pendular JS20S-24 cu acumulatori 20V, reducere 38% pe MatHaus 2026 — 743 lei de la 1190 lei.',
  },
  'ps-mathaus-set-masina-de-gaurit-si-insurubat-cu-per-11195520': {
    titlu: 'Set Hyundai HD20X-60TT + șurubelniță impact ID20S-180Nm, 2 acumulatori 20V',
    descriere: 'Set Hyundai: mașină găurit HD20X-60TT + șurubelniță impact ID20S-180Nm, 2 acumulatori 20V, reducere 37% pe MatHaus 2026 la 660 lei.',
  },
  'ps-hotpick-resigilat-aparat-de-sandwich-2-in-1-domo- DO1106C': {
    titlu: 'Aparat sandwich Domo DO1106C, 2 în 1, plăci interschimbabile, 750W (resigilat)',
    descriere: 'Aparat de sandwich Domo DO1106C 2 în 1 cu plăci interschimbabile pentru sandwich sau waffles, 750W, resigilat, reducere 36% pe Hotpick 2026 la 128 lei.',
  },
  'ps-novodoors-usa-metalica-de-apartament-cu-izolatie-s-EN88ORDR': {
    titlu: 'Ușă metalică apartament Novo Doors First Class NDS31, 200×88 cm, Wenge',
    descriere: 'Ușă metalică apartament Novo Doors First Class NDS31 cu izolație și vizor, 200×88 cm, finisaj wenge, reducere 34% pe Novodoors 2026 — 1486 lei, kit complet.',
  },
  'ps-novodoors-usa-metalica-de-apartament-cu-izolatie-s-ID88ORDR': {
    titlu: 'Ușă metalică apartament Novo Doors First Class NDS32, 200×88 cm, Gri deschis',
    descriere: 'Ușă metalică Novo Doors First Class NDS32 cu izolație și vizor, 200×88 cm, gri deschis, reducere 34% pe Novodoors 2026 — 1486 lei, kit complet inclus.',
  },
  'forit-a735f1f3': {
    titlu: 'Aspirator robot X50 Ultra Complete RLX85CE-4-WH, AI, 20.000 Pa',
    descriere: 'Aspirator robot X50 Ultra Complete cu detectare AI, navigare 360°, aspirare 20.000 Pa, depășire obstacole 6 cm, reducere 33% pe Forit 2026 — 4585 lei.',
  },
  'emag-d5037f93': {
    titlu: 'Tabletă Philips 10.1", 6GB RAM, 128GB, gri',
    descriere: 'Tabletă Philips 10.1" cu 6GB RAM, 128GB stocare, greutate 491g, gri, reducere 32% pe eMAG 2026 — 428 lei pentru uz zilnic și streaming.',
  },
  'ps-case-smart-senzor-de-gaz-luxion-cu-wi-fi-control-ap--BG-GS01': {
    titlu: 'Senzor de gaz Luxion Wi-Fi, control din aplicație, alarmă 70 dB',
    descriere: 'Senzor de gaz Luxion cu Wi-Fi, control prin aplicație, alarmă 70 dB, reducere 31% pe Case-Smart 2026 — 95,80 lei, compatibil smart home.',
  },
  'ps-case-smart-modul-intrerupator-triplu-cu-touch-luxio--MT-R301': {
    titlu: 'Modul întrerupător triplu Luxion cu touch, RF433',
    descriere: 'Modul întrerupător triplu Luxion cu touch și RF433, reducere 31% pe Case-Smart 2026 — 102 lei, integrare smart home simplă.',
  },
};

const deals = JSON.parse(fs.readFileSync(DEALS_PATH, 'utf-8'));
let patched = 0, skipped = 0;
const now = new Date().toISOString();

for (const d of deals) {
  const p = PATCH[d.id];
  if (!p) continue;
  // preserve original
  if (!d.titlu_original) d.titlu_original = d.titlu;
  d.titlu = p.titlu;
  d.title = p.titlu;
  d.descriere = p.descriere;
  d.description = p.descriere;
  d.seo_rewritten_at = now;
  patched++;
}
for (const id of Object.keys(PATCH)) {
  if (!deals.find(d => d.id === id)) {
    console.warn('MISSING:', id);
    skipped++;
  }
}

fs.writeFileSync(DEALS_PATH, JSON.stringify(deals, null, 2) + '\n', 'utf-8');
console.log(`Patched ${patched} deals, ${skipped} missing IDs, ${deals.length} total.`);
