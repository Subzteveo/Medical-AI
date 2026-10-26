> **27 October 2026 interaction correction:** The PMID 37249199 research-variable false positive is corrected by a bounded deterministic grammar, with live broad-query results verified against original XML. Unrecognised variable expressions and ambiguous references still withhold conservatively; separate generic-term false positives remain. This is not general medicine recognition or clinical validation. See `project_docs/evidence/research-interactions-20261027/README.md`. The earlier observation below is historical.

> **27 October 2026 PubMed context correction:** PubMed abstracts are now extracted whole and attributed to their publications, rather than reduced to keyword-matching sentences. This preserves abstract-level context, not full-paper context or clinical truth. Results can be long. The existing conservative consequence classifier may withhold an entire answer when an abstract mentions a flagged term, including non-drug uses of “interactions”. Population applicability, conflicting evidence and semantic clinical verification remain unproven. Revision-bound execution evidence is in `project_docs/evidence/pubmed-discovery-20261027/README.md`; older environment observations below are historical.

# Known Limitations — alpha2.1 remediation candidate

1. Extractive only: no generative medical synthesis.
2. PubMed literature plus ClinicalTrials.gov trial discovery only; no guideline, regulator, drug-interaction or terminology authority path yet.
3. Abstract evidence is not equivalent to full-text critical appraisal.
4. ClinicalTrials.gov registry information supports trial discovery and registered-study facts only; narrative sponsor/investigator descriptions are not admitted as efficacy/safety claims.
5. No GRADE/certainty assessment.
6. Literature relevance after retrieval still uses simple lexical overlap rather than a validated production reranker.
7. High-consequence queries and high-consequence extracted claims fail closed, but the authoritative-source + independent clinical verifier path is still absent.
8. Patient/identifier detection is heuristic. Five reproduced bypass examples are now covered, but this does not establish complete PHI detection or de-identification. Users must not enter identifying information.
9. No production PHI posture is claimed.
10. Query digests are keyed HMACs, but trace storage remains a local engineering mechanism, not an audited production logging system.
11. A recall@k metric harness exists, but a clinically reviewed retrieval gold set and ≥98% authoritative-source recall target are not established.
12. Live PubMed/ClinicalTrials execution for this remediation candidate is blocked in the current build environment by outbound DNS/network restrictions and must be rerun elsewhere against the exact artifact.
13. Static browser semantics and DOM-safe rendering do not establish accessibility conformance or assistive-technology success.
14. No authentication/multi-user tenancy exists.
15. Dependency versions are pinned for the candidate, but a standard build-isolated wheel build is blocked in this environment because build isolation cannot resolve the package index; no-build-isolation succeeds with the provisioned toolchain.
16. No final TGA classification/exemption determination has been made. Public/commercial distribution remains deferred.
17. Not for public clinical deployment.
