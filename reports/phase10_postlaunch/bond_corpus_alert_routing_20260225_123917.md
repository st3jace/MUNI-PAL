# Bond Corpus Drift Alert Routing

- Generated (UTC): `2026-02-25T12:39:17.497580+00:00`
- Source drift report: `bond_corpus_drift_20260225_123917.json`
- Drift status: `stable`
- Highest severity: `none`
- Requires incident: `False`
- Hold advisory generation: `False`

## Alert Summary

- Info: `0`
- Warning: `0`
- Critical: `0`

## CDR-5 Metric Coverage

- `reliability_band_change`: evaluated via sample-size proxy transitions
- `overall_posture_score_delta_gt_0_10`: evaluated via posture_score_proxy series
- `conflict_rate_spike_gt_0_20`: evaluated via conflict_rate_proxy series
- `evidence_count_drop_gt_30pct`: evaluated

## Routed Events

| Severity | Rule | Sector | Dimension | Message |
|---|---|---|---|---|
| none | - | - | - | No routed alert events. |

## Escalation Actions

- No action required beyond weekly evidence archival.
- Continue scheduled Phase 10 monitoring cadence.