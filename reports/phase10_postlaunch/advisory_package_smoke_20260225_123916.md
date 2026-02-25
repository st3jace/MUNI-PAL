# Advisory Package Smoke Assessment

- Generated (UTC): `2026-02-25T12:39:16.881027+00:00`
- Mode: `asgi`
- Base URL: `http://127.0.0.1:8000`
- ASGI sqlite path: `C:\Users\st3ja\AppData\Local\Temp\munipal_advisory_smoke_is_5ix_g.db`
- Recommendation: `go`
- Project used: `6a293270-f5f2-40b6-a119-ac7c4c2a1698`
- Project created by script: `6a293270-f5f2-40b6-a119-ac7c4c2a1698`

## Step Results

| Step | Method | Path | Status | Duration (s) |
|---|---|---|---:|---:|
| Health Check | GET | /health | 200 | 0.00 |
| Get Default Playbook | GET | /api/v1/playbooks/default | 404 | 0.04 |
| Seed Default Playbook | POST | /api/v1/playbooks/seed | 201 | 0.02 |
| Get Default Playbook (After Seed) | GET | /api/v1/playbooks/default | 200 | 0.00 |
| List Projects | GET | /api/v1/projects/ | 200 | 0.01 |
| Create Smoke Project | POST | /api/v1/projects/ | 201 | 0.01 |
| Generate Internal Advisory Report | POST | /api/v1/advisory-packages/internal/generate | 200 | 0.08 |
| Fetch Internal Advisory Report | GET | /api/v1/advisory-packages/internal/1f53f232-4def-4c1c-b14a-f7f5206ebce1 | 200 | 0.00 |
| Export Internal Advisory Report (MD) | GET | /api/v1/advisory-packages/internal/1f53f232-4def-4c1c-b14a-f7f5206ebce1/export | 200 | 0.00 |
| Generate External Advisory Package | POST | /api/v1/advisory-packages/external/generate | 200 | 0.03 |
| Fetch External Advisory Package | GET | /api/v1/advisory-packages/external/1f5e27a4-0e88-4e86-befe-287957e846b1 | 200 | 0.00 |
| Validate External Advisory Package | GET | /api/v1/advisory-packages/external/1f5e27a4-0e88-4e86-befe-287957e846b1/validate | 200 | 0.00 |
| Export External Advisory Package (MD) | GET | /api/v1/advisory-packages/external/1f5e27a4-0e88-4e86-befe-287957e846b1/export | 200 | 0.00 |

## Assertions

| Assertion | Result |
|---|---|
| project_id_resolved | True |
| internal_generate_ok | True |
| internal_report_fetch_ok | True |
| external_generate_ok | True |
| external_package_fetch_ok | True |
| external_validate_ok | True |

## Summary

- Internal report id: `1f53f232-4def-4c1c-b14a-f7f5206ebce1`
- External package id: `1f5e27a4-0e88-4e86-befe-287957e846b1`
- Internal overall score: `0.0`
- External ready_for_distribution: `False`
- External distribution issue count: `1`
- External risk integration mode: `Fallback`

## Recommendation Notes

- No blocking smoke issues detected.

## Linked Artifacts

- latest_advisory_cohort_inference_json: `advisory_cohort_inference_20260225_123914.json`