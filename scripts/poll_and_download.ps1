param(
    [int64]$RunId = 22875372029,
    [int]$MaxAttempts = 120,
    [int]$SleepSeconds = 10
)

Set-Location 'C:\IDX_Analyst'
Write-Host "Polling run $RunId (up to $MaxAttempts attempts, $SleepSeconds s interval)..."
$attempt = 0
$info = $null
while ($attempt -lt $MaxAttempts) {
    $attempt++
    $infoJson = gh run view $RunId --json status,conclusion 2>$null
    if (-not $infoJson) {
        Write-Host "gh CLI returned no info (attempt $attempt), retrying..."
        Start-Sleep -Seconds 5
        continue
    }
    $info = $infoJson | ConvertFrom-Json
    Write-Host ('Attempt {0}: status={1} conclusion={2}' -f $attempt, $info.status, $info.conclusion)
    if ($info.status -eq 'in_progress' -or $info.status -eq 'queued' -or $info.status -eq 'requested') {
        Start-Sleep -Seconds $SleepSeconds
        continue
    }
    break
}

if (-not $info) { Write-Host 'Failed to retrieve run info'; exit 1 }
Write-Host 'Final run info:'
$info | Format-List

if ($info.status -ne 'completed') { Write-Host 'Run did not complete in time'; exit 0 }

$outDir = "pr-logs-artifacts-$RunId"
Write-Host ('Downloading artifacts to {0}...' -f $outDir)
gh run download $RunId -D $outDir
if ($LASTEXITCODE -ne 0) { Write-Host 'gh run download failed'; exit 1 }

Write-Host 'Downloaded artifact files:'
Get-ChildItem $outDir -Recurse | Select-Object FullName,Length | Format-Table -AutoSize

$tgz = Get-ChildItem $outDir -Filter 'pr-logs-*.tar.gz' -Recurse | Select-Object -First 1
if ($tgz) {
    $extractDir = Join-Path $outDir 'extracted'
    mkdir $extractDir -Force | Out-Null
    Write-Host "Extracting $($tgz.FullName) to $extractDir"
    tar -xzf $tgz.FullName -C $extractDir
    Write-Host 'Extracted contents:'
    Get-ChildItem $extractDir -Recurse | Select-Object FullName,Length | Format-Table -AutoSize
} else {
    Write-Host 'No pr-logs tar.gz artifact found; done.'
}
