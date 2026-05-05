# ELA-51 — Local dashboard platform landing review

Reviewed: local current HEAD

Routes and services reviewed:

- Frontend dashboard: http://localhost:4121/dashboard
- Public sensing hub: http://localhost:4121/tools
- Pilot Navigation: http://localhost:4121/tools/pilot-navigation
- Backend health: http://localhost:8000/health
- Projects API: http://localhost:8000/api/v1/projects/?limit=5

## Executive summary

The local dashboard loads in the current launch setup and the backend/frontend dev servers are reachable. The dashboard is operational as a BFMS shell, but it is not yet a strong launch landing experience: with the current empty local database it renders generic project metrics and an empty-project CTA rather than explaining BFMS purpose, pilot readiness, Healthcare/Housing scenario status, or the sensing-to-pilot handoff state.

No immediate route-load blocker was found for /dashboard, but the page should not be treated as launch-demo ready until seeded Healthcare/Housing walkthrough data exists and the landing state is made more pilot-aware.

## Evidence

HTTP probes:

- /dashboard: 200
- /tools: 200
- /tools/pilot-navigation: 200
- /health: 200
- /api/v1/projects/?limit=5: 200 with empty projects response: projects=[], total=0, skip=0, limit=5

Source anchors reviewed:

- frontend/src/pages/Dashboard.tsx
- frontend/src/components/Layout.tsx
- frontend/src/pages/ProjectList.tsx
- frontend/src/services/generatedApi.ts
- frontend/src/generated/api-client/services/ProjectsService.ts

Browser-tool note: the built-in browser session failed in this WSL/Windows environment with WinError 193, so this pass used local HTTP probes and source-level inspection rather than interactive browser screenshots.

## Findings

### Launch blocker: no seeded local projects for dashboard review

Severity: High for launch/demo readiness; not a runtime bug.

The current local Projects API returns an empty project list. As a result, /dashboard can only demonstrate:

- Total Projects: 0
- Documents Uploaded: 0
- Projects Scored: 0
- Avg Readiness: No data
- Recent Projects: No projects / Create Project

This confirms route reliability, but it does not validate the actual BFMS operator value proposition. It also makes Healthcare/Housing walkthrough issues dependent on seed data before they can be meaningfully reviewed.

Recommendation: handle this in the next batch via ELA-57 before using ELA-52/53 as product-readiness evidence.

### Product clarity blocker: dashboard does not explain pilot status or launch path

Severity: Medium/High.

The dashboard headline is generic:

- Dashboard
- Overview of your bond facility management activities

The top bar says Bond Facility Management System, and the empty state says Get started by creating a new project.

For an operator or pilot reviewer, the page does not currently answer:

- What is BFMS for?
- Which pilot scenarios are loaded or ready?
- What is the expected next action after sensing qualification?
- Which sectors are primary vs pilot-stage vs supported/control?
- Whether this is an authenticated/internal BFMS workspace, not the public sensing site.

Recommendation: add a launch/pilot-aware dashboard panel in a follow-up implementation issue after seed data exists. It should summarize Healthcare primary, Housing pilot-stage, UCS/WTE supported/control, and link to the next operator action.

### UX gap: empty state sends users to generic project creation, not a guided pilot path

Severity: Medium.

The empty dashboard CTA links to /projects with text Create Project. The Projects page supports Healthcare, Affordable Housing, and Waste-to-Energy sectors, which is good. However, from the dashboard alone there is no distinction between ad hoc project creation and the qualified sensing-to-pilot path implemented in ELA-54/55/56.

Recommendation: after ELA-57 seed data, provide a guided empty/demo state such as:

- Review seeded Healthcare pilot
- Review Housing pilot-stage scenario
- Create BFMS project from qualified lead
- Open public Pilot Navigation

### Public vs authenticated surface separation is mostly clear

Severity: Low.

The authenticated/full BFMS layout includes Sensing Tools in the sidebar, but ELA-56 now ensures the standalone public sensing app is split from the full BFMS app. Within the full platform, the sidebar separation is understandable:

- Dashboard
- Projects
- Sensing Tools

This does not appear to confuse public deployment routing by itself. The main risk is narrative clarity: a launch reviewer might not know whether /tools is public-prospect-facing or an internal operator convenience when seen from inside the full BFMS shell.

Recommendation: add short labels/copy in a later polish pass, not a blocker.

### Auth/dev-mode caveat should remain a separate security pass

Severity: High as platform security risk, but outside ELA-51 dashboard landing scope.

Generated API clients include development headers when no bearer token is configured. Several full BFMS route families are mounted in munipal.main. This is acceptable for local review but should not be conflated with public sensing deployment safety; ELA-56 addressed the public sensing route boundary by requiring munipal.sensing_app.

Recommendation: create or prioritize a full BFMS auth hardening/security pass before pilot/commercial launch.

## Launch blocker vs polish recommendations

### Launch/demo blockers

1. Seeded local dashboard data is missing. ELA-57 should create credible Healthcare/Housing demo projects before ELA-52/53 walkthroughs.
2. Dashboard landing does not yet communicate pilot status or next actions; this becomes more important once seed data is available.

### High-priority follow-up

1. Add a dashboard launch/pilot status panel after ELA-57.
2. Add an explicit internal/full-BFMS label near the dashboard/shell to distinguish it from public sensing.
3. Run full BFMS auth hardening as a separate security issue.

### Non-blocking polish

1. Improve empty state copy from generic Create Project to guided pilot/demo actions.
2. Add links from dashboard to Pilot Navigation and seeded scenario walkthroughs.
3. Add error handling on the dashboard analogous to ProjectList.tsx so API failures do not silently collapse into an empty/partial Recent Projects card.

## Recommendation for next batch order

Proceed with ELA-57 next, before ELA-52/53.

Reason: Healthcare and Housing walkthroughs will be low-signal while the dashboard has zero local projects. ELA-57 should seed credible scenarios and golden walkthrough notes so ELA-52/53 can test actual product behavior rather than empty states.
