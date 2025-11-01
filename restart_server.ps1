Set-Location "C:\CURSOR\PARFUME VISUAL"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Restarting Perfume Visual Generator" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Stopping running server..." -ForegroundColor Yellow

# Find and kill Python processes running app.py
$stopped = $false
Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    $process = $_
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($process.Id)").CommandLine
        if ($cmdLine -like "*app.py*") {
            Write-Host "  Stopping process $($process.Id)..." -ForegroundColor Yellow
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            $stopped = $true
        }
    } catch {
        # Ignore errors
    }
}

if (-not $stopped) {
    Write-Host "  No running server found" -ForegroundColor Gray
}

Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Starting server..." -ForegroundColor Green
Write-Host ""

# Start server in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\CURSOR\PARFUME VISUAL'; python app.py"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Server restarted!" -ForegroundColor Green
Write-Host "Opening browser in 3 seconds..." -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Cyan

Start-Sleep -Seconds 3
Start-Process "http://localhost:8080"

Write-Host ""
Write-Host "Done! Server is running." -ForegroundColor Green
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")




