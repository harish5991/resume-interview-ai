@echo off
REM Resume Interview AI — 1-Click Startup Script (Windows)

echo ==================================================
echo  Starting Resume Interview AI on Windows...
echo ==================================================

REM 1. Activate virtualenv if present
if exist ".venv\Scripts\activate.bat" (
    echo Activating .venv virtual environment...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo Activating venv virtual environment...
    call venv\Scripts\activate.bat
)

REM 2. Determine python command
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PY_CMD=python"
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "PY_CMD=py"
    ) else (
        echo.
        echo ❌ Python is not found in your PATH.
        echo Please install Python 3.10+ and check the "Add Python to PATH" option.
        pause
        exit /b 1
    )
)

REM 3. Run Universal Launcher
%PY_CMD% run.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ An error occurred during startup or execution.
    pause
)
