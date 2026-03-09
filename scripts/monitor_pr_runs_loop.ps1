param(
    [int]$PrNumber = 11,
    [int]$IntervalSeconds = 300,
    [int]$Limit = 50
)

Write-Output "Starting PR monitor loop for PR #$PrNumber (interval ${IntervalSeconds}s)"
while ($true) {
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass -File scripts/monitor_pr_runs.ps1 -PrNumber $PrNumber -Limit $Limit
        # Run auto-fix runner after fetching logs; it will be a no-op if no fixes apply.
        & powershell -NoProfile -ExecutionPolicy Bypass -File scripts/auto_fix_pr_failures.ps1 -PrNumber $PrNumber
    } catch {
        Write-Error "Monitor run failed: $_"
    }
    Start-Sleep -Seconds $IntervalSeconds
}
