# RET-EXP-001 — lexical baseline preparation, 13 November 2026

Engineering evaluation only. Public, pilot, commercial and clinical release:
**NO-GO**. Independent audit and owner review pending.

## 1. Defect / preconditions

The existing retrieval gold file supplies two pre-ranked lists; it does not
execute retrieval. The owner requested a frozen experiment contract and an
executable lexical baseline. Main was retrieved and pinned at
`f292523c3fd94983b2df48812739dbeba6ac0d06`; original AMBOSS handoff was read at
`4efac408f5b5a8213242b4ebfc0d28685665fbf5`.

Existing canonical instructions, intended use, workflow, build plan, source policy,
schemas, provenance validator and extractor were inspected before changes.
Ecosystem status returned `Tool ecosystem_storage_status not found`; no Ecosystem
save or retrieval is claimed. No storage reconfiguration occurred.

## 2. What was implemented

- [Frozen contract](../../plans/RET-EXP-001-v0.1.md), 30 synthetic cases / 68 corpus
  passages, 15 development + 15 held-out-engineering cases.
- Byte pins for contract, cases and unchanged baseline code/policy dependencies.
- Offline CLI calling the existing source qualifier and lexical extractor, with
  complete-passage identity/content checks and traceable selected evidence IDs.
- Separate candidate-pool, post-qualification and selected recall; empty gold
  remains null. Quality limitations remain visible, not recast as a PASS.
- 37 regression/integrity tests and strict Pyright coverage for the new runner.

No application runtime module, connector, authority kernel, policy, renderer,
existing retrieval fixture or A4 assurance workstream changed. The supplied
source-class plan bypasses query planning; the runner is not a second authority
resolver or a substitute for the engine.

## 3. Behaviour exercised

Two baseline runs yielded identical case results and summaries:

`0c29caa1ddf6621ab566f1a9856dc3f6b216407739e6deef55b36045b6ed7844`

| Observation | Result | Scope |
|---|---:|---|
| Executed cases | 30 | 28 nonempty relevant sets; 2 empty |
| Mean candidate-pool recall | 26/28 = 92.86% | Synthetic supplied pools |
| Mean post-qualification recall | 26/28 = 92.86% | Existing source qualification |
| Mean selected-passage recall@5 | 20/28 = 71.43% | Actual extractor selection |
| Mean precision@5 | 14.67% | Fixed denominator 5, including short/empty outputs |
| Cases with labelled excluded selections | 8 | Pre-authority stage only |
| Empty-gold cases with nonempty selection | 2 | Not correct abstention |

Both splits share templates and yield the same aggregates; this is not independent
validation or an estimate of population performance. Relevant paraphrases and
abbreviations are missed, keyword distractors outrank a relevant passage, and
missing candidates cannot be recovered. Source-class/superseded/narrative and
one known injection exclusion behave as asserted. Retraction/jurisdiction/
population and irrelevant lexical matches expose stage limitations. These do not
prove that the full runtime rendered excluded evidence: downstream authority,
verification, hazard and rendering gates are not exercised by this runner.

## 4. Local check results

All statements are local **executed/passed** results, not independent verification.

| Check | Observed result |
|---|---|
| Untouched baseline pytest | 469 passed, 1 dependency deprecation warning |
| Initial new-test RED run | Collection failed: runner did not yet exist |
| New regression checks | 37 passed within full suite |
| Full pytest after addition | 506 passed, same dependency warning |
| Strict Pyright / influence guard | 0 errors; guard passed for 8 authoritative files |
| Source checksum verification | 131 checksums passed; verifier did not regenerate manifest |
| Tracked-file hygiene | Passed |
| Compile/import and policy parity | Passed |
| Alpha3 harness | 4 required passed; 2 BLOCKED and 3 UNPROVEN preserved |
| Repeated RET-EXP-001 runs | Identical results/summaries digest |
| Diff review | No runtime/kernel/policy changes; no whitespace errors |

Initial strict typing caught a set/frozenset comparison diagnostic in the runner;
the comparison was corrected and the gate rerun successfully. No test or typing
rule was weakened. The initial RED run is interface evidence, not reproduction
of a pre-existing runtime safety defect.

The accompanying machine reports record the actual tested code revision, file
hashes and environment. Evidence attachment is a separate commit; it does not
alter the measured implementation. Final PR-head CI must be read from GitHub.

## 5. Not done / still gated

No semantic model/RerankerPort, live-source search, clinical gold set, independent
Kilo Claw audit, runtime integration, invitations, merge, deployment or release.
No clinical 98% recall claim. No change to existing Alpha3 blocked/unproven cases.
The selected plugin's reconciliation contract was applied manually to retrieved
sources; no deterministic memory-resolver script was run and no memory was changed.

Next bounded decision: review this contract/benchmark, then authorise and pin one
offline candidate comparison, with the exact insertion point defined so lexical
extraction cannot silently overwrite candidate ordering. Runtime influence and
release still require their separate evidence and owner gates.
