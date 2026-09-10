"""labkit -- contracts for the internal `lab/twin-bfms` program.

Internal R&D only. Nothing here is mounted by `munipal.main` or `munipal.sensing_app`;
the only bridge from the test suite is `tests/lab_support.py`.

"twin-bfms" is a label, not a claim (DEC-009 section 9.8).

Modules (stdlib + pydantic only):
- `law`        -- constants that transcribe the rulings in `lab/twin-bfms/LAW.md`
- `types`      -- pydantic v2 models; every status is four-valued by construction
- `provenance` -- the ONLY file writer; stamps the legend and the envelope
"""

LAB_VERSION = "0.1.0"
GENERATOR_VERSION = "lab-gen-0.1.0"

__all__ = ["GENERATOR_VERSION", "LAB_VERSION"]
