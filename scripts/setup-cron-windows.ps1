# Setup Windows Task Scheduler — Sync Profitshare zilnic la 06:00
#
# Rulează ca Administrator:
#   powershell -ExecutionPolicy Bypass -File scripts\setup-cron-windows.ps1

$TaskName = "SyncProfitshare_GhidulReducerilor"
$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$LogDir = Join-Path $ProjectDir "logs"
$ScriptPath = Join-Path $ProjectDir "scripts\sync-profitshare.js"
$NodePath = (Get-Command node -ErrorAction SilentlyContinue).Source

if (-not $NodePath) {
    Write-Host "❌ Node.js nu este instalat sau nu e in PATH!" -ForegroundColor Red
    exit 1
}

# Creează directorul logs dacă nu există
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
    Write-Host "✅ Creat directorul: $LogDir"
}

# Construieste comanda cu logging
$DateFormat = 'yyyy-MM-dd'
$LogFile = "$LogDir\sync-$(Get-Date -Format $DateFormat).log"
$Action = New-ScheduledTaskAction `
    -Execute $NodePath `
    -Argument "`"$ScriptPath`" >> `"$LogDir\sync-%date:~0,10%.log`" 2>&1" `
    -WorkingDirectory $ProjectDir

# Trigger: zilnic la 06:00
$Trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM

# Settings
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

# Înregistrare task
try {
    # Șterge task-ul vechi dacă există
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description "Sincronizare zilnica produse Profitshare -> ghidulreducerilor.ro" `
        -RunLevel Highest

    Write-Host ""
    Write-Host "✅ Task Scheduler configurat cu succes!" -ForegroundColor Green
    Write-Host "   Task: $TaskName"
    Write-Host "   Trigger: Zilnic la 06:00"
    Write-Host "   Script: $ScriptPath"
    Write-Host "   Logs: $LogDir\sync-YYYY-MM-DD.log"
    Write-Host ""
    Write-Host "Pentru a rula manual:"
    Write-Host "   Start-ScheduledTask -TaskName '$TaskName'"
} catch {
    Write-Host "❌ Eroare la creare task: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternativ, rulează manual zilnic:"
    Write-Host "   cd $ProjectDir"
    Write-Host "   npm run sync:profitshare"
}
