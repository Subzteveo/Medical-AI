#!/usr/bin/env python3
"""Local, read-only preflight for a Medical AI coding session.

This checks local revision hygiene only. It cannot establish GitHub enforcement,
medical safety, independent validation, external access, or release authority.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REQUIRED_FILES = (
    "AGENTS.md",
    "README.md",
    "project_docs/NORTH_STAR.md",
    "project_docs/PROJECT_INDEX.md",
    "project_docs/STATUS.md",
    "project_docs/DEVELOPMENT_WORKFLOW.md",
    "docs/INTENDED_USE.md",
    "docs/INFLUENCE_CONTROL_CORE_v0.2.md",
    "docs/RELEASE_READINESS.md",
)


def git(repo: Path, *args: str) -> tuple[bool, str]:
    try:
        process = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    return process.returncode == 0, process.stdout.strip()


def inspect(repo: Path, expected_sha: str) -> dict[str, object]:
    repo = repo.resolve()
    root_ok, detected_root = git(repo, "rev-parse", "--show-toplevel")
    sha_ok, sha = git(repo, "rev-parse", "HEAD")
    status_ok, status = git(repo, "status", "--porcelain", "--untracked-files=all")
    at_root = root_ok and Path(detected_root).resolve() == repo
    clean = status_ok and not status
    matching = sha_ok and sha == expected_sha
    missing = [name for name in REQUIRED_FILES if not (repo / name).is_file()]

    blockers: list[str] = []
    if not at_root:
        blockers.append("not_a_git_repository_root")
    if not matching:
        blockers.append("head_does_not_match_expected_sha")
    if not clean:
        blockers.append("working_tree_not_clean_or_unavailable")
    if missing:
        blockers.append("required_contract_file_missing")

    return {
        "schema": "medical-ai.local-preflight/1",
        "expected_sha": expected_sha,
        "observed_sha": sha if sha_ok else None,
        "repository_root_verified": at_root,
        "head_matches": matching,
        "working_tree_clean": clean,
        "missing_contract_files": missing,
        "local_preflight": "PASS" if not blockers else "FAIL",
        "blockers": blockers,
        "github_required_pr_and_ci": "UNVERIFIED",
        "independent_medical_validation": "NOT_EVALUATED",
        "deployment_and_release_authority": "NOT_EVALUATED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--expected-sha", required=True, help="40-character exact Git commit SHA")
    args = parser.parse_args()
    if re.fullmatch(r"[0-9a-f]{40}", args.expected_sha) is None:
        parser.error("--expected-sha must be a 40-character lowercase hex commit SHA")
    report = inspect(args.repo, args.expected_sha)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["local_preflight"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
