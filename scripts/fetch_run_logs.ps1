param(
    [int]$PrNumber = 11,
    [int]$Limit = 200
)

$prInfo = gh pr view $PrNumber --json headRefName 2>$null
if (-not $prInfo) {
    Write-Output "PR not found or gh CLI failed."
    exit 0
}
$headBranch = (ConvertFrom-Json $prInfo).headRefName
if (-not $headBranch) {
    Write-Output "Could not determine head branch for PR #$PrNumber."
    exit 0
}
Write-Output "Head branch: $headBranch"

$runsJson = gh run list --branch $headBranch --limit $Limit --json databaseId,conclusion,workflowName,headBranch 2>$null
if (-not $runsJson) {
    Write-Output "No runs found for branch $headBranch."
    exit 0
}

$runs = $runsJson | ConvertFrom-Json
$failed = $runs | Where-Object { $_.conclusion -ne 'success' -and $_.conclusion -ne $null }
if (-not $failed) {
    Write-Output "No failed runs for PR #$PrNumber."
    exit 0
}

$outDir = Join-Path -Path (Get-Location) -ChildPath "pr-logs"
New-Item -Path $outDir -ItemType Directory -Force | Out-Null

foreach ($r in $failed) {
    $id = $r.databaseId
    $wf = $r.workflowName -replace '[\\/:*?""<>|]','_'
    Write-Output "Saving logs for $id ($wf)"
    gh run view $id --log > (Join-Path $outDir ("gh-run-$id.log"))
    Start-Sleep -Milliseconds 200
}

Write-Output "--- Files saved ---"
Get-ChildItem $outDir | Select-Object Name,Length | Sort-Object Length -Descending | Format-Table -AutoSize
