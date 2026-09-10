---
source: synthetic
generator_version: lab-gen-0.1.0
lab_version: 0.1.0
scenario_id: SYN-HSG-AZ-2025-LAB03
seed: 20250626
sha256_body: f1e2319c53f7b57d259e8261ae1b83d1c1bfa460cb11a9dd2f8935e9e92b7ff5
created_from:
  - "src/munipal/services/pilot_onboarding.py::build_pilot_onboarding_workflow('housing').document_request_list"
---

> SYNTHETIC RESEARCH ARTIFACT — MUNI-TWIN — NOT LEGAL ADVICE — NOT PREPARED BY AN ATTORNEY — NOT AN OFFER OF SECURITIES. Fictional names collision-checked against real firms.

# Document request checklist (housing sector playbook)

Generated from `build_pilot_onboarding_workflow('housing_affordable_multifamily').document_request_list` (src/munipal/services/pilot_onboarding.py:202-207) mapped through `playbook.required_artifacts[*].display_name -> artifact_key` (src/munipal/services/sector_playbooks.py::_HOUSING_ARTIFACTS).

| # | Requested document | Level | artifact_key | status in this pack |
|---|---|---|---|---|
| 1 | Issuer, borrower, and revenue pledge package (required) | required | `issuer_borrower_authority` | present (intake/01_PROJECT-OVERVIEW/issuer_borrower_authority.txt) |
| 2 | LIHTC, HAP, subsidy, and affordability restriction stack (required) | required | `subsidy_stack` | present (intake/02_FINANCING-STRUCTURE/subsidy_stack.txt) |
| 3 | Rent roll, occupancy, and operating revenue package (required) | required | `rent_roll_operating` | present (intake/02_FINANCING-STRUCTURE/rent_roll_operating.txt) |
| 4 | Site control, permits, and construction readiness package (required) | required | `site_control_permits` | absent_by_scenario (knob drop_required_artifact) |
| 5 | Market, demographics, lease-up, and compliance risk package (recommended) | recommended | `market_compliance` | present (intake/03_DUE-DILIGENCE/market_compliance.txt) |

SYNTHETIC RESEARCH ARTIFACT — MUNI-TWIN — NOT LEGAL ADVICE — NOT PREPARED BY AN ATTORNEY — NOT AN OFFER OF SECURITIES. Fictional names collision-checked against real firms.
