@echo off
py --version
py -c "import sys; print(sys.executable)"
py -c "from playwright.sync_api import sync_playwright; print('playwright OK')"
