@echo off
cd /d "C:\Users\ovidi\OneDrive\Desktop\GHIDULREDUCERILOR.RO"
git add .github/workflows/daily-pipeline.yml
git commit -m "fix: git add public/images/ in daily pipeline (image_repair local downloads)"
git push
