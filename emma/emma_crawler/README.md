# EMMA Crawler (Muni-Pal Waste Sector)

Initial implementation of the EMMA municipal bond crawler using async Playwright.

## Current status

- Project scaffold and configuration completed.
- Phase 1 search population and Phase 2 collect-first queue flow implemented.
- Phase 3 direct URL processing loop implemented with extractor placeholders.

## Quick start

```bash
pip install -r requirements.txt
playwright install chromium
python -m src.main --phase2-only
```

## Commands

```bash
python -m src.discover_selectors --save-html
python -m src.main --test-url "https://emma.msrb.org/Security/Details/<hash>"
python -m src.main --test-cusip 46245EBA4
python -m src.main --phase2-only
python -m src.main --phase3-only --max-securities 3
python -m src.main --resume
python -m src.main --retry-failed
python -m src.main --retry-partial
python -m src.main --dry-run
python -m src.main --phase2-only --visible --emma-username "you@example.com" --emma-password "your-password"
```

`--emma-username` / `--emma-password` are optional. You can also set `EMMA_USERNAME` and `EMMA_PASSWORD` environment variables.

Session cookies/local storage are persisted automatically to `output/emma_storage_state.json` so terms/login gates are usually not repeated every run.
