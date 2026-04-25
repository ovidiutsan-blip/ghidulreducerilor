# setup_fb_scheduler.ps1 — Înregistrează un task Windows pentru postare automată Facebook
#
# Rulează O SINGURĂ DATĂ cu drepturi de administrator:
#   powershell -ExecutionPolicy Bypass -File scripts\setup_fb_scheduler.ps1
#
# Ce face task-ul:
#   - Se execută zilnic la 08:30 (după ce pipeline-ul 04:00 UTC a generat posturile)
#   - Rulează facebook_poster.py --run
#   - Log în logs/fb_poster/scheduler.log

$RepoRoot   = "C:\dev\ghidulreducerilor.ro"
$PythonExe  = "C:\Python314\python.exe"   # cale fixă detectată automat
$ScriptPath = "$RepoRoot\agents\marketing\facebook_poster.py"
$LogPath    = "$RepoRoot\logs\fb_poster\scheduler.log"
$TaskName   = "GhidulReducerilor_FB_Poster"

# ─── Verificări ───────────────────────────────────────────────────────────────

if (-not $PythonExe) {
    # Fallback la căi comune
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "C:\Python311\python.exe",
        "C:\Python312\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $PythonExe = $c; break }
    }
}

if (-not $PythonExe) {
    Write-Error "Python nu a fost găsit. Instalează Python și asigură-te că e în PATH."
    exit 1
}

Write-Host "Python: $PythonExe"
Write-Host "Script: $ScriptPath"

# ─── Creare director log ───────────────────────────────────────────────────────
$LogDir = Split-Path $LogPath
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

# ─── Definire task ────────────────────────────────────────────────────────────

$Action  = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$ScriptPath`" --run >> `"$LogPath`" 2>&1" `
    -WorkingDirectory $RepoRoot

$Trigger = New-ScheduledTaskTrigger -Daily -At "08:30AM"

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

# ─── Înregistrare (sau actualizare dacă există deja) ──────────────────────────

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Task existent șters."
}

Register-ScheduledTask `
    -TaskName  $TaskName `
    -Action    $Action `
    -Trigger   $Trigger `
    -Settings  $Settings `
    -Principal $Principal `
    -Description "Postează automat în grupuri Facebook pentru ghidulreducerilor.ro" | Out-Null

Write-Host ""
Write-Host "✅ Task '$TaskName' înregistrat cu succes!"
Write-Host "   Rulare: zilnic la 08:30"
Write-Host "   Log:    $LogPath"
Write-Host ""
Write-Host "Comenzi utile:"
Write-Host "  Verifică task:   Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Rulează acum:    Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Șterge task:     Unregister-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "IMPORTANT: Rulează mai întâi setup-ul:"
Write-Host "  python agents\marketing\facebook_poster.py --setup"
