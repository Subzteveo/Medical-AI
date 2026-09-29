"""Targeted credential and forbidden tracked-artifact check; not a PHI audit."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = (
    ("private key", re.compile(rb"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("cloud key", re.compile(rb"\b(?:AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35})\b")),
)


def tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=False
    )
    if result.returncode == 0:
        return [name for name in result.stdout.decode("utf-8").split("\0") if name]
    # Allows a local check of an unpacked source tree before it is committed.
    ignored = {".venv", ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
    return [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()
            and not any(part in ignored or part.endswith(".egg-info") for part in p.parts)]


def main() -> int:
    failures: list[str] = []
    paths = tracked_paths()
    for name in paths:
        path = PurePosixPath(name)
        parts = set(path.parts)
        suffix = path.suffix.lower()
        if ("build" in parts or "dist" in parts or "__pycache__" in parts
                or any(p.endswith(".egg-info") for p in parts)
                or suffix in {".sqlite", ".sqlite3", ".db", ".pem", ".key"}
                or path.name == ".env" or path.name.startswith(".env.")):
            failures.append(f"Forbidden tracked artifact: {name}")
            continue
        file = ROOT / name
        if not file.is_file() or file.is_symlink():
            failures.append(f"Nonregular tracked file: {name}")
            continue
        data = file.read_bytes()
        if b"\0" in data:
            failures.append(f"Binary tracked file requires review: {name}")
            continue
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(data):
                failures.append(f"Possible {label} in {name}")
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        return 1
    print(f"Targeted hygiene checks passed for {len(paths)} tracked files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
