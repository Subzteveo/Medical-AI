# PubMed discovery execution — 27 October 2026

Baseline: `de96e7fba8b0a1847a75943bd56d00591bffcb73`, PR #32 merged; no open PRs at intake. Code correction: `c9ff9b3` (full revision in the accompanying validation record). No deployment or clinical-scope expansion.

## Reproduced defect

Live PubMed retrieval for “Find literature about mindfulness and attention” returned PMIDs 33223537, 26168376 and 37249199. Before repair, lexical sentence ranking exposed a mediation statement from 37249199 without its cross-sectional study design or sampled population. Other sentences from that abstract did not repair the omitted context. Exact substring verification passed this incomplete proposition.

Three synthetic regression cases failed against the unchanged baseline: qualifications within an abstract, context across structured sections, and high-consequence text discarded before verification. One no-overlap control already passed. `regression-before.txt` records that run. A fifth case now retains the old shared fixture's pediatric exclusion and verifies conservative withholding. The generic positive fixture uses “other populations” instead so unrelated provenance tests continue to exercise their supported paths. Injection-contaminated abstracts now abstain rather than salvage sentences; Markdown escaping assertions remain enforced with the added attribution prefix.

## Correction

Preserve all nonempty AbstractText fields in order, including original Label/NlmCategory headings, joined with two newlines as one `Article/Abstract` passage. Extract that complete passage. The browser and Markdown identify the result as the publication's PubMed abstract. The existing consequence, source, provenance and influence controls remain in place. No dependency or architecture change.

## Executed live browser cases

Real Chromium → ephemeral authenticated local FastAPI → live ESearch/EFetch → original XML → parser → extraction → verifier → influence controller → displayed text and citation. Responses were captured without changing them; no source mocks or clinical reviewer were used.

- Targeted title search: “How does mindfulness meditation work proposing mechanisms of action from a conceptual and neural perspective”. One complete abstract (PMID 26168376), 1,591 characters, matched its original XML and citation. This is targeted discovery, not a recall/ranking benchmark.
- Broad search: “Find literature about mindfulness and attention”. HIGH_CONSEQUENCE_VERIFICATION_FAILED with no displayed claims. Preserving the full third abstract exposes “interactions” between research variables to the existing drug-interaction heuristic. This is an observed conservative false positive, not evidence of an actual drug interaction. The classifier was not weakened in this repair.
- Unsupported TGA approval question: NO_AUTHORITATIVE_SOURCE; no claims or connector calls.
- Patient-specific dosing question: OUTSIDE_VALIDATED_CAPABILITY; no claims or connector calls.

All browser cases checked HTTP 200, Cache-Control: no-store and expected rendered state. The supported case checked DOM text, attribution and source URLs; browser page errors were empty.

`original-field-check.json` records original-XML and complete-abstract digests. The standalone checker imports none of the runtime parser, extractor, verifier or authority code. A deliberately substituted claim was rejected. The checker was written during this development session and is not independent clinical review.

Publisher abstracts, screenshots containing full abstracts, raw request-time captures and ephemeral credentials are not redistributed in this evidence directory. Original records: https://pubmed.ncbi.nlm.nih.gov/26168376/ , https://pubmed.ncbi.nlm.nih.gov/33223537/ , https://pubmed.ncbi.nlm.nih.gov/37249199/ . Re-fetching can produce changed XML; the retained digests identify the inspected snapshot, not a guarantee that a future response will match.

## Limits and next useful work

This demonstrates bounded original-text fidelity and abstention, not clinical correctness, treatment efficacy, study quality, full-paper context, applicability, conflict resolution, search completeness or production readiness. Full abstracts can be long. The remaining classifier false positive is a concrete next bounded usability/safety investigation; reproduce it and preserve genuine drug-interaction controls before any change. Qualified external review is required for medical-correctness claims engineering checks cannot establish.

Final-head CI and integration state belong to the PR. The earlier STATUS checkpoint predates PR #32's merge; that merge is confirmed at the baseline above.
