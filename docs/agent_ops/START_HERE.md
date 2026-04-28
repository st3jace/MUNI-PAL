# Muni-Pal Agent Operations Contract (START HERE)

Purpose: force consistent, low-drift agent execution for Muni-Pal engineering and operations work.

## Repository workspace contract

Engineering-mode agents must use the native WSL checkout as the canonical repo root:

    /home/st3ja/Developer/MUNI-PAL

If launched from the OneDrive-backed path under /mnt/c/Users/st3ja/OneDrive/.../MUNI-PAL, do not start broad traversal or edits. Run:

    python scripts/check_dev_environment.py --warn-only

Then switch to the canonical WSL checkout before implementation. Full policy: docs/development/CANONICAL_DEV_PATH.md.

## Non-negotiable rules for agents

1. Do not start with full codebase review.
2. Do not change code unless explicitly asked for engineering mode.
3. Check the development workspace before implementation.
4. Use the scoped source review paths from docs/development/CANONICAL_DEV_PATH.md.
5. Do not expose secrets from .env files.
