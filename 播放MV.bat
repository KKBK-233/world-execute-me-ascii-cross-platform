@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
if exist "dist\WorldExecuteMV\WorldExecuteMV.exe" (
    "dist\WorldExecuteMV\WorldExecuteMV.exe" %*
) else (
    if not exist ".venv\Scripts\python.exe" (
        echo Python environment not found. See README-Windows.md.
        pause
        exit /b 1
    )
    ".venv\Scripts\python.exe" "player.py" %*
)
if errorlevel 1 pause
