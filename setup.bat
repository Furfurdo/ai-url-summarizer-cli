@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python not found. Please install Python 3.10 or newer.
  echo Download: https://www.python.org/downloads/
  echo.
  pause
  exit /b 1
)

python src\cli.py setup

echo.
pause
