# Age Weighting Policy Assessment

- Generated (UTC): `2026-02-25T12:39:17.244034+00:00`
- Source calibration report: `bond_corpus_calibration_20260225_123913.json`
- Recommendation status: `hold`

## Recency Summary

- Sectors evaluated: `2`
- Max stale ratio (>365d): `0.0`
- Avg stale ratio (>365d): `0.0`

## Sector Recency

| Sector | Stale Ratio >180d | Stale Ratio >365d |
|---|---:|---:|
| waste | 0.0 | 0.0 |
| healthcare | 0.0 | 0.0 |

## Candidate Penalty Simulation

| Max Penalty | Avg Score Penalty | Avg Confidence Multiplier |
|---:|---:|---:|
| 0.1 | 0.0 | 1.0 |
| 0.15 | 0.0 | 1.0 |
| 0.2 | 0.0 | 1.0 |

## Suggested Environment

- `RISK_REPORTING_V2_AGE_WEIGHTING=false`
- `RISK_REPORTING_V2_AGE_WEIGHTING_FULL_WEIGHT_DAYS=365`
- `RISK_REPORTING_V2_AGE_WEIGHTING_MAX_PENALTY=0.10`

## Recommendation Notes

- Recency staleness is limited; keep age-weighting disabled until next data refresh.
- Suggested max penalty selected from observed stale ratio distribution across sectors.