@echo off
echo =========================================
echo   Stopping Perfume Visual Generator
echo =========================================
echo.
echo Stopping all Python processes...
taskkill /F /IM python.exe 2>nul
echo.
if %errorlevel%==0 (
    echo Server stopped successfully!
) else (
    echo No Python processes found.
)
echo.
echo =========================================
pause




