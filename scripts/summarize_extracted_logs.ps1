Set-Location 'C:\IDX_Analyst'
$base = 'pr-logs-artifacts-22875372029\extracted\pr-logs'
$outFile = 'pr_detailed_summary.txt'
if (-not (Test-Path $base)) {
    'No extracted pr-logs found' | Out-File $outFile -Encoding utf8
    exit 0
}

$out = New-Object System.Collections.Generic.List[string]
$out.Add('Detailed PR logs summary')
$out.Add('Generated: ' + (Get-Date).ToString('u'))
$out.Add('')

foreach ($runDir in Get-ChildItem $base -Directory) {
    $out.Add('Run folder: ' + $runDir.Name)
    $files = Get-ChildItem $runDir.FullName -Recurse -File -ErrorAction SilentlyContinue
    if (-not $files) { $out.Add('  (no files)'); $out.Add(''); continue }
    $out.Add('  Files: ' + ($files.Count))
    $largest = $files | Sort-Object Length -Descending | Select-Object -First 3
    foreach ($f in $largest) {
        $out.Add(('  - {0} ({1} bytes)' -f $f.FullName, $f.Length))
        # capture first/last 20 lines and search for error/exception/failed
        $first = Get-Content $f.FullName -ErrorAction SilentlyContinue | Select-Object -First 20
        $last = Get-Content $f.FullName -ErrorAction SilentlyContinue | Select-Object -Last 20
        $out.Add('    First lines:')
        $first | ForEach-Object { $out.Add('      ' + $_) }
        $out.Add('    Last lines:')
        $last | ForEach-Object { $out.Add('      ' + $_) }
        $matches = Select-String -Path $f.FullName -Pattern 'error|exception|failed|traceback' -SimpleMatch -CaseSensitive:$false -ErrorAction SilentlyContinue | Select-Object -First 10
        if ($matches) {
            $out.Add('    Matches (error/exception/failed):')
            foreach ($m in $matches) { $out.Add(('      {0}:{1} {2}' -f $m.Path, $m.LineNumber, $m.Line.Trim())) }
        } else {
            $out.Add('    No explicit error/exception/failed matches found in file.')
        }
        $out.Add('')
    }
    $out.Add('')
}

$out | Out-File -Encoding utf8 $outFile
Write-Host "Wrote $outFile"
Get-Content $outFile | Select-Object -First 500 | ForEach-Object { Write-Host $_ }
