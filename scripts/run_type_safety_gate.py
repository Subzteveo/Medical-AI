from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", required=True)
    args = parser.parse_args()

    revision_run = _run(["git", "rev-parse", "HEAD"])
    revision = str(revision_run["stdout"]).strip() if revision_run["returncode"] == 0 else "UNKNOWN"

    checks = [
        _run(["python", "-m", "pyright", "--project", "pyproject.toml"]),
        _run(["python", "scripts/verify_influence_boundary.py"]),
    ]
    passed = all(check["returncode"] == 0 for check in checks)

    report = {
        "schema_version": "medical-ai-type-safety-evidence-v0.1",
        "revision": revision,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "authoritative medical influence control path",
        "claims": {
            "strict_static_typing": "PASSED" if checks[0]["returncode"] == 0 else "FAILED",
            "no_untyped_alternate_render_or_capability_path": (
                "PASSED" if checks[1]["returncode"] == 0 else "FAILED"
            ),
        },
        "checks": checks,
        "verdict": "PASSED" if passed else "FAILED",
        "limitations": [
            "This is revision-bound engineering evidence, not proof of medical correctness.",
            "The guard proves properties of the inspected source revision and cannot authorize future revisions.",
            "Runtime external inputs still require validation at their explicit trust boundaries.",
        ],
    }

    output = Path(args.json_out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for check in checks:
        print("$ " + " ".join(str(part) for part in check["command"]))
        if check["stdout"]:
            print(check["stdout"], end="")
        if check["stderr"]:
            print(check["stderr"], end="")
    print(f"Type-safety evidence: {report['verdict']} for {revision}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
