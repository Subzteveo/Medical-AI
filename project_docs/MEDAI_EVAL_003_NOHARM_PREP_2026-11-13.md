# MEDAI-EVAL-003 — Licensed NOHARM Open-Subset Evaluation Preparation

**Status:** PREPARED / HOLD — DO NOT EXECUTE  
**Prepared:** 2026-11-13  
**Release authority:** Human owner  
**Parent evidence:** MEDAI-EVAL-002 exact-head PASS at `400a0122fba8d3247021dad3735b2926425892d7`  
**Clinical/public/commercial release posture:** NO-GO unchanged

## Purpose

Prepare a reproducible, licence-aware boundary for a future NOHARM open-subset evaluation without bypassing Medical-AI's existing patient-specific input controls or pretending that a benchmark protocol is compatible before that compatibility is demonstrated.

No NOHARM inference or judge API call has been executed by this preparation step.

## Upstream freeze

Repository: `ARISENetwork/mast`  
Pinned upstream commit: `57a12c5490f3a7a6b0a6ce4e0d49f8e393ff49ee`

Pinned NOHARM files:

| File | Git blob SHA |
|---|---|
| `benchmarks/donoharm/README.md` | `9947daa6210fa22fdf1eba66a4c9fbb71f699861` |
| `benchmarks/donoharm/DATA.md` | `2a66f2d9abe1c072f01ea8ba2c238fbed299dd46` |
| `benchmarks/donoharm/run.py` | `80ee605fdde08200c813da0ee4c53087b2751d24` |
| `benchmarks/donoharm/score.py` | `b9ea251051575a2af5d28219ce023702de7d4eb5` |
| `benchmarks/donoharm/judge/metrics.py` | `08bd3bd358e94088bd44b18edd7b7269e5b3b64d` |
| `benchmarks/donoharm/config/benchmark.yaml` | `a968a54cdeee3101341fa797e70961dc64b172ff` |
| `benchmarks/donoharm/config/models/example.yaml` | `0983127a8618f4b3d41325a1786760f65fd0bd49` |
| `benchmarks/donoharm/prompts/default.md` | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` |
| `benchmarks/donoharm/dataset/items.jsonl` | `94f4c656327c137ac244763640fa736cb5c1e854` |
| `benchmarks/donoharm/LICENSE` | `e505045bf5ff640a24b04304c903f6f7c16aafb4` |
| `benchmarks/donoharm/LICENSE-DATA` | `e9b34dc2a57d65c73c39f70bfe6ce494d9bee007` |

The whole benchmark directory remains pinned by the upstream commit, including rubric and judge-guidance files not individually enumerated above.

## Licence boundary

Observed upstream licence position at the pinned revision:

- code, runner, scorer and vendored judge: MIT;
- cases, perturbations, rubrics and guidance: CC-BY-4.0;
- requested data attribution: **ARISE Network, NOHARM benchmark**, with the applicable licence retained/linked;
- source/citation: Wu et al., *First, do NOHARM: towards clinically safe large language models*, arXiv:2512.01241.

Any copied or redistributed benchmark data must preserve the CC-BY-4.0 attribution requirements. This document is an engineering licence record, not legal advice.

## Reference protocol freeze

The current public open kit documents:

- 30 open base cases;
- up to 11 variants per base case;
- default `k=11`: 330 total items;
- one trial in `config/benchmark.yaml`;
- max tokens: 8192;
- default prompt: empty / unprompted;
- headline metric: `F1_weighted`;
- severe-harm visibility: `Severe_rate`;
- aggregate perturbation metrics: `F1_floor` and published NOHARM `Resilience`;
- 95% stratified cluster bootstrap, base case as sampling unit, B=10000;
- harm weights: Uncertain:Mild:Moderate:Severe = 1:3:24:72.

Pinned judge configuration documented in `DATA.md`:

- match judge: `gemini/gemini-3-flash-preview`;
- review judge: `gemini/gemini-3.5-flash`;
- reasoning effort: minimal;
- match + review stages produce the headline metric.

Preview judge behavior may drift even with the documented model IDs, so exact numeric reproduction is not guaranteed.

## Denominator / completeness invariant

The pinned scorer contains explicit completeness checks. The future Medical-AI run must preserve the same principle at every boundary:

1. frozen expected item/trial keys;
2. raw response completeness;
3. match-cache completeness;
4. review-cache completeness;
5. judged-file completeness;
6. no failed generation silently removed;
7. no duplicate record silently increasing the denominator;
8. no off-manifest record silently entering the score.

An incomplete run is **non-comparable** and must not publish a headline score.

## Material compatibility blocker

NOHARM is a patient-specific clinical management benchmark. Example open cases contain detailed individual patient scenarios and ask for a management plan.

The current Medical-AI runtime intentionally classifies patient-specific requests as outside validated capability and returns `OUTSIDE_VALIDATED_CAPABILITY` before sending the text to public evidence connectors.

That control is part of the current safety/privacy boundary.

Therefore:

> Running the NOHARM case text directly through the current Medical-AI public/runtime answer path would test the refusal boundary, not clinical management quality.

It would be technically misleading to call the resulting numbers a NOHARM capability score, and weakening or bypassing the patient-specific gate merely to obtain a benchmark number is not authorised.

## Candidate-system configuration status

The NOHARM example model config is **not** the Medical-AI candidate configuration. It names a generic LiteLLM model and warns that changing model IDs without changing the cache namespace can reuse stale responses/judgments.

Medical-AI is a governed evidence workflow rather than one model endpoint.

The candidate adapter/model configuration is therefore:

**UNRESOLVED / NOT FROZEN**

until the benchmark execution boundary below is approved and implemented.

## Smallest safe next architecture decision

Before any NOHARM execution, choose and verify one of these bounded paths:

### Path A — refusal-boundary study

Run selected public NOHARM cases against the unchanged Medical-AI runtime solely to verify that patient-specific cases fail closed.

This may establish refusal/control behavior.

It must **not** be reported as NOHARM clinical-performance evaluation.

### Path B — isolated benchmark-only research adapter

Create a non-production, non-routed evaluation adapter that:

- accepts only the pinned public NOHARM dataset by manifest identity;
- cannot accept arbitrary user or patient input;
- has no production/API route;
- does not alter Medical-AI's patient-specific public/runtime policy;
- labels benchmark data as licensed public research fixtures, not live PHI;
- records every input, output, source use, failure and configuration revision;
- cannot confer clinical or release authority;
- is independently reviewable and removable.

Only after that adapter passes its own privacy/authority tests should a clinical-performance NOHARM run be considered.

## Required pre-execution gate

Before MEDAI-EVAL-003 may execute:

- [x] MEDAI-EVAL-002 exact-head synthetic gate passed.
- [x] Upstream NOHARM commit frozen.
- [x] Code/data licence split verified.
- [x] Open case-manifest file pinned.
- [x] Scorer implementation pinned.
- [x] Judge IDs and public scoring protocol recorded.
- [x] Completeness/denominator invariant recorded.
- [ ] Candidate Medical-AI benchmark adapter frozen.
- [ ] Candidate model/system configuration frozen.
- [ ] Benchmark-only data routing reviewed against Medical-AI privacy/authority policy.
- [ ] Credential-handling plan approved for candidate inference and Gemini judging.
- [ ] Cost ceiling approved.
- [ ] Cache namespace and invalidation policy frozen.
- [ ] Independent review of metric/protocol equivalence complete.

## Current decision

**HOLD MEDAI-EVAL-003 execution.**

Reason: current Medical-AI correctly blocks the patient-specific scenario type that NOHARM is designed to evaluate. Direct execution would not measure the intended clinical-performance construct.

Smallest next action: design and adversarially review the isolated benchmark-only research adapter described in Path B, while preserving the unchanged production/runtime patient-specific refusal gate.

No merge, deployment, clinical release, public claim or commercial certification is authorised by this preparation.
