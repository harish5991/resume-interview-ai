@echo off
REM Resume Interview AI — 1-Click Startup Script (Windows)

echo ==================================================
echo  Starting Resume Interview AI on Windows...
echo ==================================================

python run.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ An error occurred while starting. Please ensure Python and Node.js are in your PATH.
    pause
)
