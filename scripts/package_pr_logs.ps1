Set-Location 'C:\IDX_Analyst'
if (-not (Test-Path .\pr-logs)) {
    Write-Host 'pr-logs not found'
    exit 1
}
$ts = Get-Date -Format yyyyMMdd-HHmmss
$out = "pr-logs-$ts.tar.gz"
Write-Host "Creating $out..."
tar -czf $out .\pr-logs
if ($LASTEXITCODE -ne 0) { Write-Host 'tar exited with code' $LASTEXITCODE; exit $LASTEXITCODE }
Write-Host 'Created.'
Get-Item $out | Select-Object FullName,Length
Write-Host '--- Archive contents (first 200 entries) ---'
tar -tzf $out | Select-Object -First 200
