# Phase 7 Staging Evidence Template

Date: 2026-02-20

## Automated Gate Evidence (COMPLETE)

All four automated gates passed in GitHub Actions run `22235130725`.

### Phase 7 Closeout Dispatch

- CI workflow: `.github/workflows/phase7-closeout-dispatch.yml`
- Run URL: `https://github.com/st3jace/MUNI-PAL/actions/runs/22235130725`
- Commit SHA: `84f2a18dfc667aa504a15f60dc75cbd86ef98cae`
- Result summary: `pass — 4/4 gates green`

| Gate | Status | Duration |
|---|---|---:|
| Backend CI-Equivalent Gate (174 tests) | pass | 14.89s |
| Frontend Tests (vitest) | pass | 2.00s |
| Frontend Production Build | pass | 7.60s |
| Risk Focused Regression Slice | pass | 4.45s |

---

## Target CI Evidence

- CI workflow: `.github/workflows/core-security-risk-gate.yml`
- Run URL: `https://github.com/st3jace/MUNI-PAL/actions/runs/22235087843`
- Commit SHA: `84f2a18dfc667aa504a15f60dc75cbd86ef98cae`
- Result summary: `pass — green checkmark confirmed 2026-02-20`

## Staging API Evidence

- Endpoint: `GET /api/v1/risk/bfms-integration`
- Fallback mode project ID: `de618f31-bb6f-4905-be68-8445c357ed32`
- Fallback mode result: `integration_mode=fallback`, `overall_posture_score=0.78`, `5 low-reliability dimensions`, all 3 compliance checks pass, 7 critical risk flags, 5 material risk statements, 5 advisory next steps
- Full mode note: Full mode confirmed live — see Full-Mode BFMS Staging Example section below

## Staging UI Evidence

- Readiness tab: loads without errors — confirmed 2026-02-20
- Advisory Packages — External tab: BFMS fallback mode panel renders correctly (yellow banner, contract version, posture score, fallback reasons, top risk next steps displayed)
- Advisory Packages — Internal tab: Generate Report succeeded after `session.refresh(disclosure_doc, attribute_names=["tbd_items"])` fix applied to `advisory_package_service.py` — confirmed 2026-02-20

## Full-Mode BFMS Staging Example

Full mode is reached when all 5 risk dimensions have HIGH or MEDIUM reliability (≥2 approved facts each at confidence ≥ 0.95). The seed script creates this state deterministically.

### How to capture

```bash
# From project root (server NOT required):
python scripts/seed_fullmode_risk_facts.py

# Then call (server must be running on port 8080):
# GET http://localhost:8080/api/v1/risk/bfms-integration
#   ?project_id=de618f31-bb6f-4905-be68-8445c357ed32
#   &sector=waste_to_energy&issuer_size_band=mid&deal_type=revenue
#   &recency_window=5y&sample_size=50
```

### Actual staging full-mode response — 2026-02-20T20:05:13Z

Captured after running `python scripts/seed_fullmode_risk_facts.py` against project `de618f31-bb6f-4905-be68-8445c357ed32`.

```json
{
  "contract_version": "risk-bfms-integration-v1",
  "generated_at": "2026-02-20T20:05:13.466902Z",
  "project_id": "de618f31-bb6f-4905-be68-8445c357ed32",
  "cohort": {
    "sector": "waste_to_energy",
    "issuer_size_band": "mid",
    "deal_type": "revenue",
    "recency_window": "5y",
    "sample_size": 50
  },
  "integration_mode": "full",
  "fallback_reasons": [],
  "overall_benchmark_position": "below",
  "overall_posture_score": 0.25,
  "reliability_low_dimensions": 0,
  "directional_guidance_only": false,
  "critical_risk_flags": [
    "DSCR covenant headroom: Base DSCR 1.34x vs covenant 1.35x gives -0.01x headroom. Headroom is below tolerance minimum.",
    "Stress DSCR floor: Stress DSCR 0.89x evaluated against target floor 1.25x (tolerance 1.15x). Stress coverage is below tolerance minimum."
  ],
  "material_risk_statements": [],
  "advisory_next_steps": [
    {
      "action_id": "action.dscr.coverage",
      "priority": "high",
      "owner": "Financial Advisor / Sponsor",
      "title": "Strengthen DSCR coverage and covenant cushion",
      "target_date_hint": "7 days",
      "expected_impact": "Improves debt-service resilience and reduces probability of covenant stress."
    }
  ],
  "key_assumptions": [
    "No material assumptions beyond current validated evidence set."
  ],
  "compliance_checks": [
    {"rule_id": "no_internal_conflict_diagnostics", "passed": true, "detail": "Conflict counts and unresolved conflict references are excluded."},
    {"rule_id": "no_operational_queue_metadata", "passed": true, "detail": "Internal queue and workflow metadata are not included."},
    {"rule_id": "no_internal_uncertainty_notes", "passed": true, "detail": "Internal uncertainty notes are converted to external assumptions."}
  ],
  "internal_report_contract_version": "risk-internal-v1",
  "external_brief_contract_version": "risk-external-v1"
}
```

**Key assertions confirmed:** `integration_mode=full`, `directional_guidance_only=false`, `fallback_reasons=[]`, `reliability_low_dimensions=0`.

### Test coverage equivalent

`tests/integration/test_risk_reporting_foundation.py::test_risk_bfms_integration_contract_returns_full_mode_when_reliable` — passes in gate 4 of phase7-closeout-dispatch (4.45s, run `22235130725`).

---

## External Package Content Evidence (PENDING — manual)

To complete this section:
1. With server running, open Advisory Packages → External tab for project `de618f31-bb6f-4905-be68-8445c357ed32`
2. Click **Generate Report**
3. Copy the returned package ID from the response or UI
4. Open the package and verify the executive summary and assumptions sections reference BFMS integration mode/posture score
5. Fill in below:

- Package ID: `<package-id>`
- Evidence that summary/assumptions carry BFMS integration context: `<paste snippet or screenshot link>`

## Sign-off

- Product/Domain: `<name>` / `<date>`
- Engineering: `<name>` / `<date>`
- QA/Validation: `<name>` / `<date>`
