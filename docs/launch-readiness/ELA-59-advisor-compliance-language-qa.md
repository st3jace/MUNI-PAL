# ELA-59 Advisor-ready Handoff and Compliance Language Live QA

Date: 2026-05-08T16:42:00.689947+00:00

Environment labels:
- Deployed public site: https://muni-pal.io/ and https://muni-pal.io/pricing, captured by HTTP and Windows Chrome screenshot fallback.
- Current local source: /home/st3ja/Developer/MUNI-PAL current working tree.
- Browser-tool status: built-in browser failed with WinError 193, so evidence used HTTP probes plus Windows Chrome screenshots.

## Linear acceptance criteria

- No deal approval, pricing recommendation, issuance recommendation, bond sizing recommendation, legal opinion, MA advice, or closing instruction language appears.
- Evidence-backed claims are distinguishable from missing/unknown facts.
- Advisor/counsel/operator roles are framed accurately.
- Screenshots/examples of problematic language are attached to findings.
- Launch-safe copy changes are filed or implemented.

## Evidence captured

| URL | Status | Final URL | Note |
| --- | ---: | --- | --- |
| https://muni-pal.io/ | 200 | https://muni-pal.io/ | static HTML captured; SPA screenshot captured separately |
| https://muni-pal.io/pricing | 200 | https://muni-pal.io/pricing | static HTML captured; SPA screenshot captured separately |

Artifacts:
- dogfood-output/ela59/http/muni-pal.io.html
- dogfood-output/ela59/http/muni-pal.io_pricing.html
- dogfood-output/ela59/dom/muni-pal.io.txt
- dogfood-output/ela59/dom/muni-pal.io_pricing.txt
- dogfood-output/ela59/screenshots/home.png
- dogfood-output/ela59/screenshots/pricing.png
- dogfood-output/ela59/audit/compliance_language_hits.json
- dogfood-output/ela59/audit/high_risk_phrase_hits_after_patch.json

## Findings

### 1. Deployed public site still contains stale high-risk cost/pricing framing

Status: launch blocker until redeploy from patched source or equivalent production copy update.

Observed deployed examples:
- dogfood-output/ela59/http/muni-pal.io.html: meta description says know what good looks like, what it costs, and where deals fall apart.
- dogfood-output/ela59/http/muni-pal.io.html: static list contains Know what it costs — corpus-calibrated TIC estimates by rating tier.
- dogfood-output/ela59/http/muni-pal.io_pricing.html has the same static content.

Why it matters: TIC estimates and what it costs are too close to pricing/cost-of-capital advice for a launch page unless surrounded by stronger registered-advisor and non-pricing boundaries. This is production evidence, not current-HEAD evidence.

Source action taken: reframed cost/pricing language to cost context before registered advisor review; reframed pressure-test advisor language to prepare better questions for the registered advisor and deal team; reframed COI optimization and pre-issuance support as readiness support.

### 2. Current readiness/advisory package copy implied execution or market-readiness too strongly

Status: patched in current source.

Examples patched:
- execution-grade advisory decisioning -> evidence-backed advisor review support
- Risk outputs are stable for advisory decisioning -> registered advisor review support with explicit non-approval/non-sizing/non-pricing/non-issuance boundary
- Proposed Bond Amount -> Target Financing Amount
- proposes to issue revenue bonds -> is evaluating potential revenue bond financing
- Ready for Broad Market -> Ready for Advisor-Led Market Review
- formal underwriter selection process -> professional diligence / issuer-borrower direction boundary
- advisor-grade / bond-issuance-ready product copy -> advisor-facing / advisor-review-ready readiness support

### 3. Existing handoff/pilot disclaimers are generally aligned

Status: pass with false-positive audit hits.

The post-patch phrase scan still finds phrases like deal approval, pricing recommendation, and municipal advisory advice in files that explicitly disclaim those acts. Those are desired boundary statements, not unsafe recommendations.

## Current source posture after patches

- Healthcare: pass for current source, subject to redeploy before public launch.
- Housing: no new Housing-specific unsafe launch copy was identified in this pass, but the public deployed site remains Healthcare-centric. Housing should remain invite-only/direct-pilot unless a separate public Housing page is reviewed.
- Warm Handoff / advisory package: pass for current source after copy changes and guardrail tests.
- Readiness: pass for current source after high-score label and rationale changes.
- Public deployed site/pricing: fail until stale deployed TIC/cost wording is replaced by patched source copy or a manual production edit.

## Files changed for launch-safe copy
- src/munipal/services/advisory_package_service.py
- src/munipal/services/readiness_service.py
- src/munipal/api/routes/readiness.py
- src/munipal/core/schemas/readiness.py
- src/munipal/main.py
- src/munipal/__init__.py
- src/munipal/services/playbook_data.py
- src/munipal/services/warm_handoff.py
- frontend/src/pages/AdvisoryPackages.tsx
- frontend/src/pages/Readiness.tsx
- frontend/src/pages/tools/HealthcareCFOLanding.tsx
- frontend/src/pages/tools/HealthcareMIRContent.tsx
- frontend/src/pages/tools/HealthcareReadiness.tsx
- frontend/src/pages/tools/ReadinessAssess.tsx
- frontend/src/pages/tools/design-variants/variant-a/HealthcareCFOLanding.tsx
- frontend/src/pages/tools/design-variants/variant-b/HealthcareCFOLanding.tsx
- frontend/src/pages/tools/design-variants/variant-c/HealthcareCFOLanding.tsx
- tests/unit/test_advisory_package_service.py
- tests/unit/test_readiness_launch_language.py

## Verification performed so far

Command: /home/st3ja/.local/bin/uv run --extra dev pytest tests/unit/test_advisory_package_service.py::test_external_package_language_stays_advisor_review_safe tests/unit/test_readiness_launch_language.py tests/unit/test_warm_handoff_pack.py -q
Result: 7 passed

Post-patch phrase audit: dogfood-output/ela59/audit/high_risk_phrase_hits_after_patch.json
Remaining current-source hits are disclaimer/guardrail false positives. Remaining deployed-site hits are blocker evidence for stale production copy.

## Launch verdict

Current source can proceed toward advisor/compliance launch readiness after full verification/build. Deployed public site is not launch-safe yet because it still serves stale TIC/cost wording. Redeploy from this patched source, then re-run ELA-59 public-site screenshot/HTTP evidence before declaring production pass.
