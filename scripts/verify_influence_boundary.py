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
OUTPUT_CONSTRUCTORS = {"EvidenceAnswer"}


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
            errors.append(f"{(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)}: type-ignore escape hatch is forbidden")
        tree = ast.parse(text, filename=str(path))
        typing_aliases = {"typing", "typing_extensions"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in {"typing", "typing_extensions"}:
                        typing_aliases.add(alias.asname or alias.name)
            if isinstance(node, ast.ImportFrom) and node.module in {"typing", "typing_extensions"}:
                for alias in node.names:
                    if alias.name in {"Any", "cast"}:
                        errors.append(
                            f"{(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)}:{node.lineno}: "
                            f"typing.{alias.name} is forbidden in the authoritative influence path"
                        )
            if isinstance(node, ast.Name) and node.id == "Any":
                errors.append(
                    f"{(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)}:{node.lineno}: Any is forbidden "
                    "in the authoritative influence path"
                )
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id in typing_aliases
                and node.attr in {"Any", "cast"}
            ):
                errors.append(
                    f"{(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)}:{node.lineno}: qualified typing.{node.attr} is forbidden"
                )
            if isinstance(node, ast.Call) and _name(node.func) == "cast":
                errors.append(
                    f"{(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)}:{node.lineno}: unchecked cast is forbidden"
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
        relative = (path.relative_to(ROOT) if path.is_relative_to(ROOT) else path).as_posix() if path.is_relative_to(ROOT) else str(path)
        capability_aliases = set(CAPABILITY_CONSTRUCTORS)
        output_aliases = set(OUTPUT_CONSTRUCTORS)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name in CAPABILITY_CONSTRUCTORS:
                        capability_aliases.add(alias.asname or alias.name)
                    if alias.name in OUTPUT_CONSTRUCTORS:
                        output_aliases.add(alias.asname or alias.name)
        for _ in range(3):
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and isinstance(node.value, (ast.Name, ast.Attribute)):
                    assigned = _name(node.value)
                    for target in node.targets:
                        if not isinstance(target, ast.Name):
                            continue
                        if assigned in capability_aliases:
                            capability_aliases.add(target.id)
                        if assigned in output_aliases:
                            output_aliases.add(target.id)
        pydantic_constructors = {"model_construct", "model_validate", "model_validate_json"}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = _name(node.func)
            if called == "render_answer" and relative != "src/medical_ai/engine.py":
                errors.append(
                    f"{relative}:{node.lineno}: alternate runtime render_answer call path"
                )
            capability_type = called in capability_aliases or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in pydantic_constructors
                and _name(node.func.value) in capability_aliases
            )
            output_type = called in output_aliases or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in pydantic_constructors
                and _name(node.func.value) in output_aliases
            )
            if capability_type and relative != "src/medical_ai/influence.py":
                errors.append(
                    f"{relative}:{node.lineno}: {called} capability construction "
                    "is restricted to influence.py"
                )
            if output_type and relative != "src/medical_ai/engine.py":
                errors.append(
                    f"{relative}:{node.lineno}: {called} user-facing output construction "
                    "is restricted to engine.py"
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
        "renderer, output, and capability construction paths are singular."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
