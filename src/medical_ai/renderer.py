from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import quote, urlsplit, urlunsplit

from .schemas import AuthorizedClaimView, CitationMapping, EvidenceUnit, Passage, SourceRecord
from .influence import InfluenceController
from .provenance import safe_source_url, validate_output_provenance


def _escape_markdown_text(value: str) -> str:
    escaped = " ".join(value.splitlines()).replace("\\", "\\\\")
    for ch in (chr(96), "*", "_", "~", "{", "}", "[", "]", "(", ")", "#", "+", "!", ">", "<", "|"):
        escaped = escaped.replace(ch, f"\\{ch}")
    return escaped


def _safe_markdown_url(value: str) -> str:
    def _encode_link_component(component: str, *, safe: str) -> str:
        return quote(component, safe=safe).replace("(", "%28").replace(")", "%29")

    if safe_source_url(value) is None:
        raise ValueError("Source link is not permitted HTTPS")
    parts = urlsplit(value)
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            _encode_link_component(parts.path, safe="/:@%+-._~"),
            _encode_link_component(parts.query, safe="=&%+-._~"),
            _encode_link_component(parts.fragment, safe="%+-._~"),
        )
    )


def _runtime_authorized_view(
    value: object, controller: InfluenceController | None
) -> AuthorizedClaimView:
    if not isinstance(value, AuthorizedClaimView):
        raise TypeError("Renderer requires AuthorizedClaimView inputs")
    if controller is None:
        raise ValueError("Renderer requires the issuing influence controller")
    controller.validate_authorized_claim_view(value)
    return value

def render_answer(
    views: Sequence[AuthorizedClaimView],
    sources: Sequence[SourceRecord],
    *,
    trial_discovery: bool = False,
    influence_controller: InfluenceController | None = None,
    evidence_objects: Sequence[EvidenceUnit] = (),
    passages: Sequence[Passage] = (),
    citation_mappings: Sequence[CitationMapping] = (),
) -> str:
    """Render only authorization-carrying claim views.

    Raw ClaimRecord objects are not accepted. Runtime checks are retained even
    with static typing so untyped callers fail closed rather than bypassing the
    authorization capability.
    """

    checked_views = [_runtime_authorized_view(view, influence_controller) for view in views]
    validate_output_provenance(
        [view.claim for view in checked_views], sources, evidence_objects, passages, citation_mappings,
    )

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
            source = source_map[source_id]
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
                (
                    "*Alpha2 trial-discovery limitation: ClinicalTrials.gov records "
                    + "support discovery and registered-study facts. They are not treated "
                    + "as proof that an intervention is effective or safe.*"
                ),
            ]
        )
    else:
        lines.extend(
            [
                "",
                (
                    "*Alpha2 literature limitation: claims are extractive sentences from "
                    + "admitted PubMed abstract passages; study quality, GRADE certainty "
                    + "and clinical recommendations are not yet synthesized.*"
                ),
            ]
        )
    return "\n".join(lines)
