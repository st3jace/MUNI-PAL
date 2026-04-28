# Canonical Development Workspace

Muni-Pal is a mixed source, corpus, artifact, and historical-workspace repository. Agents and developers should not treat every top-level directory as active application source.

## Canonical active workspace

Use a native WSL path for active engineering work:

    /home/st3ja/Developer/MUNI-PAL

The OneDrive-backed Windows path is useful for archival/sync visibility, but it is not the active development workspace:

    /mnt/c/Users/st3ja/OneDrive/Documents/MEGA/PROJECTS/INNOVATION FACTORY/MUNI-PAL

Do not run long agent traversals, broad git status, test discovery, or build loops from the OneDrive path. WSL access through /mnt/c plus OneDrive placeholders/sync metadata has already caused slow or timed-out repository operations.

## Initial setup

Preferred setup from WSL:

    mkdir -p /home/st3ja/Developer
    git clone https://github.com/st3jace/MUNI-PAL.git /home/st3ja/Developer/MUNI-PAL
    cd /home/st3ja/Developer/MUNI-PAL
    python scripts/check_dev_environment.py

If a local OneDrive checkout has unpushed work, mirror or cherry-pick intentionally instead of using OneDrive as the day-to-day working tree. Keep secrets in local environment files and never copy .env values into chat, docs, or Linear comments.

## OneDrive policy

Until this repository is fully migrated, treat the OneDrive location as:

- archive/sync material;
- a place to inspect existing documents when necessary;
- not the canonical path for agent implementation runs.

Engineering changes should be made from the native WSL checkout and pushed through git. If an agent is launched inside the OneDrive path, it should stop and run:

    python scripts/check_dev_environment.py --warn-only

Then switch to /home/st3ja/Developer/MUNI-PAL before editing code.

## Canonical application tree and historical workspaces

The root repository tree is the canonical active BFMS application tree. Current engineering work should target root-level application paths such as `src/`, `frontend/`, `tests/`, `contracts/`, `alembic/`, root manifests, deployment files, and active docs.

V1/ is an archived historical application snapshot. Use it only as reference material when a task explicitly requires lineage review or migration comparison.

V2/ is a planning and execution-history workspace. It contains phase plans, runbooks, trackers, and release history; it is not the active code tree.

Do not implement active application changes under V1/ or V2/. If a request appears to point at those trees, first confirm whether the work is historical documentation/planning maintenance or should be redirected to the root application tree.

## Agent-safe source review scope

For code review and planning, scope traversal to the active source/manifests first:

    README.md
    PLAN.md
    pyproject.toml
    uv.lock
    docker-compose.yml
    docker-compose.prod.yml
    docker-compose.sensing.yml
    railway.toml
    .env.example
    .env.sensing.example
    frontend/package.json
    src/
    frontend/src/
    tests/
    contracts/
    alembic/versions/
    scripts/
    docs/

Avoid broad traversal of these directories unless a task explicitly calls for corpus or historical material:

    .git/
    node_modules/
    .venv/
    Bond Facility Development/
    V1/
    V2/
    artifacts/
    data/
    files/
    pdfs/
    images/
    logs/
    .gstack/
    .vercel/
    emma/emma_crawler/
    emma/bond_os_extractor/data/

## Health check

Run the workspace health check before implementation work:

    python scripts/check_dev_environment.py

Expected result in the canonical WSL checkout:

- repo root resolves to /home/st3ja/Developer/MUNI-PAL;
- git root resolves quickly;
- scoped source traversal completes quickly;
- no OneDrive or /mnt/c active-working-tree warning is emitted.

When run from the current OneDrive checkout, the script is expected to warn/fail so the problem is visible before a long agent run begins.
