# ELA-93 Public Copy Redeploy QA

## Environment

- Canonical checkout: /home/st3ja/Developer/MUNI-PAL
- Branch: master
- Scope: healthcare public entrypoint, pricing page, healthcare landing variants, healthcare market-intelligence/readiness launch copy, and generated build:healthcare artifacts.
- Linear: ELA-93 — BFMS Launch: Redeploy compliance-safe public copy and re-run launch QA.

## Summary

ELA-93 follow-up found that earlier React/TSX public-copy fixes were not sufficient because the static Vite healthcare entry template still carried stale fallback/meta copy. The remaining generated healthcare artifact contained advisor-replacement and precise cost/TIC wording from frontend/index.healthcare.html even after the React source pages were patched.

This pass removes the remaining static-template risks, broadens static guardrail coverage, and verifies the current local healthcare build no longer contains the blocked phrases while preserving explicit registered-advisor / municipal-advisory boundary language.

## Copy guardrails enforced

Blocked launch wording now covered by tests/unit/test_public_launch_copy_guardrails.py includes:

- what your advisors wont tell you
- document your way to a better rating
- ongoing advisory access
- COI optimization
- active deal coordination
- TIC estimates
- what it costs
- rating pays
- achieving and maintaining an A or better

Required boundary wording remains:

- registered advisor
- not municipal advisory advice

## Files changed

- frontend/index.healthcare.html: replaced static meta/fallback copy that implied advisor-replacement or precise cost/TIC estimates; added registered-advisor review framing and a not municipal advisory advice boundary to the noscript fallback.
- frontend/src/pages/tools/PricingPage.tsx: replaced ongoing advisory access with readiness workspace language; expanded footer disclaimer to state not investment advice, not municipal advisory advice, and not pricing/sizing/issuance/deal-execution recommendation.
- frontend/src/pages/tools/HealthcareCFOLanding.tsx, frontend/src/pages/tools/HealthcareMIRContent.tsx, and healthcare design variants A/B/C: reframed rating-improvement, COI optimization, active deal coordination, and pre-issuance support language around evidence preparation, readiness workplans, benchmark context, and registered-advisor/deal-team review.
- tests/unit/test_public_launch_copy_guardrails.py: new static regression test for public launch copy sources, including the static healthcare HTML entrypoint.

## Evidence

Local build phrase scan:

- Evidence file: dogfood-output/ela93/local_build_phrase_scan.json
- Blocked hits: none
- Required hits present: registered advisor; not municipal advisory advice
- Files scanned: frontend/dist-healthcare/index.healthcare.html and generated healthcare JS/CSS chunks under frontend/dist-healthcare/assets/

Earlier deployed/public-site evidence and asset-scan artifacts are under dogfood-output/ela93/. Browser screenshot capture was not available in this WSL/Windows tool session because the built-in browser failed with WinError 193 and direct Windows Chrome headless execution was denied by the tool permission layer; those blocked commands were not retried.

## Verification

Commands run from /home/st3ja/Developer/MUNI-PAL:

- /home/st3ja/.local/bin/uv run --extra dev pytest tests/unit/test_public_launch_copy_guardrails.py tests/unit/test_readiness_launch_language.py -q
  - Result: 3 passed in 0.05s
- npm --prefix frontend run build:healthcare
  - Result: Vite healthcare build succeeded. The only warning was the existing non-blocking large-chunk warning for html2pdf.
- python3 scripts/check_dev_environment.py
  - Result: status: OK
- git diff --check
  - Result: passed.

## Deployment note

This report verifies the current canonical local checkout and generated healthcare build. ELA-93 should only be marked fully launch-complete after the committed changes are pushed and the deployed public site is rechecked to confirm production no longer serves stale copy.
