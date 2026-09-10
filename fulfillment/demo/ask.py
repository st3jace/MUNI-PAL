#!/usr/bin/env python3
"""ask.py — "Where is this in my documents?"  (the Arthur seat, demo form)

Answers ONLY by pointing at text: file, section, and the clause itself.
Never interprets. Never says whether something applies, is material, or is compliant.

  python ask.py "annual report due"
  python ask.py "listed events"
  python ask.py "is the bond call material"      -> refused, logged
  python ask.py --corpus ../../..../public-finance "dissemination agent"   -> adds reference-shelf hits,
                                                                              labeled as secondary synthesis

Judgment questions get the one-liner from the offer sheet and a line in output/refusal-log.md.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "documents"

JUDGMENT = re.compile(
    r"\b(material|materiality|should (we|i)|do (we|i) (need|have) to|must (we|i)|compliant|compliance with|"
    r"appl(y|ies)|controls?|which clause|is (this|that|it) (a|an) (listed|reportable)|are we (ok|fine|late)|"
    r"advice|advise|recommend|what should)\b", re.I)
# Arthur's wording, 2026-09-09 ruling §3.1. No status code, no implied triage.
ONE_LINER = ("That is a call for your bond counsel or dissemination agent. I will log the question, "
             "send it to them, and leave that field empty until they answer in writing.")

STOP = {"the", "a", "an", "of", "in", "to", "is", "my", "our", "where", "what", "when", "does", "do", "for", "and", "or", "on", "by", "it", "this", "that", "are", "be", "with"}
SECTION_RE = re.compile(r"^## (.+)$", re.M)


def sections(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    parts = SECTION_RE.split(text)
    yield "(preamble)", parts[0], 1
    line = parts[0].count("\n") + 1
    for i in range(1, len(parts) - 1, 2):
        heading, body = parts[i], parts[i + 1]
        yield heading.strip(), body, line
        line += 1 + body.count("\n")


def score(q_terms: list[str], heading: str, body: str) -> int:
    hay = (heading + " " + body).lower()
    s = 0
    for t in q_terms:
        n = hay.count(t)
        if n:
            s += 3 + min(n, 5)
            if t in heading.lower():
                s += 4
    return s


def search(root: Path, q_terms: list[str], label: str, limit: int, glob: str = "*.md"):
    hits = []
    for p in sorted(root.rglob(glob)):
        if p.name.startswith(("VERIFICATION", "PROVENANCE", "Volume_", "VOLUME_")):
            continue
        for heading, body, line in sections(p):
            sc = score(q_terms, heading, body)
            if sc:
                hits.append((sc, label, p, heading, line, body.strip()))
    hits.sort(key=lambda h: -h[0])
    return hits[:limit]


def log_refusal(question: str) -> None:
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    p = out / "refusal-log.md"
    if not p.exists():
        p.write_text("# Refusal log\n\nEvery judgment question put to us: the question, the date, and where it was routed. We do not answer them.\n\n", encoding="utf-8")
    with p.open("a", encoding="utf-8") as f:
        f.write(f"- {date.today().isoformat()} · asked via Q&A: \"{question}\" · routed to: bond counsel / dissemination agent · not answered.\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="+")
    ap.add_argument("--corpus", default="", help="optional reference shelf (secondary synthesis; may FIND authority, never BE it)")
    ap.add_argument("--limit", type=int, default=4)
    args = ap.parse_args()
    q = " ".join(args.question)

    if JUDGMENT.search(q):
        print("REFUSED (judgment question)\n" + ONE_LINER)
        log_refusal(q)
        sys.exit(2)

    terms = [t for t in re.findall(r"[a-z0-9()\-]+", q.lower()) if t not in STOP and len(t) > 2]
    if not terms:
        print("Ask for a thing, e.g. 'annual report', 'listed events', 'rebate'.")
        sys.exit(1)

    hits = search(DOCS, terms, "YOUR DOCUMENTS", args.limit)
    print(f"Question: {q}\nTerms: {', '.join(terms)}\n")
    if not hits:
        print("Not found in your documents. That is the answer: it is not in the excerpts you gave us.")
    for sc, label, p, heading, line, body in hits:
        print(f"[{label}] {p.name} :: {heading}  (line {line})")
        for para in body.split("\n"):
            if para.strip():
                print("    " + para.strip()[:600])
        print()

    if args.corpus:
        cp = Path(args.corpus)
        if cp.exists():
            ref = search(cp, terms, "REFERENCE SHELF", 3)
            if ref:
                print("--- Reference shelf (secondary synthesis, agent-authored 2026-03; may FIND authority, never BE it; verify against primary text before use) ---")
            for sc, label, p, heading, line, body in ref:
                print(f"[{label}] {p.relative_to(cp)} :: {heading}  (line {line})")
                print("    " + body.strip().split("\n")[0][:400] + "\n")
        else:
            print(f"(corpus path not found: {cp})")


if __name__ == "__main__":
    main()
