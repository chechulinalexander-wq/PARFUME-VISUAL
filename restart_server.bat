@echo off
cd "C:\CURSOR\PARFUME VISUAL"
echo =========================================
echo   Restarting Perfume Visual Generator
echo =========================================
echo.
echo Stopping running server...

REM Kill any Python process running app.py
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr /B "PID"') do (
    wmic process where "ProcessId=%%i AND CommandLine LIKE '%%app.py%%'" delete 2>nul
)

REM Fallback - kill all Python processes
taskkill /F /IM python.exe 2>nul

timeout /t 2 /nobreak >nul
echo.
echo Starting server...
echo.
start "Perfume Visual Server" python app.py
echo.
echo =========================================
echo Server restarted!
echo Opening browser...
echo =========================================
timeout /t 3 /nobreak >nul
start http://localhost:8080




