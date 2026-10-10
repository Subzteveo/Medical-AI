from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITATIVE_FILES = (
    ROOT / "src/medical_ai/schemas.py",
    ROOT / "src/medical_ai/influence.py",
    ROOT / "src/medical_ai/engine.py",
    ROOT / "src/medical_ai/renderer.py",
    ROOT / "src/medical_ai/connectors/base.py",
)
RUNTIME_ROOT = ROOT / "src/medical_ai"
CAPABILITY_CONSTRUCTORS = {
    "InfluenceAuthorization",
    "InfluenceDecision",
    "AuthorizedClaimView",
}


def _name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _annotation_text(node: ast.AST | None) -> str:
    if node is None:
        return ""
    return ast.unparse(node)


def main() -> int:
    errors: list[str] = []

    for path in AUTHORITATIVE_FILES:
        text = path.read_text(encoding="utf-8")
        if "# type: ignore" in text or "# pyright: ignore" in text:
            errors.append(f"{path.relative_to(ROOT)}: type-ignore escape hatch is forbidden")
        tree = ast.parse(text, filename=str(path))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "typing":
                for alias in node.names:
                    if alias.name in {"Any", "cast"}:
                        errors.append(
                            f"{path.relative_to(ROOT)}:{node.lineno}: "
                            f"typing.{alias.name} is forbidden in the authoritative influence path"
                        )
            if isinstance(node, ast.Name) and node.id == "Any":
                errors.append(
                    f"{path.relative_to(ROOT)}:{node.lineno}: Any is forbidden "
                    "in the authoritative influence path"
                )
            if isinstance(node, ast.Call) and _name(node.func) == "cast":
                errors.append(
                    f"{path.relative_to(ROOT)}:{node.lineno}: unchecked cast is forbidden"
                )

    renderer_path = ROOT / "src/medical_ai/renderer.py"
    renderer_tree = ast.parse(renderer_path.read_text(encoding="utf-8"))
    render_function = next(
        (
            node
            for node in renderer_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "render_answer"
        ),
        None,
    )
    if render_function is None:
        errors.append("renderer.py: render_answer is missing")
    else:
        if not render_function.args.args:
            errors.append("renderer.py: render_answer must accept authorized views")
        else:
            annotation = _annotation_text(render_function.args.args[0].annotation)
            if "AuthorizedClaimView" not in annotation:
                errors.append(
                    "renderer.py: render_answer first parameter must be AuthorizedClaimView-based"
                )

    for path in RUNTIME_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(ROOT).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = _name(node.func)
            if called == "render_answer" and relative != "src/medical_ai/engine.py":
                errors.append(
                    f"{relative}:{node.lineno}: alternate runtime render_answer call path"
                )
            if (
                called in CAPABILITY_CONSTRUCTORS
                and relative != "src/medical_ai/influence.py"
            ):
                errors.append(
                    f"{relative}:{node.lineno}: {called} capability construction "
                    "is restricted to influence.py"
                )

    schemas_tree = ast.parse(
        (ROOT / "src/medical_ai/schemas.py").read_text(encoding="utf-8")
    )
    influence_subject = next(
        (
            node
            for node in schemas_tree.body
            if isinstance(node, ast.ClassDef) and node.name == "InfluenceSubject"
        ),
        None,
    )
    if influence_subject is None:
        errors.append("schemas.py: InfluenceSubject is missing")
    else:
        annotations = {
            node.target.id: _annotation_text(node.annotation)
            for node in influence_subject.body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        }
        if annotations.get("evidence_authority") != "EvidenceAuthorityState":
            errors.append(
                "schemas.py: evidence_authority must use EvidenceAuthorityState"
            )
        if (
            annotations.get("information_handling_authority")
            != "InformationHandlingAuthorityState"
        ):
            errors.append(
                "schemas.py: information_handling_authority must use "
                "InformationHandlingAuthorityState"
            )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        "Influence boundary static guard passed: "
        f"{len(AUTHORITATIVE_FILES)} authoritative files checked; "
        "renderer and capability construction paths are singular."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
