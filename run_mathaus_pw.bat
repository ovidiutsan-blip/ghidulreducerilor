@echo off
cd /d "C:\Users\ovidi\OneDrive\Desktop\GHIDULREDUCERILOR.RO"
C:\Python314\python.exe -c "from playwright.sync_api import sync_playwright; print('playwright check OK')"
C:\Python314\python.exe scripts\fix_mathaus_playwright.py
echo EXIT_CODE=%ERRORLEVEL%
