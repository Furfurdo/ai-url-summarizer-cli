@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo 未检测到 Python，请先安装 Python 3.10 或更高版本。
  echo 下载地址: https://www.python.org/downloads/
  echo.
  pause
  exit /b 1
)

set /p INPUT=请输入链接文件路径（默认: examples\urls.txt）: 
if "%INPUT%"=="" set INPUT=examples\urls.txt

python src\cli.py batch "%INPUT%" --format markdown

echo.
pause
