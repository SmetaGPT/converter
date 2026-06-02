from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from typing import Any

GITHUB_API = "https://api.github.com"
NIGHTLY_MARKER = "<!-- nightly-full-e2e -->"
AGENT_ID_RE = re.compile(r"(?im)^\s*[-*]?\s*agent_id(?:\(s\))?:\s*(.+?)\s*$")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a nightly failure issue with last merged PR context.")
    parser.add_argument("--repo", required=True, help="GitHub repository in owner/name format.")
    parser.add_argument("--run-id", required=True, help="GitHub Actions run ID.")
    parser.add_argument("--run-url", required=True, help="URL for the failing GitHub Actions run.")
    parser.add_argument("--workflow-name", default="nightly-full-e2e", help="Logical workflow name for the issue title.")
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")

    owner, repo = parse_repo(args.repo)
    run_payload = github_json(
        "GET",
        f"{GITHUB_API}/repos/{owner}/{repo}/actions/runs/{urllib.parse.quote(str(args.run_id))}",
        token,
    )
    jobs_payload = github_json(
        "GET",
        f"{GITHUB_API}/repos/{owner}/{repo}/actions/runs/{urllib.parse.quote(str(args.run_id))}/jobs?per_page=100",
        token,
    )
    latest_pr = fetch_latest_merged_pr(owner, repo, token)
    title = build_issue_title(args.workflow_name, run_payload)
    body = build_issue_body(
        workflow_name=args.workflow_name,
        run_payload=run_payload,
        run_url=args.run_url,
        jobs=jobs_payload.get("jobs", []),
        latest_pull_request=latest_pr,
    )

    existing_issue = find_existing_issue(owner, repo, token, title)
    if existing_issue is not None:
        print(
            json.dumps(
                {
                    "status": "exists",
                    "issue_number": existing_issue["number"],
                    "issue_url": existing_issue["html_url"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    issue_payload = github_json(
        "POST",
        f"{GITHUB_API}/repos/{owner}/{repo}/issues",
        token,
        payload={"title": title, "body": body},
    )
    print(
        json.dumps(
            {
                "status": "created",
                "issue_number": issue_payload["number"],
                "issue_url": issue_payload["html_url"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def parse_repo(repo: str) -> tuple[str, str]:
    owner, name = repo.split("/", 1)
    if not owner or not name:
        raise ValueError(f"Invalid repo: {repo}")
    return owner, name


def fetch_latest_merged_pr(owner: str, repo: str, token: str) -> dict[str, Any]:
    payload = github_json(
        "GET",
        f"{GITHUB_API}/repos/{owner}/{repo}/pulls?state=closed&base=main&sort=updated&direction=desc&per_page=50",
        token,
    )
    merged = [pull for pull in payload if isinstance(pull, dict) and pull.get("merged_at")]
    if not merged:
        raise RuntimeError("No merged pull requests found for main.")
    merged.sort(key=lambda pull: str(pull.get("merged_at")), reverse=True)
    return merged[0]


def infer_agent_id(pull_request: Mapping[str, Any]) -> tuple[str, str]:
    body = str(pull_request.get("body") or "")
    match = AGENT_ID_RE.search(body)
    if match:
        value = match.group(1).strip()
        if value and value not in {"-", "—"}:
            return value, "pr_body"

    head = pull_request.get("head")
    if isinstance(head, Mapping):
        head_ref = head.get("ref")
        if isinstance(head_ref, str) and head_ref.strip():
            return head_ref.strip(), "head_ref"

    user = pull_request.get("user")
    if isinstance(user, Mapping):
        login = user.get("login")
        if isinstance(login, str) and login.strip():
            return login.strip(), "author_login"

    return "unknown", "fallback_unknown"


def build_issue_title(workflow_name: str, run_payload: Mapping[str, Any]) -> str:
    run_date = str(run_payload.get("created_at") or "unknown-date")[:10]
    return f"Nightly full e2e failed on {run_date}"


def build_issue_body(
    *,
    workflow_name: str,
    run_payload: Mapping[str, Any],
    run_url: str,
    jobs: Sequence[Mapping[str, Any]],
    latest_pull_request: Mapping[str, Any],
) -> str:
    agent_id, agent_id_source = infer_agent_id(latest_pull_request)
    failed_jobs = [
        job
        for job in jobs
        if isinstance(job, Mapping)
        and str(job.get("conclusion") or "failure") not in {"success", "skipped"}
    ]

    latest_user = latest_pull_request.get("user")
    latest_head = latest_pull_request.get("head")

    lines = [
        NIGHTLY_MARKER,
        f"# Nightly workflow failure: {workflow_name}",
        "",
        "## Run",
        f"- workflow: {workflow_name}",
        f"- run_id: {run_payload.get('id')}",
        f"- event: {run_payload.get('event')}",
        f"- conclusion: {run_payload.get('conclusion')}",
        f"- head_sha: {run_payload.get('head_sha')}",
        f"- run_url: {run_url}",
        "",
        "## Last merged PR",
        f"- number: #{latest_pull_request.get('number')}",
        f"- title: {latest_pull_request.get('title')}",
        f"- merged_at: {latest_pull_request.get('merged_at')}",
        f"- merge_commit_sha: {latest_pull_request.get('merge_commit_sha')}",
        f"- agent_id: {agent_id}",
        f"- agent_id_source: {agent_id_source}",
        f"- author: {latest_user.get('login') if isinstance(latest_user, Mapping) else 'unknown'}",
        f"- head_ref: {latest_head.get('ref') if isinstance(latest_head, Mapping) else 'unknown'}",
        "",
        "## Non-success jobs",
    ]

    if failed_jobs:
        for job in failed_jobs:
            lines.append(f"- {job.get('name')}: {job.get('conclusion')}")
    else:
        lines.append("- GitHub Actions API did not return any non-success jobs for this run.")

    lines.extend(
        [
            "",
            "## Notes",
            "- Issue created automatically by nightly-full-e2e.",
            "- `agent_id` is taken from PR body when available; otherwise the helper falls back to `head_ref`, then author login for older merges.",
        ]
    )
    return "\n".join(lines) + "\n"


def find_existing_issue(owner: str, repo: str, token: str, title: str) -> dict[str, Any] | None:
    payload = github_json(
        "GET",
        f"{GITHUB_API}/repos/{owner}/{repo}/issues?state=open&per_page=100",
        token,
    )
    for issue in payload:
        if not isinstance(issue, dict) or issue.get("pull_request"):
            continue
        if issue.get("title") == title and NIGHTLY_MARKER in str(issue.get("body") or ""):
            return issue
    return None


def github_json(method: str, url: str, token: str, payload: Mapping[str, Any] | None = None) -> Any:
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "nightly-full-e2e-helper",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed: {exc.code} {error_body}") from exc


if __name__ == "__main__":
    raise SystemExit(main())