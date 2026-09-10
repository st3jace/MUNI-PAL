"""The ONLY file writer for `lab/twin-bfms` (BUILD-SPEC 4.5, 4.6).

Every generated document carries the legend and a provenance envelope by construction:

- `.md`        YAML frontmatter (envelope) -> legend as the first blockquote -> optional
               banner -> body -> legend as the last line; files over 60 lines repeat the
               legend every 60 lines ("every page").
- intake `.txt` `# key: value` envelope lines -> legend line -> content.
- vault `.txt` label line (line 1, unchanged; run.py indexes it) -> legend (line 2) ->
               `# key: value` envelope lines -> content.
- `.json`      `_legend` + `_provenance` keys, canonical (sorted keys, 2-space, LF).
- `.csv`       header + rows, plus a sidecar `<file>.provenance.json`.

By construction the writer also refuses: any rule-3 token; the MSRB platform token beyond
the caller's explicit allowance (default 0); extensions outside {md,txt,csv,json}; a path
component named in `law.IGNORED_DIR_NAMES`; non-ASCII file names. Nothing here reads a
clock: envelopes carry no timestamp, so two generations are byte-identical.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from labkit import law
from labkit.types import Envelope


class ProvenanceViolation(ValueError):
    """Raised when a write would break a lab law; fence-class, never swallowed."""


# --------------------------------------------------------------------------------------
# Hash / JSON helpers
# --------------------------------------------------------------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def canonical_json(obj: Any) -> str:
    """Sorted keys, 2-space indent, UTF-8 characters kept, single trailing LF."""
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def tree_sha256(root: Path, *, ignore_dirs: frozenset[str] = frozenset({"__pycache__"})) -> str:
    """Deterministic hash of a directory tree: sorted relative paths + file hashes."""
    root = Path(root)
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if any(part in ignore_dirs for part in path.relative_to(root).parts):
            continue
        h.update(path.relative_to(root).as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update(sha256_file(path).encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


# --------------------------------------------------------------------------------------
# Written-file record and path law
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class WrittenFile:
    path: Path
    relpath: str | None
    sha256: str
    sha256_body: str
    size: int
    kind: str


def _check_path(path: Path, *, sidecar: bool = False) -> None:
    if not path.name.isascii():
        raise ProvenanceViolation(f"non-ASCII file name: {path.name!r}")
    suffix = path.suffix.lower()
    if sidecar:
        if not path.name.endswith(law.CSV_SIDECAR_SUFFIX):
            raise ProvenanceViolation(f"sidecar must end with {law.CSV_SIDECAR_SUFFIX}: {path}")
    elif suffix not in law.ALLOWED_EXTENSIONS:
        raise ProvenanceViolation(f"extension {suffix!r} not allowed (md/txt/csv/json only): {path}")
    for part in path.parts[:-1]:
        if part in law.IGNORED_DIR_NAMES:
            raise ProvenanceViolation(
                f"directory name {part!r} is swallowed by the root .gitignore: {path}"
            )


def _check_content(text: str, *, where: Path, emma_allowed: int) -> None:
    hits = law.forbidden_token_hits(text)
    if hits:
        raise ProvenanceViolation(f"rule-3 token(s) {hits} in {where}")
    n = len(law.EMMA_WORD.findall(text))
    if n != emma_allowed:
        raise ProvenanceViolation(
            f"MSRB platform token count {n} != allowed {emma_allowed} in {where}"
        )


def _relpath(path: Path, root: Path | None) -> str | None:
    if root is None:
        return None
    try:
        return path.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return None


def _write_bytes(path: Path, text: str) -> bytes:
    """UTF-8, no BOM, LF only."""
    if "\r" in text:
        raise ProvenanceViolation(f"CR found in content for {path}; files are LF only")
    data = text.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def _finish(
    path: Path,
    data: bytes,
    *,
    sha256_body: str,
    kind: str,
    root: Path | None,
    manifest: PackManifest | None,
    created_from: list[str],
) -> WrittenFile:
    written = WrittenFile(
        path=path,
        relpath=_relpath(path, root if root is not None else (manifest.pack_root if manifest else None)),
        sha256=sha256_bytes(data),
        sha256_body=sha256_body,
        size=len(data),
        kind=kind,
    )
    if manifest is not None:
        manifest.add_file(written, created_from=created_from)
    return written


def _yaml_scalar(value: Any) -> str:
    """JSON encoding is valid YAML for scalars; keeps colons and quotes safe."""
    if isinstance(value, bool | int) or value is None:
        return json.dumps(value)
    return json.dumps(str(value), ensure_ascii=False)


def _frontmatter(envelope: Envelope) -> list[str]:
    lines = [
        "---",
        f"source: {envelope.source}",
        f"generator_version: {envelope.generator_version}",
        f"lab_version: {envelope.lab_version}",
        f"scenario_id: {envelope.scenario_id}",
        f"seed: {envelope.seed}",
        f"sha256_body: {envelope.sha256_body}",
    ]
    if envelope.created_from:
        lines.append("created_from:")
        lines.extend(f"  - {_yaml_scalar(item)}" for item in envelope.created_from)
    else:
        lines.append("created_from: []")
    lines.append("---")
    return lines


def _interleave_legend(lines: list[str], every: int) -> list[str]:
    """Insert the legend blockquote every `every` lines, never inside a fenced block."""
    out: list[str] = []
    since = 0
    in_fence = False
    pending = False
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
        out.append(line)
        since += 1
        if since >= every:
            pending = True
        if pending and not in_fence:
            out.extend(["", f"> {law.LEGEND}", ""])
            since = 0
            pending = False
    return out


# --------------------------------------------------------------------------------------
# Writers
# --------------------------------------------------------------------------------------


def write_md(
    path: Path,
    body: str,
    envelope: Envelope,
    *,
    banner: str | None = None,
    emma_allowed: int = 0,
    manifest: PackManifest | None = None,
    root: Path | None = None,
) -> WrittenFile:
    path = Path(path)
    _check_path(path)
    body = body.rstrip("\n")
    sha_body = sha256_text(body)
    env = envelope.model_copy(update={"sha256_body": sha_body})
    lines = _frontmatter(env) + ["", f"> {law.LEGEND}", ""]
    if banner:
        lines += [banner.rstrip("\n"), ""]
    body_lines = body.split("\n") if body else []
    if len(body_lines) > law.LEGEND_EVERY_N_LINES:
        body_lines = _interleave_legend(body_lines, law.LEGEND_EVERY_N_LINES)
    lines += body_lines + ["", law.LEGEND]
    text = "\n".join(lines) + "\n"
    _check_content(text, where=path, emma_allowed=emma_allowed)
    data = _write_bytes(path, text)
    return _finish(
        path, data, sha256_body=sha_body, kind="md", root=root, manifest=manifest,
        created_from=list(env.created_from),
    )


def write_txt(
    path: Path,
    body: str,
    envelope: Envelope,
    *,
    emma_allowed: int = 0,
    manifest: PackManifest | None = None,
    root: Path | None = None,
) -> WrittenFile:
    """Intake `.txt`: `# key: value` envelope lines, the legend line, then the content."""
    path = Path(path)
    _check_path(path)
    body = body.rstrip("\n")
    sha_body = sha256_text(body)
    env = envelope.model_copy(update={"sha256_body": sha_body})
    lines = [f"# {line}" for line in env.as_lines()] + [law.LEGEND] + body.split("\n")
    text = "\n".join(lines) + "\n"
    _check_content(text, where=path, emma_allowed=emma_allowed)
    data = _write_bytes(path, text)
    return _finish(
        path, data, sha256_body=sha_body, kind="txt", root=root, manifest=manifest,
        created_from=list(env.created_from),
    )


def write_vault_txt(
    path: Path,
    label: str,
    body: str,
    envelope: Envelope,
    *,
    emma_allowed: int = 0,
    manifest: PackManifest | None = None,
    root: Path | None = None,
) -> WrittenFile:
    """Vault `.txt`: label (line 1, indexed by run.py), legend (line 2), envelope, content."""
    path = Path(path)
    _check_path(path)
    if "\n" in label or not label.strip():
        raise ProvenanceViolation(f"vault label must be one non-empty line: {label!r}")
    body = body.rstrip("\n")
    sha_body = sha256_text(body)
    env = envelope.model_copy(update={"sha256_body": sha_body})
    lines = [label, law.LEGEND] + [f"# {line}" for line in env.as_lines()] + body.split("\n")
    text = "\n".join(lines) + "\n"
    _check_content(text, where=path, emma_allowed=emma_allowed)
    data = _write_bytes(path, text)
    return _finish(
        path, data, sha256_body=sha_body, kind="vault_txt", root=root, manifest=manifest,
        created_from=list(env.created_from),
    )


def write_json(
    path: Path,
    payload: dict[str, Any],
    envelope: Envelope,
    *,
    emma_allowed: int = 0,
    manifest: PackManifest | None = None,
    root: Path | None = None,
) -> WrittenFile:
    """`_legend` + `_provenance` + payload, canonical JSON."""
    path = Path(path)
    _check_path(path)
    bad = [k for k in payload if k.startswith("_")]
    if bad:
        raise ProvenanceViolation(f"payload keys may not start with '_': {bad}")
    sha_body = sha256_text(canonical_json(payload))
    env = envelope.model_copy(update={"sha256_body": sha_body})
    doc = {"_legend": law.LEGEND, "_provenance": env.model_dump(mode="json"), **payload}
    text = canonical_json(doc)
    _check_content(text, where=path, emma_allowed=emma_allowed)
    data = _write_bytes(path, text)
    return _finish(
        path, data, sha256_body=sha_body, kind="json", root=root, manifest=manifest,
        created_from=list(env.created_from),
    )


def write_csv(
    path: Path,
    header: list[str],
    rows: list[dict[str, Any]] | list[list[Any]],
    envelope: Envelope,
    *,
    emma_allowed: int = 0,
    manifest: PackManifest | None = None,
    root: Path | None = None,
) -> tuple[WrittenFile, WrittenFile]:
    """CSV (no comment row; DictReader-safe) plus its `<file>.provenance.json` sidecar."""
    path = Path(path)
    _check_path(path)
    if path.suffix.lower() != ".csv":
        raise ProvenanceViolation(f"write_csv needs a .csv path: {path}")
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        if isinstance(row, dict):
            extra = set(row) - set(header)
            if extra:
                raise ProvenanceViolation(f"row carries columns outside the header: {sorted(extra)}")
            writer.writerow([row.get(col, "") for col in header])
        else:
            if len(row) != len(header):
                raise ProvenanceViolation(f"row length {len(row)} != header length {len(header)}")
            writer.writerow(list(row))
    text = buf.getvalue()
    _check_content(text, where=path, emma_allowed=emma_allowed)
    data = _write_bytes(path, text)
    sha_body = sha256_bytes(data)
    env = envelope.model_copy(update={"sha256_body": sha_body})
    main = _finish(
        path, data, sha256_body=sha_body, kind="csv", root=root, manifest=manifest,
        created_from=list(env.created_from),
    )
    sidecar_path = path.with_name(path.name + law.CSV_SIDECAR_SUFFIX)
    _check_path(sidecar_path, sidecar=True)
    sidecar_doc = {
        "_legend": law.LEGEND,
        "_provenance": env.model_dump(mode="json"),
        "for_file": path.name,
        "columns": list(header),
        "rows": len(rows),
        "sha256": main.sha256,
    }
    sidecar_text = canonical_json(sidecar_doc)
    _check_content(sidecar_text, where=sidecar_path, emma_allowed=0)
    sidecar_data = _write_bytes(sidecar_path, sidecar_text)
    sidecar = _finish(
        sidecar_path, sidecar_data, sha256_body=sha256_text(canonical_json(sidecar_doc)),
        kind="csv_sidecar", root=root, manifest=manifest, created_from=[path.name],
    )
    return main, sidecar


# --------------------------------------------------------------------------------------
# Pack manifest
# --------------------------------------------------------------------------------------


class PackManifest:
    """`packs/<deal_id>/PACK-MANIFEST.json`: every file (sha256, created_from) + absences."""

    def __init__(self, pack_root: Path, envelope: Envelope) -> None:
        self.pack_root = Path(pack_root)
        self.envelope = envelope
        self.files: list[dict[str, Any]] = []
        self.absent_by_scenario: list[dict[str, Any]] = []

    @property
    def path(self) -> Path:
        return self.pack_root / law.PACK_MANIFEST_NAME

    def add_file(self, written: WrittenFile, *, created_from: list[str]) -> None:
        rel = _relpath(written.path, self.pack_root)
        if rel is None:
            raise ProvenanceViolation(f"{written.path} is outside the pack root {self.pack_root}")
        if rel == law.PACK_MANIFEST_NAME:
            return
        if any(entry["path"] == rel for entry in self.files):
            raise ProvenanceViolation(f"manifest already lists {rel}")
        self.files.append(
            {
                "path": rel,
                "kind": written.kind,
                "sha256": written.sha256,
                "sha256_body": written.sha256_body,
                "size": written.size,
                "created_from": list(created_from),
            }
        )

    def add_absent(self, **entry: Any) -> None:
        if "status" not in entry:
            entry["status"] = "absent_by_scenario"
        if "reason" not in entry or not str(entry["reason"]).strip():
            raise ProvenanceViolation("absent_by_scenario entries need a reason")
        self.absent_by_scenario.append(dict(entry))

    def payload(self) -> dict[str, Any]:
        return {
            "deal_id": self.envelope.scenario_id,
            "files": sorted(self.files, key=lambda e: e["path"]),
            "absent_by_scenario": sorted(
                self.absent_by_scenario, key=lambda e: json.dumps(e, sort_keys=True)
            ),
        }

    def save(self) -> WrittenFile:
        return write_json(self.path, self.payload(), self.envelope)

    @classmethod
    def load(cls, pack_root: Path) -> dict[str, Any]:
        """Read a committed manifest (data only; no re-registration)."""
        return json.loads((Path(pack_root) / law.PACK_MANIFEST_NAME).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------
# Audit (used by S02 and the pack fences to walk legend/envelope by construction)
# --------------------------------------------------------------------------------------


def audit_file(path: Path, *, emma_allowed: int = 0) -> list[str]:
    """Problems with a written file's stamping (empty list == conforms)."""
    path = Path(path)
    problems: list[str] = []
    try:
        _check_path(path, sidecar=path.name.endswith(law.CSV_SIDECAR_SUFFIX))
    except ProvenanceViolation as exc:
        problems.append(str(exc))
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        problems.append("BOM present")
    if b"\r" in data:
        problems.append("CR present (LF only)")
    text = data.decode("utf-8")
    try:
        _check_content(text, where=path, emma_allowed=emma_allowed)
    except ProvenanceViolation as exc:
        problems.append(str(exc))
    lines = text.split("\n")
    suffix = path.suffix.lower()
    if path.name.endswith(law.CSV_SIDECAR_SUFFIX) or suffix == ".json":
        doc = json.loads(text)
        if doc.get("_legend") != law.LEGEND:
            problems.append("_legend missing or not verbatim")
        if not isinstance(doc.get("_provenance"), dict):
            problems.append("_provenance missing")
    elif suffix == ".md":
        if lines[0] != "---" or "---" not in lines[1:]:
            problems.append("frontmatter missing")
        else:
            end = lines.index("---", 1)
            if not any(line.startswith("sha256_body: ") for line in lines[1:end]):
                problems.append("frontmatter lacks sha256_body")
            after = [line for line in lines[end + 1 :] if line.strip()]
            if not after or after[0] != f"> {law.LEGEND}":
                problems.append("legend is not the first blockquote after the frontmatter")
        if text.rstrip("\n").split("\n")[-1] != law.LEGEND:
            problems.append("legend is not the last line")
    elif suffix == ".txt":
        if lines[0].startswith("# source: "):
            envelope_lines = [line for line in lines if line.startswith("# ")]
            if len(envelope_lines) < 7:
                problems.append("intake envelope incomplete")
            if lines[len(envelope_lines)] != law.LEGEND:
                problems.append("legend must follow the intake envelope")
        else:
            if len(lines) < 2 or lines[1] != law.LEGEND:
                problems.append("vault file: legend must be line 2")
            if not lines[0].strip():
                problems.append("vault file: label line empty")
    elif suffix == ".csv":
        sidecar = path.with_name(path.name + law.CSV_SIDECAR_SUFFIX)
        if not sidecar.is_file():
            problems.append("csv sidecar missing")
        elif json.loads(sidecar.read_text(encoding="utf-8")).get("sha256") != sha256_bytes(data):
            problems.append("csv sidecar sha256 mismatch")
    return problems


__all__ = [
    "PackManifest",
    "ProvenanceViolation",
    "WrittenFile",
    "audit_file",
    "canonical_json",
    "sha256_bytes",
    "sha256_file",
    "sha256_text",
    "tree_sha256",
    "write_csv",
    "write_json",
    "write_md",
    "write_txt",
    "write_vault_txt",
]
