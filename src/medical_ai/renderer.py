from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import quote, urlsplit, urlunsplit

from .schemas import AuthorizedClaimView, InfluenceAuthorizationState, SourceRecord


def _escape_markdown_text(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    for ch in (chr(96), "*", "_", "{", "}", "[", "]", "(", ")", "#", "+", "!", ">", "<", "|"):
        escaped = escaped.replace(ch, f"\\{ch}")
    return escaped


def _safe_markdown_url(value: str) -> str:
    def _encode_link_component(component: str, *, safe: str) -> str:
        return quote(component, safe=safe).replace("(", "%28").replace(")", "%29")

    parts = urlsplit(value)
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        return "#"
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            _encode_link_component(parts.path, safe="/:@%+-._~"),
            _encode_link_component(parts.query, safe="=&%+-._~"),
            _encode_link_component(parts.fragment, safe="%+-._~"),
        )
    )


def _runtime_authorized_view(value: object) -> AuthorizedClaimView:
    if not isinstance(value, AuthorizedClaimView):
        raise TypeError("Renderer requires AuthorizedClaimView inputs")
    if value.authorization.state != InfluenceAuthorizationState.ACTIVE:
        raise ValueError("Renderer received a revoked influence authorization")
    return value


def render_answer(
    views: Sequence[AuthorizedClaimView],
    sources: Sequence[SourceRecord],
    *,
    trial_discovery: bool = False,
) -> str:
    """Render only authorization-carrying claim views.

    Raw ClaimRecord objects are not accepted. Runtime checks are retained even
    with static typing so untyped callers fail closed rather than bypassing the
    authorization capability.
    """

    checked_views = [_runtime_authorized_view(view) for view in views]

    source_map = {source.source_id: source for source in sources}
    lines = ["### Evidence-bound answer", ""]
    if not checked_views:
        return (
            "### Evidence-bound answer\n\n"
            "The available evidence did not pass the required verification "
            "and influence-authorization gates for a supported answer."
        )

    for view in checked_views:
        claim = view.claim
        refs: list[str] = []
        for source_id in claim.source_ids:
            source = source_map.get(source_id)
            if source is None:
                continue
            if "PMID" in source.identifiers:
                label = "PMID " + source.identifiers["PMID"]
            elif "NCT" in source.identifiers:
                label = source.identifiers["NCT"]
            else:
                label = source.record_id
            refs.append(
                f"[{_escape_markdown_text(label)}]"
                f"({_safe_markdown_url(source.stable_url)})"
            )
        citation = " " + " ".join(refs) if refs else ""
        lines.append(f"- {_escape_markdown_text(claim.claim_text)}{citation}")

    lines.extend(["", "### Sources"])
    for source in sources:
        identifiers = ", ".join(
            f"{_escape_markdown_text(key)}: {_escape_markdown_text(value)}"
            for key, value in source.identifiers.items()
        )
        lines.append(
            f"- [{_escape_markdown_text(source.title)}]"
            f"({_safe_markdown_url(source.stable_url)}) — {identifiers}"
        )

    if trial_discovery:
        lines.extend(
            [
                "",
                "*Alpha2 trial-discovery limitation: ClinicalTrials.gov records "
                "support discovery and registered-study facts. They are not treated "
                "as proof that an intervention is effective or safe.*",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "*Alpha2 literature limitation: claims are extractive sentences from "
                "admitted PubMed abstract passages; study quality, GRADE certainty "
                "and clinical recommendations are not yet synthesized.*",
            ]
        )
    return "\n".join(lines)
