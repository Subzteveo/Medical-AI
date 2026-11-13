# AMBOSS / NOHARM integration note — 2026-11-13

## Status

**PROPOSED / IMPLEMENTED-AS-ENGINEERING-PR / NOT CLINICALLY VALIDATED / NO RELEASE AUTHORITY**

This change transfers publicly observable design patterns and openly licensed
clinical-harm evaluation ideas into Medical-AI without copying AMBOSS private
source code, private data, prompts, model configuration, ranking logic or
authenticated product behavior.

## Publicly observed AMBOSS patterns

The public Clinical AI Mode material describes a bounded clinical search agent
that:

- retrieves from a curated medical corpus rather than the unrestricted web;
- links generated summaries back to reviewable source material;
- highlights differing recommendations rather than flattening disagreement;
- adapts presentation/context to specialty;
- exposes limits and indicates when relevant information is not found;
- positions AI output as decision support rather than a replacement for
  professional judgment.

These are product-contract observations, not proof of AMBOSS's internal
service topology.

Primary public source:
https://www.amboss.com/us/clinical-ai-mode

## Open NOHARM material used as engineering reference

The public NOHARM bundle in `ARISENetwork/mast` provides an openly licensed
clinical-harm benchmark and scorer.

Observed source files at investigation time:

- `benchmarks/donoharm/README.md`
  blob `9947daa6210fa22fdf1eba66a4c9fbb71f699861`
- `benchmarks/donoharm/DATA.md`
  blob `2a66f2d9abe1c072f01ea8ba2c238fbed299dd46`
- `benchmarks/donoharm/score.py`
  blob `b9ea251051575a2af5d28219ce023702de7d4eb5`
- `benchmarks/donoharm/judge/metrics.py`
  blob `08bd3bd358e94088bd44b18edd7b7269e5b3b64d`

Repository:
https://github.com/ARISENetwork/mast

The upstream repository identifies code as MIT licensed and the released
benchmark cases/rubrics as CC-BY-4.0. No upstream dataset content is vendored
by this PR.

## What this PR adds

`medical_ai.evals.clinical_harm` adds an independent Medical-AI implementation
of five engineering controls:

1. explicit omission-harm detection for required actions;
2. explicit commission-harm detection for prohibited/harmful actions;
3. severity-weighted precision, recall and F1 using the public 1/3/24/72
   severity scale as an engineering configuration;
4. a severe-harm flag that cannot disappear inside an average;
5. a fail-closed manifest completeness check plus a separately named
   severity-weighted decision-consistency measure across perturbations.

The local `decision_resilience` function is **not** the NOHARM published
Resilience implementation and must not be reported as that benchmark metric.

## Capability boundary

This PR does **not** establish:

- clinical safety;
- parity with AMBOSS;
- NOHARM leaderboard comparability;
- clinician validation of any Medical-AI output;
- authorization for diagnosis or treatment;
- production deployment;
- use of patient-identifying data.

The new module is evaluation plumbing. It becomes evidence of working
capability only when repository tests and CI execute on the exact PR head.

## Next integration gate

After this engineering primitive is green, the next bounded step is to add a
small synthetic Medical-AI case adapter that converts existing answer traces
into explicit action IDs and runs them through this scorer. Only after that
should the open NOHARM case subset be evaluated, with its license attribution,
judge/model configuration and reproducibility limits preserved.
