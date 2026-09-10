# Obligation Register — demo on a synthetic deal

This folder is the proof for the one offer we sell: the **10-Day Obligation Register** (`LS-A2-POST`).
It runs end to end on **SYN-HSG-AZ-2025**, a synthetic affordable-housing conduit deal. Every name,
amount and date is invented. The method is real; the deal is not. No EMMA content anywhere.

## What it shows a prospect

1. **Their documents in** (`documents/`): closing-binder excerpts, shaped on the deidentified ALA
   closing index from muni-twin (metadata travels, content does not).
2. **Their professionals approve the list** (`approved-inputs.csv` + `approval-2026-09-08.md`): every
   obligation, clause and date on the register was approved by the client's own counsel or
   dissemination agent. We transcribe. We do not decide.
3. **The register out** (`output/register.html`): register, calendar, gap list, items awaiting
   input (what we asked counsel for and have not received), refusal log, evidence vault index.
4. **Arthur inside it** (`ask.py`): "where is this in my documents?" answered by pointing at the
   clause. Judgment questions are refused with the one-liner and logged.

## Run it

```bash
python3 build_fixtures.py          # rebuild documents/, approved-inputs.csv, vault/
python3 run.py --asof 2026-09-10   # writes output/
python3 ask.py "annual report due"
python3 ask.py "listed events"
python3 ask.py "is the bond call material"        # refused, logged
python3 ask.py --corpus /mnt/c/Users/st3ja/braintrust/corpus/legal/public-finance "dissemination agent"
```

Open `output/register.html` in a browser.

## The four statuses, and nothing else

`filed` · `not filed` · `evidence missing` · `not testable`

A fifth code ("professional determination required") was rejected by Arthur on 2026-09-09: marking a
row that way is itself a determination, and the unmarked rows read as cleared. The function lives in
two other places instead: the **items awaiting input** list (what we asked for in writing and have not
received) and the **refusal log** (judgment questions put to us, logged and routed, never answered).
A status only ever attaches to a row that has written professional input behind it.

## What it never does

Never files. Never says "compliant". Never decides which clause controls, interprets a deadline
formula, decides whether an obligation applies, or drafts a notice. Ambiguity goes to the refusal
log and to the client's counsel.

## Where the pieces come from

| Piece | Source |
|---|---|
| Deal shape (`scenario/`) | BONDI `deal-v0` schema, muni-twin six-station spine |
| Document list | muni-twin `data/taxonomy/ala-2024-index-deidentified-v1.tsv` (L1, deidentified) |
| Offer rules | `braintrust/workspace/gtm-stack-a-corpus/2026-09-09-OBLIGATION-REGISTER-ONE-PAGER.md` |
| Reference shelf for `ask.py --corpus` | `braintrust/corpus/legal/public-finance/` (secondary synthesis; may find authority, never be it) |

## Next

- Replace `documents/` with a real client's drop. Nothing else changes.
- Landing page = section 1 to 6 of `register.html`, with the intake form on top.
- Arthur seat: swap `ask.py` retrieval for his live seat on the 890, same refusal rule.
