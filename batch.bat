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

set /p INPUT=Input file path (default: examples\urls.txt): 
if "%INPUT%"=="" set INPUT=examples\urls.txt

python src\cli.py batch "%INPUT%" --format markdown

echo.
pause
