Set-Location 'C:\IDX_Analyst'
$base = 'pr-logs-artifacts-22875372029\extracted\pr-logs'
$outFile = 'pr_summary.txt'
if (-not (Test-Path $base)) {
    'No extracted pr-logs found' | Out-File $outFile -Encoding utf8
    exit 0
}

$out = New-Object System.Collections.Generic.List[string]
$folders = Get-ChildItem $base -Directory
$out.Add('Extracted pr-logs summary')
$out.Add('Folders found: ' + $folders.Count)
foreach ($f in $folders) {
    $files = Get-ChildItem $f.FullName -Recurse -File -ErrorAction SilentlyContinue
    $count = $files.Count
    $total = ($files | Measure-Object Length -Sum).Sum
    $out.Add('- Folder: ' + $f.Name + ' — files: ' + $count + ', total_bytes: ' + $total)
    $top = $files | Sort-Object Length -Descending | Select-Object -First 5
    foreach ($t in $top) { $out.Add('    * ' + $t.FullName + ' — ' + $t.Length + ' bytes') }
    $mm = Join-Path $f.FullName 'model_metrics\model_metrics.json'
    if (Test-Path $mm) {
        $out.Add('    model_metrics.json:')
        $out.Add((Get-Content $mm -Raw))
    }
}
$out.Add('')
$out | Out-File -Encoding utf8 $outFile
Write-Host "Wrote $outFile"
Get-Content $outFile | Select-Object -First 200 | ForEach-Object { Write-Host $_ }
