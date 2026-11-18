# RET-EXP-001 v0.1 — frozen lexical-baseline experiment contract

Status: proposed engineering experiment; baseline preparation only. Frozen means
the inputs and contract are byte-bound before measurement, not clinically reviewed
or owner-approved. Public, pilot, commercial and clinical release remain NO-GO.

## Authority and scope

Current owner request: prepare the frozen experiment contract and executable
lexical-baseline benchmark first. The continuation packet is not evidence or
implementation approval. This request permits this bounded offline evaluation;
it does not approve a semantic model, runtime integration, kernel changes, merge,
deployment, invitations, or release.

Baseline: `Subzteveo/Medical-AI` main
`f292523c3fd94983b2df48812739dbeba6ac0d06`, retrieved 13 November 2026.
Original handoff: `project_docs/AMBOSS_CLEAN_ROOM_HANDOFF_2026-11-13.md` at
`4efac408f5b5a8213242b4ebfc0d28685665fbf5` (documentation branch).
The handoff's AMBOSS disclosures were not independently reverified here.
Canonical boundaries: AGENTS.md, INTENDED_USE.md, STATUS.md, development workflow,
Medical Evidence Influence Policy and the 11 November full-app build plan.

**RET-EXP-001 is separate from Alpha3 A4 adversarial assurance.** It does not
advance the C-series build chunks or close their audit gates. Independent audit
(the recorded Kilo Claw process) and owner review remain pending.

## Question and smallest useful result

What does the existing lexical extractor actually select from a fixed synthetic
candidate pool, and which relevant passages are lost before versus during ranking?
This slice establishes a reproducible comparator. It does not test live search,
clinical authority, answer quality, medical truth, or a semantic reranker.

## Frozen inputs and evaluation boundary

- `evals/retrieval/ret-exp-001-v0.1/cases.json`: 30 authored synthetic cases,
  15 development and 15 held-out-engineering cases, disjoint passage/source IDs.
  All text is invented evaluation material, not patient data or AMBOSS content.
  Sources use `https://example.invalid/` and explicit synthetic attribution.
- No clinical adjudication. Held-out means reserved for later candidate tuning;
  the baseline author can see it, both splits share case categories/templates,
  and it is not an independent or blind validation set. Any tuning on held-out
  results requires a new held-out set and version; preserve these results.
- Every case has a question, fixed source-class/jurisdiction plan, corpus records,
  candidate passage IDs, relevant passage IDs, excluded passage IDs and rationale.
  Labels are authored expectations, never derived from baseline rankings. A
  relevant passage may exist in the corpus but be absent from the candidate pool.
- Categories: exact match, whole abstract, paraphrase, abbreviation, distractor
  cutoff, missing candidate, wrong source class, registry narrative, supersession,
  retraction, jurisdiction, conflict pair, population, injection and no evidence.
- Ranking unit: one complete literature abstract passage or one attributed
  registry-fact passage. No sentence splitting, chunk changes or copied scorer.
- k=5 is fixed. Candidate pools include more than five items in cutoff cases.
  Execute the unchanged `qualify_source` and `extract_evidence` functions. The
  supplied plan fixes upstream routing; no live connector, query planner, model,
  engine, claim builder, resolver, renderer or state store runs in this benchmark.
- Input validation requires unique IDs, closed references and safe synthetic
  URLs. No record receives a version/authority approval fabricated by the runner.
- The untruncated extraction records rank; a second call with `max_units=5`
  records selection and must equal its first five units. Preserve exact passage
  hashes, evidence IDs and source mapping. No generated medical prose is output.

`freeze.json` binds this contract, case bytes and the baseline implementation
dependencies. The runner refuses altered/missing pins, wrong case counts, wrong
splits, duplicate/unknown IDs and malformed records. A freeze is a reproducibility
check, not a signature or security boundary against an authorised editor changing
both manifest and files. Never refresh pins as part of running or verification.
Change any frozen input only under a new experiment version with a reason.
Runner and environment hashes/versions accompany each result; the measured tree
is identified by Git HEAD plus dirty state and exact execution-file hashes.

## Metrics and reporting

For each nonempty relevant-ID set E:

- candidate-pool recall = |E intersect candidate IDs| / |E|;
- post-qualification recall = |E intersect admitted passage IDs| / |E|;
- selected passage recall@5 = |E intersect selected IDs| / |E|;
- first relevant passage rank from actual untruncated extraction, or null;
- precision@5 = relevant selected count / 5 (fixed denominator).

For empty E, all recall and first-rank values are null, not 1. Report these cases
separately, including whether any passage was selected. All cases retain
`excluded_selected_ids`; this is a **pre-authority selection diagnostic**, not a
claim that the runtime displayed an unsafe answer. Compute macro means only over
non-null values, by split and category. Report missing relevant IDs at each stage.
Conflict cases require both opposing passages for retrieval recall, but do not
test conflict detection. Jurisdiction/retraction/population labels do not add new
filters: report existing behaviour even when it misses these expectations.

Report execution integrity separately from quality. A successful CLI exit means
the fixed experiment executed and its structural checks passed; low recall or
excluded selections must remain visible and cannot be renamed a quality PASS.
The semantic comparison and clinical authority recall target remain unproven.
Do not infer 98% authoritative-source recall from these synthetic results.

## Acceptance for this preparation slice

1. All 30 cases execute through the real baseline; no pre-ranked result inputs.
2. Two runs produce identical case results/summary and result digest. Time, Git
   dirty state and dependency observations are separately labelled metadata.
3. Tests reject missing cases, bad references, duplicate identities, altered pins
   and changed evidence content; test the CLI exit/error path and no network.
4. Independent assertions exercise paraphrase misses, missing candidate recall,
   cutoff at k, complete abstract preservation, registry narrative exclusion,
   empty gold handling and known pre-authority selection limitations.
5. Existing regressions, strict typing, influence guard, checksums, hygiene,
   package-policy parity and Alpha3 harness run with actual results recorded.
6. No application runtime or authority-policy change; audit/owner review pending.

## Later candidate comparison — not implemented by this slice

Select one model only after checking licence/runtime/privacy constraints. Define
a provider-neutral RerankerPort; candidate IDs and text must remain immutable.
Use the same candidate pools and report paired held-out results including every
regression. Proposed continuation criteria: improved held-out ranking with no
decrease in recall@5, reproducible traces and zero observed provenance/authority
violations in the defined tests. These are not release acceptance criteria.
An upstream reranker can have its ordering overwritten by the current extractor;
future work must specify the exact insertion point and measure final selection.
Clinician-reviewed evidence, independent assurance and owner release decisions
remain separate prerequisites before any production influence.

## Run

From a repository checkout with its exact-pinned development dependencies:

```bash
python -m medical_ai.evals.lexical_baseline --json-out /tmp/ret-exp-001.json
python -m pytest tests/test_lexical_baseline.py
```

No network is required by the benchmark; dependency installation is separate.
Rollback: omit/revert this offline evaluation addition. No runtime toggle or
database migration is involved.
