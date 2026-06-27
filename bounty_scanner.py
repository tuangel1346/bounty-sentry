#!/usr/bin/env python3
"""Rank GitHub bounty issues and surface common trust/competition risks."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path


API = "https://api.github.com"
SUSPICIOUS_TERMS = (
    "bounty-hunters",
    "bug-bounty",
    "shadow-arena",
    "bounty-forge",
    "test-bounty",
)


@dataclass(frozen=True)
class Candidate:
    score: int
    repository: str
    title: str
    url: str
    comments: int
    stars: int
    reward_usd: int | None
    assignees: tuple[str, ...]
    warnings: tuple[str, ...]


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token
        self.cache: dict[str, dict] = {}

    def get(self, path: str) -> dict:
        if path in self.cache:
            return self.cache[path]
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "bounty-sentry",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(f"{API}{path}", headers=headers)
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.load(response)
        self.cache[path] = result
        return result


def reward_from(text: str) -> int | None:
    match = re.search(r"(?:USD|US\$|\$)\s*([0-9][0-9,]*(?:\.\d{1,2})?)", text, re.I)
    return round(float(match.group(1).replace(",", ""))) if match else None


def score_candidate(issue: dict, repository: dict, today: dt.date) -> Candidate:
    warnings: list[str] = []
    full_name = repository["full_name"]
    lowered = full_name.lower()
    created = dt.date.fromisoformat(repository["created_at"][:10])
    stars = repository.get("stargazers_count", 0)
    assignees = tuple(user["login"] for user in issue.get("assignees", []))

    if any(term in lowered for term in SUSPICIOUS_TERMS):
        warnings.append("bounty-farm naming pattern")
    if repository.get("fork"):
        warnings.append("repository is a fork")
    if repository.get("archived"):
        warnings.append("repository is archived")
    if stars < 10:
        warnings.append("fewer than 10 stars")
    if (today - created).days < 180:
        warnings.append("repository is under 180 days old")
    if assignees:
        warnings.append("issue already assigned")
    if issue.get("comments", 0) >= 10:
        warnings.append("high competition")

    reward = reward_from(f'{issue["title"]} {issue.get("body") or ""}')
    score = min(stars, 100) - issue.get("comments", 0) * 4 - len(warnings) * 25
    if reward:
        score += min(reward // 100, 30)
    if repository.get("has_discussions"):
        score += 5

    return Candidate(
        score=score,
        repository=full_name,
        title=issue["title"],
        url=issue["html_url"],
        comments=issue.get("comments", 0),
        stars=stars,
        reward_usd=reward,
        assignees=assignees,
        warnings=tuple(warnings),
    )


def search(client: GitHubClient, *, days: int, limit: int) -> list[Candidate]:
    since = dt.date.today() - dt.timedelta(days=days)
    query = f'is:issue is:open label:bounty created:>={since.isoformat()}'
    path = "/search/issues?" + urllib.parse.urlencode(
        {"q": query, "sort": "updated", "order": "desc", "per_page": min(limit, 100)}
    )
    issues = client.get(path).get("items", [])[:limit]
    candidates = []
    for issue in issues:
        repository_name = "/".join(issue["repository_url"].split("/")[-2:])
        repository = client.get(f"/repos/{repository_name}")
        candidates.append(score_candidate(issue, repository, dt.date.today()))
    return sorted(candidates, key=lambda item: item.score, reverse=True)


def markdown_report(candidates: list[Candidate]) -> str:
    lines = [
        "# Bounty Sentry report",
        "",
        "Scores are triage signals, not payment guarantees.",
        "",
        "| Score | Reward | Repository | Competition | Warnings |",
        "|---:|---:|---|---:|---|",
    ]
    for item in candidates:
        reward = f"${item.reward_usd:,}" if item.reward_usd is not None else "Unverified"
        warnings = ", ".join(item.warnings) or "None detected"
        lines.append(
            f"| {item.score} | {reward} | [{item.repository}]({item.url}) | "
            f"{item.comments} comments | {warnings} |"
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=90, help="search window (default: 90)")
    parser.add_argument("--limit", type=int, default=20, help="maximum issues (default: 20)")
    parser.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    parser.add_argument("--output", type=Path, help="write the report to a file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.days < 1 or not 1 <= args.limit <= 100:
        raise SystemExit("--days must be positive and --limit must be between 1 and 100")
    client = GitHubClient(os.environ.get("GITHUB_TOKEN"))
    candidates = search(client, days=args.days, limit=args.limit)

    if args.format == "json":
        report = json.dumps([asdict(item) for item in candidates], indent=2) + "\n"
    elif args.format == "markdown":
        report = markdown_report(candidates)
    else:
        chunks = []
        for item in candidates:
            reward = f"${item.reward_usd:,}" if item.reward_usd is not None else "unverified"
            chunks.append(f"[{item.score:>3}] {item.repository} | {reward} | {item.title}\n      {item.url}")
            if item.warnings:
                chunks[-1] += f"\n      warnings: {', '.join(item.warnings)}"
        report = "\n".join(chunks) + ("\n" if chunks else "")

    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
