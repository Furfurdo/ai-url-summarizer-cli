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

echo Starting web app...
echo Open browser: http://127.0.0.1:7860

python -c "import flask" >nul 2>nul
if errorlevel 1 (
  echo Flask is missing. Run: pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)

python src\web_app.py --host 127.0.0.1 --port 7860

echo.
pause
