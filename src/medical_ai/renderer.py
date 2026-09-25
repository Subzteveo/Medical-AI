from __future__ import annotations
from .schemas import ClaimRecord, SourceRecord, VerificationStatus


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
                refs.append(f"[{label}]({src.stable_url})")
        citation = " " + " ".join(refs) if refs else ""
        lines.append(f"- {claim.claim_text}{citation}")
    lines.extend(["", "### Sources"])
    for src in sources:
        ids = ", ".join(f"{k}: {v}" for k, v in src.identifiers.items())
        lines.append(f"- [{src.title}]({src.stable_url}) — {ids}")
    if trial_discovery:
        lines.extend(["", "*Alpha2 trial-discovery limitation: ClinicalTrials.gov records support discovery and registered-study facts. They are not treated as proof that an intervention is effective or safe.*"])
    else:
        lines.extend(["", "*Alpha2 literature limitation: claims are extractive sentences from admitted PubMed abstract passages; study quality, GRADE certainty and clinical recommendations are not yet synthesized.*"])
    return "\n".join(lines)
