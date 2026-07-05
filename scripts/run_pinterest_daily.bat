@echo off
REM Rulat de Task Scheduler (task: GhidulReducerilor_Pinterest) zilnic la 12:37.
REM Trage întâi ultimele deal-uri din repo, apoi postează pin-urile zilei.
REM Agentul are fereastră de postare 12-22 și se oprește singur în afara ei.
cd /d C:\dev\ghidulreducerilor.ro
if not exist logs\pinterest mkdir logs\pinterest
echo. >> logs\pinterest\task_scheduler.log
echo ===== %date% %time% ===== >> logs\pinterest\task_scheduler.log
git pull --ff-only >> logs\pinterest\task_scheduler.log 2>&1
C:\Python314\python.exe agents\marketing\pinterest_agent.py --run >> logs\pinterest\task_scheduler.log 2>&1
