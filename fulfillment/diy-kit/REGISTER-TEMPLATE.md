# Register template

Three tables. Keep them in a spreadsheet or a document. Column names matter because the skill outputs match them.

## 1. Candidate map → approved register

Rows enter as candidates (from the skill). A row becomes a register row only when the four approval columns are filled by your professional, in writing.

| id | obligation | source_document | clause | recipient | frequency | due_rule_text_verbatim | approved_by | approval_date | due_dates_approved | evidence_expected | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OB-01 | | | | | | | | | | | |

Rules:
- `due_dates_approved` is filled only by your counsel / dissemination agent. Blank means no date has been supplied and none should be computed.
- `status` is blank until `approved_by` is filled. Then it takes one of four words: `filed` · `not filed` · `evidence missing` · `not testable`. See the legend.

## 2. Items awaiting input

| requested_on | requested_from | item | source_document | clause | what_was_asked |
|---|---|---|---|---|---|

Sorted by request date. Nothing else.

## 3. Refusal log

| date | question | asked_by | routed_to |
|---|---|---|---|

Questions go in. Answers do not.

## Evidence file naming

`<id>_<period>_<short-name>.<ext>` — for example `OB-06_2026Q1_rent-roll.pdf`, `OB-01_FY2025_annual-report.pdf`.
One folder per series. The file name is the binding to the row.

## CSV header (paste into a blank sheet)

```
id,obligation,source_document,clause,recipient,frequency,due_rule_text_verbatim,approved_by,approval_date,due_dates_approved,evidence_expected,status
```
