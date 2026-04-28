# Muni-Pal Agent Operations Contract (START HERE)

Purpose: force consistent, low-drift agent execution for Muni-Pal engineering and operations work.

## Repository workspace contract

Engineering-mode agents must use the native WSL checkout as the canonical repo root:

    /home/st3ja/Developer/MUNI-PAL

If launched from the OneDrive-backed path under /mnt/c/Users/st3ja/OneDrive/.../MUNI-PAL, do not start broad traversal or edits. Run:

    python scripts/check_dev_environment.py --warn-only

Then switch to the canonical WSL checkout before implementation. Full policy: docs/development/CANONICAL_DEV_PATH.md.

Root repository tree is canonical for active BFMS application work: `src/`, `frontend/`, `tests/`, `contracts/`, `alembic/`, and root manifests/config. Do not edit V1/ or V2/ for active application work; treat `V1/` as archived historical application lineage and `V2/` as planning/execution-history material unless the task explicitly asks for archive or planning maintenance.

## Non-negotiable rules for agents

1. Do not start with full codebase review.
2. Do not change code unless explicitly asked for engineering mode.
3. Check the development workspace before implementation.
4. Use the scoped source review paths from docs/development/CANONICAL_DEV_PATH.md.
5. For bounded inventory, run: python scripts/count_source_scope.py --json; do not do whole-repo traversal.
6. Do not expose secrets from .env files.
