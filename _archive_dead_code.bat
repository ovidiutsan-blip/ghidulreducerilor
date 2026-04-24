@echo off
set GIT=C:\Program Files\Git\cmd\git.exe
set ROOT=C:\Users\ovidi\OneDrive\Desktop\GHIDULREDUCERILOR.RO

echo === Arhivare dead code ===

md "%ROOT%\_archive\agents\merchants" 2>nul
md "%ROOT%\_archive\scripts" 2>nul

echo Mutare agents...
"%GIT%" -C "%ROOT%" mv agents/orchestrator.py _archive/agents/orchestrator.py
"%GIT%" -C "%ROOT%" mv agents/fix_vegis_via_ogimage.py _archive/agents/fix_vegis_via_ogimage.py
"%GIT%" -C "%ROOT%" mv agents/fix_vegis_retry.py _archive/agents/fix_vegis_retry.py
"%GIT%" -C "%ROOT%" mv agents/fix_vegis_images.py _archive/agents/fix_vegis_images.py
"%GIT%" -C "%ROOT%" mv agents/fix_retry_broken.py _archive/agents/fix_retry_broken.py
"%GIT%" -C "%ROOT%" mv agents/fix_remaining_images.py _archive/agents/fix_remaining_images.py
"%GIT%" -C "%ROOT%" mv agents/fix_all_broken_images.py _archive/agents/fix_all_broken_images.py
"%GIT%" -C "%ROOT%" mv agents/ps_scan_v2.py _archive/agents/ps_scan_v2.py
"%GIT%" -C "%ROOT%" mv agents/ps_scan_v3.py _archive/agents/ps_scan_v3.py
"%GIT%" -C "%ROOT%" mv agents/ps_scan_candidates.py _archive/agents/ps_scan_candidates.py
"%GIT%" -C "%ROOT%" mv agents/ps_probe_vegis_image.py _archive/agents/ps_probe_vegis_image.py
"%GIT%" -C "%ROOT%" mv agents/probe_vegis_urls.py _archive/agents/probe_vegis_urls.py
"%GIT%" -C "%ROOT%" mv agents/probe_hiris.py _archive/agents/probe_hiris.py
"%GIT%" -C "%ROOT%" mv agents/probe_all_hosts.py _archive/agents/probe_all_hosts.py
"%GIT%" -C "%ROOT%" mv agents/audit_live_images.py _archive/agents/audit_live_images.py

echo Mutare merchants probes...
"%GIT%" -C "%ROOT%" mv agents/merchants/_probe_streamstore.py _archive/agents/merchants/_probe_streamstore.py
"%GIT%" -C "%ROOT%" mv agents/merchants/_probe_casesmart.py _archive/agents/merchants/_probe_casesmart.py
"%GIT%" -C "%ROOT%" mv agents/merchants/_live_audit_all.py _archive/agents/merchants/_live_audit_all.py
"%GIT%" -C "%ROOT%" mv agents/merchants/_audit_streamstore.py _archive/agents/merchants/_audit_streamstore.py

echo Mutare scripts one-off...
"%GIT%" -C "%ROOT%" mv "scripts/rewrite_top_deals_2026-04-22.js" "_archive/scripts/rewrite_top_deals_2026-04-22.js"

echo.
echo === Status dupa mutare ===
"%GIT%" -C "%ROOT%" status --short

echo.
echo === Commit ===
"%GIT%" -C "%ROOT%" commit -m "chore: archive dead code (orchestrator, fix_*, probe_*, ps_scan_v2/v3)"

echo Done.
