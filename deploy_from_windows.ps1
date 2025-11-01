# Deploy Perfume Visual Generator to Ubuntu VPS from Windows
# Server: 62.113.106.10

param(
    [string]$ServerIP = "62.113.106.10",
    [string]$ServerUser = "root"
)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  Deploying Perfume Visual Generator" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if SSH key exists
$sshKeyPath = "$env:USERPROFILE\.ssh\id_rsa"
if (-not (Test-Path $sshKeyPath)) {
    Write-Host "ERROR: SSH key not found at $sshKeyPath" -ForegroundColor Red
    Write-Host "Please generate SSH key first:" -ForegroundColor Yellow
    Write-Host "  ssh-keygen -t rsa -b 4096" -ForegroundColor Gray
    Write-Host "  ssh-copy-id $ServerUser@$ServerIP" -ForegroundColor Gray
    exit 1
}

Write-Host "Step 1: Testing SSH connection..." -ForegroundColor Yellow
$testConnection = ssh -o ConnectTimeout=5 -o BatchMode=yes "$ServerUser@$ServerIP" "echo 'Connection OK'" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Cannot connect to server" -ForegroundColor Red
    Write-Host "Please check:" -ForegroundColor Yellow
    Write-Host "  1. Server IP is correct: $ServerIP" -ForegroundColor Gray
    Write-Host "  2. SSH port 22 is open" -ForegroundColor Gray
    Write-Host "  3. SSH key is added: ssh-copy-id $ServerUser@$ServerIP" -ForegroundColor Gray
    exit 1
}

Write-Host "✓ SSH connection successful" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Copying deployment script to server..." -ForegroundColor Yellow
scp deploy_to_server.sh "${ServerUser}@${ServerIP}:/tmp/deploy_to_server.sh"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to copy deployment script" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Script copied successfully" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Running deployment on server..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor Gray
Write-Host ""

ssh "$ServerUser@$ServerIP" "chmod +x /tmp/deploy_to_server.sh && bash /tmp/deploy_to_server.sh"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Deployment failed!" -ForegroundColor Red
    Write-Host "Check the error messages above" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  ✓ Deployment Successful!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Application URL:" -ForegroundColor Cyan
Write-Host "  http://$ServerIP" -ForegroundColor White
Write-Host ""
Write-Host "To check logs:" -ForegroundColor Cyan
Write-Host "  ssh $ServerUser@$ServerIP" -ForegroundColor Gray
Write-Host "  tail -f /var/log/perfume-visual/error.log" -ForegroundColor Gray
Write-Host ""
Write-Host "To restart application:" -ForegroundColor Cyan
Write-Host "  ssh $ServerUser@$ServerIP" -ForegroundColor Gray
Write-Host "  supervisorctl restart perfume-visual" -ForegroundColor Gray
Write-Host ""

# Open browser
Write-Host "Opening application in browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
$url = "http://$ServerIP"
Start-Process $url

