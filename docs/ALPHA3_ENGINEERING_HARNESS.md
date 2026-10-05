# Alpha3 engineering harness scope and coverage

PR #15 is a bounded engineering-harness increment, referencing Issue #4.
It does not complete Alpha3 or authorize medical synthesis or release.
All cases retain `ENGINEERING FIXTURE — NOT CLINICALLY REVIEWED`.

## Execution and pass policy

`execution_case_ids` requires all six baseline cases to execute.
`required_pass_case_ids` fixes cases 001–004 as REQUIRED. Cases 005–006 remain
BLOCKED because conflict/population terminal behavior is unresolved.
The runner independently anchors these sets so editing a case tier or deleting
both a case and its policy entry cannot hide failure. CLI requirements are additive.
Versioned policy changes require deliberate code/fixture review under the canonical
Alpha3 change-control contract. Zero required cases cannot produce success.

Exit 0 means four required engineering cases passed with two capability gaps
still blocked. It does not mean six cases passed. Invalid case sets, missing
execution requirements and required expectation failures exit 1.

## Metric boundary

The fixture connector returns synthetic sources/passages in declared order,
without real source search, ranking or applying its `limit` argument.
`trace.source_ids` reflects that order after pipeline admission. Recall@k and
first-authoritative rank use this admitted trace list, not live retrieval results.
Normalization is called and recorded by the synthetic connector; this does not
exercise real PubMed/ClinicalTrials connector normalization or availability.
No claim of measured live recall or clinical citation entailment follows.

## Issue #4 acceptance coverage

| Criterion | This increment | Remaining gap |
| --- | --- | --- |
| Reviewed gold set | Six typed synthetic engineering cases | Clinician/researcher review and gold-set approval |
| Current retrieval recall@k | Fixture trace membership calculation | Real retrieval benchmark and target evaluation |
| First rank / normalization | Synthetic admitted ordering / fixture normalization | Live ranking and real connector behavior |
| Claim-specific authority / rejection | Query-plan source class and provenance rejection | Broader authority/admissibility negative coverage |
| Contamination / false support | No population-level measure | Negative source contamination benchmark |
| Extraction / entailment | Identifier, provenance, citation membership, influence checks | Semantic entailment and qualification review |
| Retraction / supersession / freshness | Metadata contract only | Dedicated negative cases |
| Jurisdiction / population | AU request metadata; population case BLOCKED | Jurisdiction mismatch and population enforcement |
| Conflict | Executed case 005, BLOCKED | Conflict representation and terminal state |
| Explicit failure taxonomy | Provenance, unavailable and high consequence tested | Remaining taxonomy states and negative coverage |
| High consequence fail-closed | Required case 004 | Broader gate bypass tests and independent verification |
| Unsupported escape | Bounded state/assertion checks | Validated-path escape measurement |
| Live PubMed / ClinicalTrials | Not executed, unproven | Revision-bound live tests |
| Revision-bound report | CI CLI JSON includes commit, versions and configuration | Review final-head run and artifact for each change |
| Visible failures / blockers | Separate counts and named gaps | Preserve separation in broader benchmark |

## Reproduction and CI evidence

Install with `python -m pip install -e '.[dev]'` in Python 3.12, then run:

```bash
python -m pytest tests/test_alpha3_evidence_fidelity_eval.py tests/test_retrieval_eval.py -q
python -m medical_ai.evals.alpha3_evidence_fidelity --json-out /tmp/alpha3-evidence-fidelity.json
python -m pytest
python scripts/verify_source_checksums.py
python scripts/check_repo_hygiene.py
python -m compileall -q src
python scripts/verify_package_policies.py
```

The existing exact-head `source-and-tests` job runs pytest and the real CLI,
and uploads JSON as `alpha3-evidence-fidelity-<head SHA>`, including on a
required-expectation failure. Malformed policy fails before report creation;
the missing artifact also remains a CI error, not a pass.
CI verifies the committed manifest without regenerating it. Manifest changes
in this increment cover only intentionally edited source, fixture and test files.
Editable policy parity does not establish build-isolated wheel packaging.
