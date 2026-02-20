# Phase 7 Staging Evidence Template

Date: 2026-02-19

Use this once target CI/staging validation is executed.

## Target CI Evidence

- CI workflow: `.github/workflows/core-security-risk-gate.yml`
- Run URL: `<paste-url>`
- Commit SHA: `<paste-sha>`
- Result summary: `<pass/fail + key counts>`

## Staging API Evidence

- Endpoint: `GET /api/v1/risk/bfms-integration`
- Full mode project ID: `<project-id>`
- Full mode evidence link/screenshot: `<link>`
- Fallback mode project ID: `<project-id>`
- Fallback mode evidence link/screenshot: `<link>`

## Staging UI Evidence

- Readiness full/fallback rendering evidence: `<link>`
- Advisory Packages full/fallback/unavailable rendering evidence: `<link>`

## External Package Content Evidence

- Package ID: `<package-id>`
- Evidence that summary/assumptions carry BFMS integration context: `<link>`

## Sign-off

- Product/Domain: `<name>` / `<date>`
- Engineering: `<name>` / `<date>`
- QA/Validation: `<name>` / `<date>`
