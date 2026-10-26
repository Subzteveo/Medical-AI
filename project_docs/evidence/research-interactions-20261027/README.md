# Research-variable interaction correction — 27 October 2026

Baseline main: `a55b0eb0b2fa9d1b04c9737196c1468d2877569c` (PR #33 merged). No open PRs returned at intake. Application/test revision: `8efd7b047804b85bf61015056b906f4e08c7073c`. Later evidence/documentation commits do not change that application code. No deployment or intended-use change.

## Reproduced failure and cause

Original EFetch XML for PMID 37249199 was retrieved, then replayed through the unchanged baseline with “Find literature about mindfulness and attention”. `baseline-trace.json` records MODERATE query classification, an extracted complete abstract classified HIGH solely for `drug_interaction`, exact-extractive support but failed verification, and zero visible claims. The phrase “interactions of these variables” refers to the immediately preceding enumeration of stress, protective factors and psychological well-being. No other consequence category matched that abstract.

Path: `planner.classify_consequence` → `claims.build_claims` → `verifier.verify_claims(high_consequence_supported=False)` → engine whole-answer withholding → renderer. The original generic interaction regex made no distinction between research variables and medicines. The original PR #33 browser record corroborates this withholding, but this session separately reproduced it from original XML. The baseline trace stores verification outcomes, not claim-level category reasons; the accompanying diagnostic explicitly records those reasons rather than claiming the trace already contained them.

## Focused correction

Only consequence classification changes. Each interaction mention must independently resolve to a bounded, explicit list of non-pharmacological variables or a two-factor statistical expression. “Of these variables” additionally requires a complete recognised enumeration in the immediately preceding sentence and no intervening subject in the reference sentence. Grouped protective factors are flattened only if every group member is recognised. Explicit pharmacological context prevents an exemption. Unknown operands, unrecognised grammar, verbal interactions, unclear antecedents, medicines with unfamiliar names and mixed meanings retain HIGH. Negation does not establish safety.

This is an intentionally incomplete deterministic grammar with a small non-drug vocabulary, not general semantic understanding or medicine recognition. It uses no PMID/query whitelist, medicine-name dependency, sentence stripping, source mutation, schema change or new package. Other high-consequence categories run independently. Full abstract extraction, original headings, publication attribution, verification and whole-answer withholding remain unchanged. The existing trace's planner component version identifies the revised classifier.

## Tests and execution

- Before implementation: 14 failures and 41 passes in the initial 55-test set (`regression-before.txt`). The failing cases establish the research-variable false positive; risk controls already passed.
- Final focused set: 74 passes, including 69 interaction tests and the five PR #33 context tests. Two further adversarial cases require withholding for an intervening subject and a semicolon-shared operand list.
- Full regression: 292 passed, one dependency deprecation warning. Strict influence typing/static guard, source checksums, tracked-file hygiene, compile/import and installed-policy parity passed.
- Alpha3: four required fixture cases passed. Existing conflict/population checks remain blocked and clinical entailment/live ranking unproven; see `alpha3.json`.
- DOM: 43 invalid responses withheld, valid positive control and 15 unsafe-link controls passed. Real Chromium synthetic desktop/mobile/keyboard/provenance checks passed.
- Browser tooling initially lacked a browser; the bundled newer browser download failed. Installing the repository CI's pinned Playwright 1.56.1 browser tooling resolved this. An initial separate-process server attempt was unreachable; co-locating the local server and browser in one execution established connectivity. These are environment failures, not passing application checks.

`tests/test_interaction_context.py` is the case-by-case expectation register: every row states its reason and is exercised as a query and as a complete extracted abstract. Positive rows require exact preserved text/headings/attribution. Risk rows require withheld claims, sources and passages, with failed verification; a separate test proves a high-consequence query cannot be downgraded by a benign abstract.

## Review-driven correction

Automatic review of publication commit `47107f5` found a P1: the two-factor regex could match the benign suffix inside `tacrolimus-by-age-by-sex interaction`. This was a real regression, not a disputed finding. Five new cases cover known/unknown prefixes, whitespace and multiplication-symbol prefixes, and an unknown suffix, at both query and full-abstract boundaries. Eight tests failed before the correction (`review-regression-before.txt`; trailing whitespace only normalised). The statistical pair now requires a sentence boundary and a bounded neutral lead-in, so it cannot hide a preceding factor. All ten cases pass after the repair. Unknown expression forms remain conservative.

The full regression and all five authenticated live-browser scenarios were repeated on corrected application revision `8efd7b0`; the current live-verification/browser-results/type-safety/Alpha3 records bind that revision. `original-replay.json` is an earlier exploratory working-copy replay; use the final revision-bound live records for acceptance. Historical initial failures remain preserved.

## Authenticated browser → live PubMed

Real Chromium → ephemeral local invite/session authentication → local FastAPI → live PubMed ESearch/EFetch → unchanged parser/extractor → verifier/influence controller → displayed answer. No live-source mocks or response substitutions. Captures remain local; only identifiers, digests and execution summaries are committed.

1. **Original broad query:** now `ANSWER_SUPPORTED_WITH_QUALIFICATIONS`, with three whole abstracts: PMIDs 33223537, 26168376 and 37249199. Each candidate has no matched high-consequence category. The previously failing PMID retains its complete context.
2. **Targeted title query:** two complete abstracts, PMIDs 37249199 and 36767238. The latter retains BACKGROUND, PURPOSE, METHODS, RESULTS and CONCLUSION headings.
3. **Additional trial-focused query:** still `HIGH_CONSEQUENCE_VERIFICATION_FAILED`, no visible claims. It includes a genuinely restricted paediatric population (30345511), unresolved time/group interaction wording (32432795), and a separate existing `diagnostic_exclusion` false positive on excluding opinion articles (25099314). Neither remaining classifier issue was weakened or repaired in this PR. The paediatric restriction independently requires withholding.
4. **TGA approval question:** `NO_AUTHORITATIVE_SOURCE`, zero connector calls.
5. **Patient-specific dosing:** `OUTSIDE_VALIDATED_CAPABILITY`, zero connector calls.

All five cases checked HTTP 200, no-store caching and rendered state; browser page errors were empty. Browser assertions compare displayed complete text, attribution and citation URLs to the response. The standalone original-field checker then compares claims, evidence and passages with original XML and checks identity/citation mappings. Additional checks compare original titles and section headings. Altered-claim negative controls were rejected. `live-verification.json` records exact XML digests, request URLs/times, actual traces, and diagnostic replay matching the live verification IDs/results. This checker was written by the implementer and is not independent clinical review.

To reproduce: install the existing project dev dependencies and CI browser tooling; set `MEDICAL_AI_INTERACTION_CAPTURE_DIR` to a private scratch directory; run `local-server.py` and `live-browser.cjs` in the same local network environment. Then run `PYTHONPATH=src python project_docs/evidence/research-interactions-20261027/verify-captures.py CAPTURE_DIR REPORT.json` from the repository root. Keep raw publisher abstracts, screenshots, traces database and ephemeral authentication material out of Git. Current retrieval may differ; the saved digests bind this observed run.

## Remaining limits and integration

Clinical correctness, study quality, applicability, recall, ranking and general semantic classification remain unproven. Recognised vocabulary and grammar are deliberately narrow; time/group and other unresolved research meanings may still produce conservative false positives. Separate generic-term false positives, including diagnostic exclusion, remain. Unknown names are held because operands are unresolved, not because this change proves they are medicines. Qualified external clinical review was not obtained; it is required before claims beyond this engineering evidence.

Shell push lacked GitHub credentials; publication uses the authenticated GitHub connector, with full tree equality checked against the local commit. Final-head CI and merge state are recorded on the PR. No production deployment, settings changes, governance additions or clinical expansion were performed.
