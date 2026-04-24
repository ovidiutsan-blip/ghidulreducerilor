@echo off
cd /d "C:\Users\ovidi\OneDrive\Desktop\GHIDULREDUCERILOR.RO"
git add app/page.tsx app/reduceri/magazin/page.tsx app/categorii/slug/page.tsx components/MobileBottomNav.tsx components/DealOfTheDay.tsx app/globals.css
git add -A
git commit -m "feat: mobile-first responsive fixes (7 issues)"
git push
