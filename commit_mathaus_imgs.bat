@echo off
cd /d "C:\Users\ovidi\OneDrive\Desktop\GHIDULREDUCERILOR.RO"
git add public\images\mathaus\ data\deals.json
git commit -m "fix: mathaus product images downloaded locally (bypass CloudFlare CDN 403)"
git push origin main
echo EXIT_CODE=%ERRORLEVEL%
