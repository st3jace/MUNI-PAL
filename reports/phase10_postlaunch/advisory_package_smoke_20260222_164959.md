# Advisory Package Smoke Assessment

- Generated (UTC): `2026-02-22T16:49:59.894216+00:00`
- Mode: `asgi`
- Base URL: `http://127.0.0.1:8000`
- ASGI sqlite path: `C:\Users\st3ja\AppData\Local\Temp\munipal_advisory_smoke_7c7ryp_y.db`
- Recommendation: `go`
- Project used: `c46ffc6d-71d4-4ad7-bf01-2e68816bec1d`
- Project created by script: `c46ffc6d-71d4-4ad7-bf01-2e68816bec1d`

## Step Results

| Step | Method | Path | Status | Duration (s) |
|---|---|---|---:|---:|
| Health Check | GET | /health | 200 | 0.00 |
| Get Default Playbook | GET | /api/v1/playbooks/default | 404 | 0.17 |
| Seed Default Playbook | POST | /api/v1/playbooks/seed | 201 | 0.03 |
| Get Default Playbook (After Seed) | GET | /api/v1/playbooks/default | 200 | 0.01 |
| List Projects | GET | /api/v1/projects/ | 200 | 0.03 |
| Create Smoke Project | POST | /api/v1/projects/ | 201 | 0.04 |
| Generate Internal Advisory Report | POST | /api/v1/advisory-packages/internal/generate | 200 | 0.28 |
| Fetch Internal Advisory Report | GET | /api/v1/advisory-packages/internal/59dc7b04-8830-4c64-80c7-478286819346 | 200 | 0.02 |
| Export Internal Advisory Report (MD) | GET | /api/v1/advisory-packages/internal/59dc7b04-8830-4c64-80c7-478286819346/export | 200 | 0.01 |
| Generate External Advisory Package | POST | /api/v1/advisory-packages/external/generate | 200 | 0.14 |
| Fetch External Advisory Package | GET | /api/v1/advisory-packages/external/99548cc7-9a85-4b9b-aa76-719ee92814c5 | 200 | 0.01 |
| Validate External Advisory Package | GET | /api/v1/advisory-packages/external/99548cc7-9a85-4b9b-aa76-719ee92814c5/validate | 200 | 0.01 |
| Export External Advisory Package (MD) | GET | /api/v1/advisory-packages/external/99548cc7-9a85-4b9b-aa76-719ee92814c5/export | 200 | 0.01 |

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

- Internal report id: `59dc7b04-8830-4c64-80c7-478286819346`
- External package id: `99548cc7-9a85-4b9b-aa76-719ee92814c5`
- Internal overall score: `0.0`
- External ready_for_distribution: `False`
- External distribution issue count: `1`
- External risk integration mode: `Fallback`

## Recommendation Notes

- No blocking smoke issues detected.

## Linked Artifacts

- latest_advisory_cohort_inference_json: `advisory_cohort_inference_20260222_164954.json`