param(
    [string[]]$Ids
)

if (-not $Ids) {
    Write-Output "No IDs provided"
    exit 0
}

$outDir = Join-Path (Get-Location) 'pr-logs'
New-Item -Path $outDir -ItemType Directory -Force | Out-Null

foreach ($idRaw in $Ids) {
    $id = [int64]$idRaw
    Write-Output "Fetching $id"
    gh run view $id --log > (Join-Path $outDir ("gh-run-$id.log"))
    $len = (Get-Item (Join-Path $outDir ("gh-run-$id.log"))).Length
    Write-Output "Size: $len"
}
