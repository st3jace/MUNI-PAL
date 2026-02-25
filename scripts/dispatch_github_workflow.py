"""
Dispatch and optionally poll a GitHub Actions workflow without relying on gh CLI.

The script resolves auth token in this order:
1) GH_TOKEN / GITHUB_TOKEN / GITHUB_PAT environment variable
2) git credential helper entry for github.com

Usage:
    python scripts/dispatch_github_workflow.py --workflow-id phase10-postlaunch-dispatch.yml --ref master --input note="weekly run"
    python scripts/dispatch_github_workflow.py --workflow-id phase10-postlaunch-dispatch.yml --ref master --wait --require-success
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

API_BASE = "https://api.github.com"
DEFAULT_POLL_INTERVAL_SECONDS = 10
DEFAULT_DISCOVERY_TIMEOUT_SECONDS = 300
DEFAULT_COMPLETION_TIMEOUT_SECONDS = 3600


@dataclass
class DispatchResult:
    owner: str
    repo: str
    workflow_id: str
    run_id: int
    run_url: str
    status: str
    conclusion: str | None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_git(*args: str, input_text: str | None = None) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=_repo_root(),
        text=True,
        input=input_text,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


def _parse_owner_repo(remote_url: str) -> tuple[str, str]:
    text = remote_url.strip()
    if text.startswith("https://github.com/"):
        suffix = text[len("https://github.com/") :]
    elif text.startswith("http://github.com/"):
        suffix = text[len("http://github.com/") :]
    elif text.startswith("git@github.com:"):
        suffix = text[len("git@github.com:") :]
    else:
        raise ValueError(f"Unsupported GitHub remote URL format: {remote_url}")
    if suffix.endswith(".git"):
        suffix = suffix[:-4]
    parts = [p for p in suffix.split("/") if p]
    if len(parts) != 2:
        raise ValueError(f"Could not parse owner/repo from remote URL: {remote_url}")
    return parts[0], parts[1]


def _resolve_owner_repo(repo_override: str | None) -> tuple[str, str]:
    if repo_override:
        text = repo_override.strip()
        if "/" not in text:
            raise ValueError("--repo must be in owner/repo format")
        owner, repo = text.split("/", 1)
        owner = owner.strip()
        repo = repo.strip()
        if not owner or not repo:
            raise ValueError("--repo must be in owner/repo format")
        return owner, repo
    remote = _run_git("remote", "get-url", "origin")
    return _parse_owner_repo(remote)


def _resolve_token() -> str:
    for key in ("GH_TOKEN", "GITHUB_TOKEN", "GITHUB_PAT"):
        value = os.environ.get(key, "").strip()
        if value:
            return value

    try:
        credential_output = _run_git(
            "credential",
            "fill",
            input_text="protocol=https\nhost=github.com\n\n",
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("Unable to resolve GitHub token from git credential helper.") from exc

    fields: dict[str, str] = {}
    for line in credential_output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        fields[key.strip()] = value.strip()
    token = fields.get("password", "").strip()
    if not token:
        raise RuntimeError(
            "No GitHub token found. Set GH_TOKEN/GITHUB_TOKEN or configure git credential helper."
        )
    return token


def _github_request(
    *,
    method: str,
    path: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any] | None]:
    url = f"{API_BASE}{path}"
    body_bytes = None
    if payload is not None:
        body_bytes = json.dumps(payload).encode("utf-8")
    request = Request(
        url=url,
        data=body_bytes,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "muni-pal-dispatch-tool",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=60) as response:
            raw = response.read()
            status = int(response.status)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed ({exc.code} {exc.reason}): {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"GitHub API request failed: {exc.reason}") from exc

    if not raw:
        return status, None
    try:
        return status, json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return status, None


def _current_head_sha(ref: str) -> str:
    return _run_git("rev-parse", ref).strip()


def _list_workflow_runs(
    *,
    owner: str,
    repo: str,
    workflow_id: str,
    branch: str,
    token: str,
) -> list[dict[str, Any]]:
    encoded_workflow_id = quote(workflow_id, safe="")
    path = (
        f"/repos/{owner}/{repo}/actions/workflows/{encoded_workflow_id}/runs"
        f"?per_page=30&branch={quote(branch, safe='')}&event=workflow_dispatch"
    )
    _, payload = _github_request(method="GET", path=path, token=token)
    if not isinstance(payload, dict):
        return []
    runs = payload.get("workflow_runs", [])
    if isinstance(runs, list):
        return [run for run in runs if isinstance(run, dict)]
    return []


def _dispatch_workflow(
    *,
    owner: str,
    repo: str,
    workflow_id: str,
    ref: str,
    inputs: dict[str, str],
    token: str,
) -> None:
    encoded_workflow_id = quote(workflow_id, safe="")
    path = f"/repos/{owner}/{repo}/actions/workflows/{encoded_workflow_id}/dispatches"
    payload: dict[str, Any] = {"ref": ref}
    if inputs:
        payload["inputs"] = inputs
    status, _ = _github_request(method="POST", path=path, token=token, payload=payload)
    if status != 204:
        raise RuntimeError(f"Unexpected dispatch response status: {status}")


def _parse_github_time(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _discover_new_run(
    *,
    owner: str,
    repo: str,
    workflow_id: str,
    ref: str,
    token: str,
    baseline_ids: set[int],
    head_sha: str,
    dispatched_after: datetime,
    timeout_seconds: int,
    poll_interval_seconds: int,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        runs = _list_workflow_runs(
            owner=owner,
            repo=repo,
            workflow_id=workflow_id,
            branch=ref,
            token=token,
        )
        for run in runs:
            run_id = int(run.get("id", 0) or 0)
            if run_id <= 0:
                continue
            if run_id in baseline_ids:
                continue
            if str(run.get("head_sha", "")).strip() != head_sha:
                continue
            created_at = _parse_github_time(run.get("created_at"))
            if created_at is not None and created_at < dispatched_after:
                continue
            return run
        time.sleep(max(poll_interval_seconds, 1))
    raise TimeoutError(
        f"Timed out after {timeout_seconds}s waiting for newly dispatched workflow run."
    )


def _get_run(
    *,
    owner: str,
    repo: str,
    run_id: int,
    token: str,
) -> dict[str, Any]:
    path = f"/repos/{owner}/{repo}/actions/runs/{run_id}"
    _, payload = _github_request(method="GET", path=path, token=token)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid run payload for run {run_id}.")
    return payload


def dispatch_and_wait(
    *,
    owner: str,
    repo: str,
    workflow_id: str,
    ref: str,
    inputs: dict[str, str],
    token: str,
    wait: bool,
    require_success: bool,
    discovery_timeout_seconds: int,
    completion_timeout_seconds: int,
    poll_interval_seconds: int,
) -> DispatchResult:
    head_sha = _current_head_sha(ref)
    baseline_runs = _list_workflow_runs(
        owner=owner,
        repo=repo,
        workflow_id=workflow_id,
        branch=ref,
        token=token,
    )
    baseline_ids = {
        int(run.get("id", 0) or 0)
        for run in baseline_runs
        if int(run.get("id", 0) or 0) > 0
    }

    dispatched_after = datetime.now(UTC)
    _dispatch_workflow(
        owner=owner,
        repo=repo,
        workflow_id=workflow_id,
        ref=ref,
        inputs=inputs,
        token=token,
    )

    discovered = _discover_new_run(
        owner=owner,
        repo=repo,
        workflow_id=workflow_id,
        ref=ref,
        token=token,
        baseline_ids=baseline_ids,
        head_sha=head_sha,
        dispatched_after=dispatched_after,
        timeout_seconds=discovery_timeout_seconds,
        poll_interval_seconds=poll_interval_seconds,
    )
    run_id = int(discovered.get("id", 0))
    run_url = str(discovered.get("html_url", "")).strip()
    status = str(discovered.get("status", "unknown")).strip().lower()
    conclusion_raw = discovered.get("conclusion")
    conclusion = str(conclusion_raw).strip().lower() if conclusion_raw else None

    if wait:
        deadline = time.monotonic() + completion_timeout_seconds
        last_status = None
        last_conclusion = None
        while time.monotonic() < deadline:
            run_payload = _get_run(owner=owner, repo=repo, run_id=run_id, token=token)
            status = str(run_payload.get("status", "unknown")).strip().lower()
            conclusion_raw = run_payload.get("conclusion")
            conclusion = str(conclusion_raw).strip().lower() if conclusion_raw else None
            if status != last_status or conclusion != last_conclusion:
                print(
                    f"[workflow-dispatch] run_id={run_id} status={status} conclusion={conclusion}"
                )
                last_status = status
                last_conclusion = conclusion
            if status == "completed":
                break
            time.sleep(max(poll_interval_seconds, 1))
        else:
            raise TimeoutError(
                f"Timed out after {completion_timeout_seconds}s waiting for run {run_id} completion."
            )

    if require_success and status == "completed" and conclusion != "success":
        raise RuntimeError(
            f"Workflow run {run_id} completed with conclusion `{conclusion}` (expected `success`)."
        )

    return DispatchResult(
        owner=owner,
        repo=repo,
        workflow_id=workflow_id,
        run_id=run_id,
        run_url=run_url,
        status=status,
        conclusion=conclusion,
    )


def _parse_inputs(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid --input value `{value}`; expected key=value.")
        key, raw = value.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid --input value `{value}`; key is empty.")
        parsed[key] = raw
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dispatch and poll GitHub Actions workflow runs.")
    parser.add_argument("--workflow-id", required=True, help="Workflow file name or numeric workflow ID.")
    parser.add_argument("--ref", default="master", help="Git ref/branch to dispatch.")
    parser.add_argument(
        "--repo",
        default=None,
        help="Optional owner/repo override. Defaults to origin remote.",
    )
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Workflow dispatch input in key=value format (repeatable).",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for run completion.",
    )
    parser.add_argument(
        "--require-success",
        action="store_true",
        help="Fail when completed run conclusion is not success.",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Polling interval in seconds.",
    )
    parser.add_argument(
        "--discovery-timeout-seconds",
        type=int,
        default=DEFAULT_DISCOVERY_TIMEOUT_SECONDS,
        help="Timeout while waiting for dispatched run discovery.",
    )
    parser.add_argument(
        "--completion-timeout-seconds",
        type=int,
        default=DEFAULT_COMPLETION_TIMEOUT_SECONDS,
        help="Timeout while waiting for run completion.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        owner, repo = _resolve_owner_repo(args.repo)
        token = _resolve_token()
        inputs = _parse_inputs(args.input)
        result = dispatch_and_wait(
            owner=owner,
            repo=repo,
            workflow_id=str(args.workflow_id),
            ref=str(args.ref),
            inputs=inputs,
            token=token,
            wait=bool(args.wait),
            require_success=bool(args.require_success),
            discovery_timeout_seconds=max(int(args.discovery_timeout_seconds), 30),
            completion_timeout_seconds=max(int(args.completion_timeout_seconds), 60),
            poll_interval_seconds=max(int(args.poll_interval_seconds), 1),
        )
    except Exception as exc:  # noqa: BLE001 - CLI tool
        print(f"[workflow-dispatch] error: {exc}")
        return 1

    print(f"[workflow-dispatch] owner_repo={result.owner}/{result.repo}")
    print(f"[workflow-dispatch] workflow_id={result.workflow_id}")
    print(f"[workflow-dispatch] run_id={result.run_id}")
    print(f"[workflow-dispatch] run_url={result.run_url}")
    print(f"[workflow-dispatch] status={result.status}")
    print(f"[workflow-dispatch] conclusion={result.conclusion}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
