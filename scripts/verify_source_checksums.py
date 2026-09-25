"""Check the committed source manifest without changing it."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "provenance/SOURCE_SHA256SUMS"
SOURCE_PREFIXES = ("src/", "tests/", "policies/", "prompts/", "evals/")


def main() -> int:
    try:
        lines = MANIFEST.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        print(f"Cannot read source manifest: {exc}", file=sys.stderr)
        return 1
    paths: list[str] = []
    failures: list[str] = []
    for number, line in enumerate(lines, 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            failures.append(f"Malformed manifest line {number}")
            continue
        expected, name = match.groups()
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or name != path.as_posix():
            failures.append(f"Unsafe manifest path at line {number}")
            continue
        paths.append(name)
        target = ROOT / name
        if not target.is_file() or target.is_symlink():
            failures.append(f"Missing or nonregular source: {name}")
            continue
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            failures.append(f"Source checksum mismatch: {name}")
    if paths != sorted(set(paths)):
        failures.append("Manifest paths must be unique and sorted")
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        capture_output=True,
        check=False,
    )
    if tracked.returncode == 0:
        tracked_source = {
            name for name in tracked.stdout.decode("utf-8").split("\0") if name
            and (name.startswith(SOURCE_PREFIXES) or name == "pyproject.toml")
        }
        unlisted = tracked_source - set(paths)
        if unlisted:
            failures.append("Unlisted tracked source: " + ", ".join(sorted(unlisted)))
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        return 1
    print(f"Verified {len(paths)} source checksums (manifest unchanged).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
