Artifact summary for run 22886407757

Artifact: pr-logs-22886407757 (artifact id 5842704878)
Run URL: https://github.com/FadelSearr/Dellmology-pro/actions/runs/22886407757

Extracted contents (under `pr-logs`):

- 22886402751/
  - model_metrics/model_metrics.json

model_metrics.json (parsed):
```
{
  "timestamp": "2026-03-10T03:58:14.722364Z",
  "samples": 16,
  "input_shape": [16, 16, 1],
  "avg_top1_confidence": 0.5
}
```

Notes:
- This artifact contains a single run folder (`22886402751`) with `model_metrics.json` showing a successful ML smoke sample run (16 samples, avg confidence 0.5).
- Several other runs in the monitor sweep had no downloadable artifacts (warnings in monitor log). The placeholder behavior ensures artifact upload even when no logs are present.

Next suggestions:
- If you want, I can append this summary as a follow-up PR comment to PR #11, or collect and summarize other archived `pr-logs-*.tar.gz` files in the repo.
