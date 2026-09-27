from __future__ import annotations
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from .schemas import ClaimRecord, SourceRecord, VerificationStatus


def _escape_markdown_text(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    for ch in ("`", "*", "_", "{", "}", "[", "]", "(", ")", "#", "+", "-", ".", "!", ">", "<", "|"):
        escaped = escaped.replace(ch, f"\\{ch}")
    return escaped


def _safe_markdown_url(value: str) -> str:
    def _encode_link_component(component: str, *, safe: str) -> str:
        return quote(unquote(component), safe=safe).replace("(", "%28").replace(")", "%29")

    parts = urlsplit(value)
    if parts.scheme.lower() not in {"http", "https"}:
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


def render_answer(claims: list[ClaimRecord], sources: list[SourceRecord], *, trial_discovery: bool = False) -> str:
    source_map = {s.source_id: s for s in sources}
    lines = ["### Evidence-bound answer", ""]
    passed = [c for c in claims if c.verification_status == VerificationStatus.PASS]
    if not passed:
        return "### Evidence-bound answer\n\nThe available evidence did not pass the required verification gates for a supported answer."
    for claim in passed:
        refs = []
        for sid in claim.source_ids:
            src = source_map.get(sid)
            if src:
                if "PMID" in src.identifiers:
                    label = f"PMID {src.identifiers['PMID']}"
                elif "NCT" in src.identifiers:
                    label = src.identifiers["NCT"]
                else:
                    label = src.record_id
                refs.append(f"[{_escape_markdown_text(label)}]({_safe_markdown_url(src.stable_url)})")
        citation = " " + " ".join(refs) if refs else ""
        lines.append(f"- {_escape_markdown_text(claim.claim_text)}{citation}")
    lines.extend(["", "### Sources"])
    for src in sources:
        ids = ", ".join(f"{_escape_markdown_text(k)}: {_escape_markdown_text(v)}" for k, v in src.identifiers.items())
        lines.append(f"- [{_escape_markdown_text(src.title)}]({_safe_markdown_url(src.stable_url)}) — {ids}")
    if trial_discovery:
        lines.extend(["", "*Alpha2 trial-discovery limitation: ClinicalTrials.gov records support discovery and registered-study facts. They are not treated as proof that an intervention is effective or safe.*"])
    else:
        lines.extend(["", "*Alpha2 literature limitation: claims are extractive sentences from admitted PubMed abstract passages; study quality, GRADE certainty and clinical recommendations are not yet synthesized.*"])
    return "\n".join(lines)
