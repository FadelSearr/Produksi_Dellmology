Set-Location 'C:\IDX_Analyst'
Write-Host 'Dispatching pr-monitor workflow...'
gh workflow run .github/workflows/pr-monitor.yml --ref feat/roadmap-core-infra-2026-03-09 --field pr_number=11
Write-Host 'Waiting 5s for run to be registered...'
Start-Sleep -Seconds 5
$rJson = gh run list --workflow='pr-monitor.yml' --branch 'feat/roadmap-core-infra-2026-03-09' --limit 1 --json databaseId,createdAt
if (-not $rJson) {
    Write-Host 'No run JSON returned'; exit 1
}
$r = $rJson | ConvertFrom-Json
$id = $r.databaseId
Write-Host "Latest run: $id"
& 'C:\IDX_Analyst\scripts\poll_and_download.ps1' -RunId $id -MaxAttempts 120 -SleepSeconds 10
