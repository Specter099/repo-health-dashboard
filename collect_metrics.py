#!/usr/bin/env python3
"""
scripts/collect_metrics.py
Fetches repo health metrics from GitHub API for all Specter099 repos.
Writes metrics.json to dist/ for the dashboard builder.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests  # type: ignore[import-untyped]
from dateutil import parser as dateparser  # type: ignore[import-untyped]

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not GITHUB_TOKEN:
    print("ERROR: GITHUB_TOKEN environment variable is required", file=sys.stderr)
    sys.exit(1)
USERNAME = os.environ.get("GITHUB_USERNAME", "Specter099")
OUTPUT_DIR = Path("dist")
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Repos to skip (forks, archived, etc.)
SKIP_REPOS: set[str] = set()  # add repo names here to exclude


def gh_get(url: str, params: dict | None = None) -> dict | list:
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    if r.status_code == 404:
        return {}
    r.raise_for_status()
    return r.json()


def paginate(url: str, params: dict | None = None) -> list:
    """Fetch all pages from a GitHub list endpoint."""
    results: list[dict] = []
    page = 1
    while True:
        p = {**(params or {}), "per_page": 100, "page": page}
        data = gh_get(url, p)
        if not data:
            break
        results.extend(data)
        if len(data) < 100:
            break
        page += 1
    return results


def age_days(dt_str: str) -> int:
    if not dt_str:
        return 9999
    dt = dateparser.parse(dt_str)
    now = datetime.now(timezone.utc)
    return (now - dt).days


def staleness_label(days: int) -> str:
    if days < 30:
        return "fresh"
    if days < 90:
        return "recent"
    if days < 180:
        return "aging"
    if days < 365:
        return "stale"
    return "dormant"


def collect_repo_metrics(repo: dict) -> dict:
    name = repo["name"]
    full_name = repo["full_name"]
    base = f"https://api.github.com/repos/{full_name}"

    print(f"  Analyzing: {name}", flush=True)

    # Branches
    branches = paginate(f"{base}/branches")
    branch_names = [b["name"] for b in branches]
    default_branch = repo.get("default_branch", "main")

    # Stale branches (last commit > 60 days ago)
    stale_branches = []
    for b in branches:
        if b["name"] in (default_branch, "main", "master", "develop"):
            continue
        commit_info = gh_get(b["commit"]["url"])
        if isinstance(commit_info, dict):
            committed_at = (
                commit_info.get("commit", {}).get("committer", {}).get("date", "")
            )
            if committed_at and age_days(committed_at) > 60:
                stale_branches.append(
                    {
                        "name": b["name"],
                        "age_days": age_days(committed_at),
                    }
                )

    # Open PRs
    open_prs = paginate(f"{base}/pulls", {"state": "open"})
    pr_list = [
        {
            "number": pr["number"],
            "title": pr["title"][:60],
            "age_days": age_days(pr["created_at"]),
            "draft": pr.get("draft", False),
        }
        for pr in open_prs
    ]

    # Open issues (excluding PRs)
    open_issues_raw = gh_get(f"{base}/issues", {"state": "open", "per_page": 30})
    if isinstance(open_issues_raw, list):
        open_issues = [i for i in open_issues_raw if "pull_request" not in i]
    else:
        open_issues = []

    # Branch protection on default branch
    branch_protection = False
    bp = gh_get(f"{base}/branches/{default_branch}/protection")
    if isinstance(bp, dict) and "url" in bp:
        branch_protection = True

    # Last commit on default branch
    commits = gh_get(f"{base}/commits", {"per_page": 1})
    last_commit_date = ""
    last_commit_sha = ""
    if isinstance(commits, list) and commits:
        last_commit_date = (
            commits[0].get("commit", {}).get("committer", {}).get("date", "")
        )
        last_commit_sha = commits[0].get("sha", "")[:7]

    # Secret scanning status
    secret_scanning = False
    ss = gh_get(f"{base}/secret-scanning/alerts", {"state": "open", "per_page": 1})
    if isinstance(ss, list):
        secret_scanning = True  # endpoint accessible = feature enabled

    # Topics / languages
    topics = repo.get("topics", [])
    language = repo.get("language", "")

    # Dependabot alerts (if accessible)
    dependabot_count = 0
    da = gh_get(f"{base}/dependabot/alerts", {"state": "open", "per_page": 100})
    if isinstance(da, list):
        dependabot_count = len(da)

    commit_age = age_days(last_commit_date)

    return {
        "name": name,
        "full_name": full_name,
        "url": repo["html_url"],
        "description": repo.get("description") or "",
        "language": language,
        "topics": topics,
        "default_branch": default_branch,
        "private": repo.get("private", False),
        "archived": repo.get("archived", False),
        "fork": repo.get("fork", False),
        "stars": repo.get("stargazers_count", 0),
        "open_issues_count": len(open_issues),
        "open_prs": pr_list,
        "open_pr_count": len(pr_list),
        "stale_branches": stale_branches,
        "stale_branch_count": len(stale_branches),
        "branch_count": len(branch_names),
        "branch_protection": branch_protection,
        "secret_scanning": secret_scanning,
        "dependabot_alerts": dependabot_count,
        "last_commit_date": last_commit_date,
        "last_commit_sha": last_commit_sha,
        "commit_age_days": commit_age,
        "staleness": staleness_label(commit_age),
        "has_license": repo.get("license") is not None,
        "has_description": bool(repo.get("description")),
        "license": repo.get("license", {}).get("spdx_id", "")
        if repo.get("license")
        else "",
    }


def compute_health_score(repo: dict) -> int:
    """0–100 health score based on key hygiene metrics."""
    score = 100
    # (raw_deduction, max_deduction)
    deductions: list[tuple[int, int]] = [
        (repo["stale_branch_count"] * 5, 20),
        (repo["open_pr_count"] * 3, 15),
        (0 if repo["branch_protection"] else 10, 10),
        (0 if repo["has_license"] else 5, 5),
        (0 if repo["has_description"] else 3, 3),
        (repo["dependabot_alerts"] * 5, 20),
        (
            {"fresh": 0, "recent": 0, "aging": 5, "stale": 10, "dormant": 0}.get(
                repo["staleness"], 0
            ),
            10,
        ),
    ]
    for raw, cap in deductions:
        score -= min(raw, cap)
    return max(0, min(100, score))


def main():
    print(f"Collecting metrics for {USERNAME}...", flush=True)

    repos = paginate(
        f"https://api.github.com/users/{USERNAME}/repos", {"type": "owner"}
    )
    print(f"Found {len(repos)} repos", flush=True)

    # Filter: skip forks, archived, and explicitly excluded
    active_repos = [
        r
        for r in repos
        if not r.get("fork") and not r.get("archived") and r["name"] not in SKIP_REPOS
    ]
    print(
        f"Analyzing {len(active_repos)} active repos (skipped {len(repos) - len(active_repos)} forks/archived)",
        flush=True,
    )

    metrics = []
    for repo in active_repos:
        try:
            m = collect_repo_metrics(repo)
            m["health_score"] = compute_health_score(m)
            metrics.append(m)
        except Exception as e:
            print(
                f"  WARNING: Failed to collect metrics for {repo['name']}: {e}",
                file=sys.stderr,
            )

    # Sort by health score ascending (worst first in dashboard)
    metrics.sort(key=lambda r: r["health_score"])

    # Aggregate summary
    summary = {
        "total_repos": len(metrics),
        "avg_health_score": round(
            sum(r["health_score"] for r in metrics) / max(len(metrics), 1)
        ),
        "total_stale_branches": sum(r["stale_branch_count"] for r in metrics),
        "total_open_prs": sum(r["open_pr_count"] for r in metrics),
        "total_open_issues": sum(r["open_issues_count"] for r in metrics),
        "total_dependabot_alerts": sum(r["dependabot_alerts"] for r in metrics),
        "repos_with_protection": sum(1 for r in metrics if r["branch_protection"]),
        "repos_without_license": sum(1 for r in metrics if not r["has_license"]),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "username": USERNAME,
    }

    output = {"summary": summary, "repos": metrics}
    out_path = OUTPUT_DIR / "metrics.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nMetrics written to {out_path}")
    print(f"Summary: {json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()
