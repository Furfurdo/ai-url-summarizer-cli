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

set /p URL=请输入文章链接: 
if "%URL%"=="" (
  echo 链接不能为空。
  echo.
  pause
  exit /b 1
)

python src\cli.py summarize "%URL%"

echo.
pause
