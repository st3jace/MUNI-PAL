# Advisory Cohort Inference Assessment

- Generated (UTC): `2026-02-22T16:49:54.152741+00:00`
- Recommendation: `go`

## Summary

- Scenarios evaluated: `6`
- Scenarios passed: `6`
- Scenarios failed: `0`
- Match rate: `100.0%`
- Target combos covered: `6/6`

## Scenario Results

| Scenario | Expected Sector | Expected Deal Type | Inferred Sector | Inferred Deal Type | Status |
|---|---|---|---|---|---|
| healthcare_conduit_extractor_profile | healthcare | conduit | healthcare | conduit | pass |
| healthcare_revenue_project_metadata | healthcare | revenue | healthcare | revenue | pass |
| healthcare_private_activity_501c3 | healthcare | private_activity | healthcare | private_activity | pass |
| waste_revenue_feedstock | waste_to_energy | revenue | waste_to_energy | revenue | pass |
| waste_conduit_ida_structure | waste_to_energy | conduit | waste_to_energy | conduit | pass |
| waste_private_activity_industrial_development | waste_to_energy | private_activity | waste_to_energy | private_activity | pass |

## Coverage Matrix (Expected Profiles)

| Sector | Revenue | Conduit | Private Activity |
|---|---:|---:|---:|
| healthcare | 1 | 1 | 1 |
| waste_to_energy | 1 | 1 | 1 |

## Recommendation Notes

- No blocking issues detected.