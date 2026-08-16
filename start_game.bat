@echo off
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Game crashed. Press any key to close...
    pause
)