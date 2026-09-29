# Validation and Evidence — alpha2 remediation candidate

## Evidence vocabulary

`proposed → generated → inspected → executed → passed → verified`, with `blocked` and `unproven` retained when stronger claims are not justified.

A passed unit/integration test supports only its assertions and environment. It does not establish public clinical safety, regulatory compliance, production security, accessibility conformance, live source availability or deployment success.

## External ultrareview correction — 25 September 2026

An independent container reproduction against the exact canonical alpha2 ZIP (`b2f46775…19bf9`) invalidated several original alpha2 acceptance claims. In particular:

- original **REQ-006 / AC-006 was not supported** by the single singular-`dose` test; multiple policy-defined high-consequence phrasings remained MODERATE and claim-level dose content could reach PASS;
- original **REQ-004 privacy evidence was insufficient**; realistic patient/identifying inputs bypassed the heuristic detector;
- retracted PubMed records and ClinicalTrials.gov narrative efficacy statements could reach the claim path;
- plain-English retrieval and several status/routing semantics were defective;
- the original checksum script regenerated its manifest rather than verifying it.

Those findings are retained as adverse evidence. They are not overwritten by later green tests.

## REQ → AC → VAL trace

| Requirement | Acceptance | Current remediation evidence |
|---|---|---|
| REQ-001 | AC-001 evidence-bound claims | Automated extract→claim→verify→trace tests pass; semantic/source-class limitations remain explicit |
| REQ-002 | AC-002 browser evidence workflow | HTTP/TestClient shell checks pass; real browser/AT interaction remains unexecuted here |
| REQ-003 | AC-003 claim-specific source routing | Literature/trial/regulator routing regressions pass; live retrieval on remediation candidate remains separately evidenced |
| REQ-004 | AC-004 patient/identifier public-route block | Five reproduced identifying/patient inputs now pass the pre-connector block regression suite; detector remains heuristic and is not a de-identification guarantee |
| REQ-005 | AC-005 jurisdiction-aware regulator fail-closed | Regression checks pass for AU and US wording; no TGA/PBS adapter exists |
| REQ-006 | AC-006 high-consequence fail-closed | **Original alpha2 evidence contradicted.** Remediation tests now cover 18 policy phrasings plus claim-level high-consequence detection and pass in this container |
| REQ-007 | AC-007 provenance and traceability | Automated identifier/component-version checks pass |
| REQ-008 | AC-008 minimal durable audit trail | Raw question absent; query digest is keyed HMAC rather than guessable unsalted SHA-256 |
| REQ-009 | AC-009 safe dependency failure | Failing-connector regression passes; no model fallback |
| REQ-010 | AC-010 accessible interaction states | Static semantics present; real browser/keyboard/screen-reader verification remains unexecuted |
| REQ-011 | AC-011 retrieval evaluation path | Metric plumbing passes; clinically reviewed recall target remains unproven |

## Remediation regression evidence

Working-copy command:

```text
pytest --tb=no
```

Observed after critical and material remediation in the current container:

```text
63 passed
```

Before fixes, after adding the ultrareview-derived regression suite, the same working copy produced:

```text
34 failed, 29 passed
```

This red→green history is the evidence that the new tests were not written after the implementation merely to confirm existing behavior.

## Explicitly not established

- live PubMed retrieval from this remediation candidate in this execution environment;
- live ClinicalTrials.gov retrieval from this remediation candidate in this execution environment;
- ≥98% authoritative-source recall@k on a clinically reviewed gold set;
- ≥99% ordinary citation correctness at release-scale sample size;
- 100% observed high-consequence citation correctness;
- zero observed critical failures across a statistically meaningful medical safety suite;
- complete PHI/identifier detection or a PHI-approved deployment route;
- WCAG conformance or screen-reader compatibility;
- subgroup performance;
- public deployment, monitoring or rollback;
- TGA/PBS/SNOMED CT-AU/AMT integration;
- final TGA classification/exemption determination for a commercial/public product.
