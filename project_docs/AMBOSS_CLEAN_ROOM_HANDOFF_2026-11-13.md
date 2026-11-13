# AMBOSS Clean-Room Competitive Architecture Handoff — 13 November 2026

**Status:** Documentation-only competitive intelligence handoff.  
**Repository:** `Subzteveo/Medical-AI`  
**Observed base:** `f292523c3fd94983b2df48812739dbeba6ac0d06`  
**Branch:** `docs/amboss-clean-room-handoff-20261113`  
**Release effect:** None. No runtime, policy, connector, model, deployment or clinical capability change.  
**Clinical/public/commercial release posture:** Unchanged — **NO-GO**.

## Parent objective

Build Medical-AI into an Australian-first, globally extensible, evidence-bound medical learning and research platform by learning deeply from strong adjacent products without copying protected implementation or weakening Medical-AI's evidence, privacy, jurisdiction or human-governance boundaries.

## Current objective

Understand how AMBOSS appears to achieve its products and services, identify overlap with Medical-AI, distinguish disclosed facts from inference, and convert the useful findings into bounded engineering opportunities.

## Governing boundary

The user-supplied AMBOSS Terms of Use dated October 2025 expressly restrict reverse engineering, decompilation, disassembly, scraping/crawling, derivative use, commercial reuse, and feeding AMBOSS content into AI/ML systems or RAG without permission.

Therefore this work uses a **clean-room competitive-analysis boundary**:

- study public product behaviour, public documentation, public research, public privacy disclosures, public integrations, public job/engineering material and lawful observations;
- do not scrape protected content, bypass controls, decompile applications, extract private APIs, clone proprietary prompts, capture protected output corpora, or import AMBOSS content into Medical-AI training/RAG;
- recreate capabilities independently from first principles, public standards and independently licensed/authoritative sources.

## Evidence classification

Use these states when continuing this work:

- **DISCLOSED** — directly stated by AMBOSS or another primary public source.
- **OBSERVED** — directly visible in lawful public product behaviour or public interfaces.
- **STRONGLY INFERRED** — the most plausible architecture required to explain multiple disclosed/observed facts, but not confirmed.
- **UNKNOWN** — not established and must not be promoted into fact.

## Current reconstructed AMBOSS architecture

### DISCLOSED / high confidence

Public AMBOSS materials reviewed in this work indicate:

1. AMBOSS AI features use OpenAI API large-language models for generative AI functions.
2. AMBOSS discloses Google Vertex AI Ranking API for reranking/relevance improvement.
3. AMBOSS discloses MongoDB Cloud Services as database infrastructure used for AMBOSS AI features.
4. AI Mode searches AMBOSS medical content and selected external clinical sources rather than relying on unrestricted open-web retrieval.
5. AMBOSS presents source-linked synthesis, can indicate that relevant evidence was not found, and exposes differing recommendations.
6. Specialty/user context can affect presented information.
7. AMBOSS exposes medical knowledge through MCP to external AI/agent environments.
8. AMBOSS publicly describes a FHIR-based healthcare-integration roadmap progressing from evidence lookup, to chart context, to clinician-reviewed structured suggestions/write-back.
9. AMBOSS Knowledge Profile uses item-response theory / a Rasch model to maintain learner proficiency estimates and drive adaptive learning.
10. AMBOSS publicly evaluates clinical-AI behaviour with medically structured benchmarks including omission/commission and severity-weighted error concepts.

### STRONGLY INFERRED

The public facts are best explained by a shared platform of approximately:

```text
Human medical editorial system
        ↓
Structured medical knowledge core
        ↓
Candidate retrieval layer              [exact implementation UNKNOWN]
        ↓
Semantic reranking                     [Vertex disclosed]
        ↓
Selected source context
        ↓
LLM synthesis/reasoning                 [OpenAI API disclosed]
        ↓
Source-linked / bounded output
        ↓
Product workflow
```

The same underlying medical-knowledge asset appears to support multiple delivery surfaces:

```text
Medical knowledge core
    ├─ search/reference
    ├─ AI Mode Clinical Care
    ├─ AI Mode Learning
    ├─ specialised assistants
    ├─ question bank / adaptive learning
    ├─ institutional analytics
    ├─ MCP / agent access
    └─ healthcare / FHIR integrations
```

The likely competitive moat is therefore not a secret standalone foundation model. It is the combination of:

- structured and curated medical knowledge;
- expert editorial processes;
- medical metadata and relationships;
- source selection and versioning;
- high-quality retrieval and reranking;
- workflow-specific presentation;
- learner and clinician context;
- evaluation infrastructure;
- product distribution across many surfaces.

## Medical-AI overlap

Medical-AI already has stronger explicit concepts in several areas:

- `A model is never evidence`;
- separate evidence authority and information/PHI authority;
- Australian jurisdiction as first-class infrastructure;
- claim-level provenance and source binding;
- explicit source-class requirements;
- fail-closed influence control;
- supersession/freshness states;
- dependency/revocation semantics;
- evidence, terminology, clinical-data and research-data plane separation;
- explicit human release authority.

The repository at the observed base also explicitly records material implementation gaps:

- current product remains extractive rather than generative;
- current live evidence coverage is principally PubMed and ClinicalTrials.gov;
- no complete guideline/regulator/drug-interaction/terminology authority path;
- relevance remains lexical rather than a validated production reranker;
- general conflict handling remains incomplete;
- authoritative-source + independent clinical verifier path remains absent;
- no clinically reviewed retrieval gold set has established the proposed authoritative-source recall target;
- no public clinical deployment is authorised.

## Highest-value lessons to adopt independently

### 1. Retrieval quality is a first-class subsystem

Do not treat retrieval as an invisible prelude to generation.

Build and evaluate:

```text
query
→ candidate retrieval
→ jurisdiction/source-class filtering
→ semantic reranking
→ freshness/supersession checks
→ applicability/conflict checks
→ admissibility gate
→ claim/source binding
```

### 2. Reranking must be provider-neutral

Introduce a `RerankerPort` rather than hard-wiring one vendor.

Candidate adapters may later include:

- Vertex ranking;
- local cross-encoder;
- other independently validated rerankers.

Evaluate recall, precision, latency, privacy, cost and failure modes separately from answer-generation quality.

### 3. Add specialty/context without making it authority

User specialty may change ordering, explanation depth or workflow presentation.

It must not silently change:

- evidence authority;
- jurisdiction;
- factual truth;
- regulatory status;
- source admissibility.

### 4. Build one governed runtime, many workflows

Do not create unrelated AI products for each task.

A workflow should largely be defined by:

```text
intent contract
+ source policy
+ retrieval policy
+ risk classification
+ verification requirement
+ output schema
```

This can support evidence search, guideline comparison, study assistance, research review, consult preparation and other modes without duplicating the underlying evidence engine.

### 5. Keep deterministic/statistical authority separate from generative UX

AMBOSS's learner modelling provides a useful pattern: statistical learner-state estimation can remain separate from LLM explanation.

Medical-AI should preserve the same design principle broadly:

```text
measured / deterministic / governed state
        ↓
generative explanation or interaction
```

Never allow generative fluency to become the authority source.

### 6. Treat MCP/API as distribution, not a second knowledge system

A future Medical-AI MCP should expose the same governed evidence foundation used by the web application rather than constructing an independent truth path.

### 7. Evaluation must become an operation

Build independent evaluation for:

- authoritative-source recall@k;
- reranker performance;
- omission;
- commission;
- source/claim entailment;
- jurisdiction mismatch;
- superseded-source leakage;
- conflict recognition;
- population/applicability mismatch;
- abstention correctness;
- latency and availability;
- reproducibility.

## Proposed next bounded engineering objective

**A4 — Retrieval Intelligence and Authoritative Reranking Candidate**

Proposed architecture:

```text
QueryPlan
→ specialty/context enrichment
→ required authority classes
→ multi-source candidate retrieval
→ jurisdiction filter
→ provider-neutral semantic reranker
→ currency/supersession evaluation
→ conflict search
→ population/applicability check
→ evidence influence gate
→ claim/source binding
→ independent verifier
→ answer / qualification / WITHHOLD
```

### Candidate acceptance evidence

Before any production influence, require at least:

1. a frozen, clinician-reviewed retrieval benchmark;
2. authoritative-source recall@k measurement;
3. comparison of lexical baseline vs reranked candidate;
4. negative controls for wrong jurisdiction and wrong source class;
5. superseded/retracted-source tests;
6. conflict and population/applicability cases;
7. reproducible ranking traces;
8. exact candidate revision and deterministic regression evidence;
9. independent review;
10. owner release decision.

## Do not infer

The following remain **UNKNOWN** unless later established from primary evidence:

- AMBOSS first-stage search/index technology;
- exact embedding model(s);
- exact OpenAI model(s) used in each product;
- proprietary prompts;
- internal schemas;
- private APIs;
- proprietary editorial tooling;
- exact ranking thresholds;
- exact safety classifiers;
- internal clinical-review workflow;
- production infrastructure topology beyond public disclosures.

## Current gate

**GO:** continued public-source competitive intelligence, architecture reconstruction, benchmark analysis and independently implemented retrieval/reranking research.

**HOLD:** any implementation that acquires new medical influence before the current Medical-AI authority and verification gates are satisfied.

**STOP:** prohibited extraction, scraping, decompilation, protected-content reuse, access-control circumvention, or use of AMBOSS content as Medical-AI training/RAG material without permission.

## Smallest next action

Do not research another broad list of competitors.

Use this handoff to design one revision-bound **A4 retrieval/reranking experiment** against the current lexical baseline, with synthetic and independently licensed/public authoritative evidence only. Keep the change behind existing fail-closed gates and do not alter the clinical/public/commercial release posture.

## Continuity statement

This document is a dated competitive-intelligence handoff, not a canonical intended-use change, implementation approval, clinical validation, release decision or substitute for `project_docs/STATUS.md`, `docs/INTENDED_USE.md`, the Medical Evidence Influence Policy, current authority policies, CI evidence or human approval.
