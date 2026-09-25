Yes. I would formalize this as a **Medical Evidence Influence Policy v0.1**.

There is no universal regulator-defined number such as “97% accuracy means safe.” Current guidance instead emphasizes intended use, evidence quality, transparency, representative validation, lifecycle monitoring, risk management, and the ability for users to understand limitations. WHO explicitly calls for rigorous evaluation before widespread health use; NHMRC requires transparent, current, systematically assessed evidence; FDA/IMDRF guidance emphasizes representative data, human-AI performance, limitations, monitoring, and transparency. ([who.int](https://www.who.int/publications/i/item/9789240084759?utm_source=chatgpt.com))

So the numerical thresholds below should be **our engineering release criteria**, not presented as regulatory requirements.

## The fundamental rule

> **A model is never evidence.**

The model may retrieve, classify, extract, compare, translate, explain, or synthesise evidence.

But a medical factual claim should enter a user-visible answer only when the system can trace that claim back to an admissible source.

That gives us a pipeline like:

**Question → retrieval → source qualification → evidence extraction → synthesis → claim verification → safety check → answer**

Not:

**Question → LLM → answer**

---

# 1. Source gate

A source should not influence a medical answer unless we can answer:

**Who published it? What exactly is it? Which version? When was it updated? What jurisdiction/population does it apply to? And can we point to the exact evidence supporting the generated claim?**

NHMRC's standards similarly emphasize transparent source evidence, systematic evidence assessment, explicit links between recommendations and supporting evidence, and keeping guidelines current. ([nhmrc.gov.au](https://www.nhmrc.gov.au/guidelinesforguidelines/standards?utm_source=chatgpt.com))

### Mandatory minimum

| Requirement | v1 threshold |
|---|---|
| Publisher | Identifiable |
| Document identity | Stable URL, DOI, PMID, guideline ID, regulatory ID or equivalent |
| Provenance | Exact retrieved passage/document section retained |
| Publication/version date | Known where applicable |
| Jurisdiction | Identified where relevant |
| Evidence type | Classified |
| Superseded status | Checked for guidelines/regulatory material |
| Licence/access | Legitimate use permitted |
| Citation | Recoverable from every downstream claim |
| Source integrity | Original source preferred over search result/snippet |

A Google result, chatbot answer, Reddit post, SEO health page or search-engine snippet could help **discover** evidence.

It should not itself establish a clinical fact.

---

# 2. Source authority must depend on the claim

I would not create one universal source ranking.

Instead create a **claim → acceptable source class matrix**.

For example:

| Claim | Minimum preferred evidence |
|---|---|
| Australian drug contraindication | Current TGA-approved PI / authoritative medicines source |
| Regulatory status | Regulator itself |
| Clinical recommendation | Current recognised clinical guideline |
| Treatment efficacy | Guideline/systematic review/meta-analysis; primary trials where appropriate |
| New trial result | Published primary study |
| Drug safety signal | Regulator/pharmacovigilance source and supporting literature |
| Disease prevalence | Appropriate official surveillance or population study |
| Diagnostic accuracy | Appropriate validation study/systematic review |
| Rare emerging phenomenon | Primary evidence, explicitly labelled uncertain |
| Biological mechanism | Peer-reviewed literature/reference resource |
| Patient education | Authoritative consumer-health material |

This avoids a common mistake: assigning a source a generic "9/10 authority score."

A randomized trial may be excellent evidence for treatment efficacy but completely inappropriate for establishing current Australian regulatory status.

---

# 3. Evidence strength gate

The engine should distinguish:

**fact retrieval** from **evidence synthesis** from **clinical recommendation**.

When synthesising evidence, it should explicitly track at least:

- study design
- population
- sample size
- comparator
- outcomes
- effect size
- uncertainty/confidence intervals
- risk of bias
- inconsistency
- indirectness
- imprecision
- publication bias where applicable
- applicability to the user's question
- conflicts/funding where available

These overlap strongly with GRADE methodology; Cochrane describes certainty assessment around risk of bias, inconsistency, indirectness, imprecision and publication bias. NHMRC now requires GRADE Evidence-to-Decision methods for guidelines seeking its approval. ([cochrane.org](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-14?utm_source=chatgpt.com))

### Important consequence

A model should never turn:

**"one small observational study found X"**

into:

**"X is recommended."**

Those are different epistemic categories.

---

# 4. Freshness gate

Freshness should be **domain-specific**, not simply "prefer newest."

For example:

**Extremely freshness-sensitive**
- regulatory warnings
- recalls
- product information
- drug availability
- infectious-disease guidance
- vaccination recommendations

**Moderately freshness-sensitive**
- clinical guidelines
- pharmacotherapy recommendations
- screening guidelines

**Potentially durable**
- anatomy
- basic physiology
- established mechanisms
- historical landmark evidence

A retrieved guideline known to have been superseded should be automatically excluded from recommendation-generation unless the user specifically asks for historical information.

The NHMRC standards explicitly require guidelines to be based on an up-to-date body of evidence and to specify when updating should occur. ([nhmrc.gov.au](https://www.nhmrc.gov.au/guidelinesforguidelines/standards?utm_source=chatgpt.com))

---

# 5. High-risk claim rule

I would create a special category called a **High-Consequence Medical Claim**.

Examples include claims involving:

- medication dose
- contraindication
- drug interaction
- pregnancy
- paediatrics
- renal/hepatic dose adjustment
- anticoagulation
- allergy
- emergency treatment
- toxicology
- diagnostic exclusion
- treatment initiation/discontinuation
- cancer therapy
- interpretation that could materially alter patient care

For these claims, v1 should require:

> **One directly applicable Tier-1 authoritative source OR concordance between at least two independent appropriate sources.**

And every high-consequence claim should undergo a second verification pass.

If sources materially disagree:

> **Do not let the LLM silently choose a winner.**

Show that disagreement.

---

# 6. Citation entailment gate

This could become one of the most important metrics in the entire system.

The question isn't:

> "Did the AI provide a citation?"

It is:

> **"Does the cited source actually support the claim immediately preceding it?"**

For the offline evaluation suite, I would target:

**≥99% citation correctness for ordinary medical factual claims**

and

**100% observed citation correctness for high-consequence claims in the release test suite.**

A citation counts as incorrect if it:

- doesn't contain the claimed information;
- refers to a different population;
- changes correlation into causation;
- exaggerates study conclusions;
- omits a material qualification;
- cites a secondary source when claiming primary evidence;
- references an outdated/superseded recommendation;
- doesn't exist.

Citation hallucination should be treated as a **release-blocking defect**, not cosmetic failure.

---

# 7. Model gate

Every model should be approved **per task**, not globally.

A model might be approved for:

**query expansion**

but not:

**clinical synthesis**.

Another might be approved for:

**biomedical NER**

but not:

**interpreting treatment evidence**.

Therefore maintain a capability registry such as:

| Model | Retrieval | Extraction | Reranking | Synthesis | High-risk synthesis |
|---|---:|---:|---:|---:|---:|
| Model A | ✓ | ✓ | ✓ | ✓ | ✗ |
| Model B | ✓ | ✓ | ✓ | ✗ | ✗ |
| Specialist model C | — | ✓ | — | — | — |

FDA/IMDRF good-machine-learning-practice guidance likewise emphasizes that performance should be evaluated in relation to intended use, representative data and the performance of the human-AI team rather than relying on generic model capability claims. ([fda.gov](https://www.fda.gov/medical-devices/software-medical-device-samd/good-machine-learning-practice-medical-device-development-guiding-principles?utm_source=chatgpt.com))

---

# 8. Minimum model evaluation suite

Before a model influences production medical answers, I would require evaluation across at least:

**Factuality**

Does it accurately represent supplied evidence?

**Citation attribution**

Does every source-backed claim point to evidence that actually entails it?

**Extraction**

Can it accurately extract populations, interventions, outcomes, doses, contraindications, etc.?

**Contradiction handling**

Can it recognize when two authoritative sources disagree?

**Abstention**

Can it decline to draw conclusions when the evidence doesn't support one?

**Instruction robustness**

Does paraphrasing the same question materially alter the medical conclusion?

**Temporal reasoning**

Can it distinguish older from current recommendations?

**Jurisdiction**

Does it distinguish Australian recommendations from US/UK/EU ones?

**Population generalisation**

Does it avoid transferring evidence from adults to children, males to pregnancy, one disease population to another, etc.?

**Adversarial safety**

Can misleading prompts force it to misrepresent evidence?

**Subgroup performance**

Does performance materially degrade across clinically relevant demographic or disease groups?

---

# 9. Critical safety threshold

For the release test suite:

> **Zero observed catastrophic or critical clinical safety failures.**

A critical failure could include:

- inventing a contraindication;
- reversing a contraindication;
- producing the wrong drug dose;
- confusing mg and µg;
- missing a clearly documented dangerous interaction;
- attributing evidence to a nonexistent trial;
- recommending an intervention explicitly contraindicated by the supplied source;
- failing to flag an emergency scenario when the workflow is supposed to detect one.

One such failure should block that model/workflow version from the relevant capability.

Importantly, **0 observed failures does not mean zero real-world risk**.

For example, observing zero critical failures across 1,000 independent tests only gives an approximate 95% statistical upper bound of ~0.3% on the underlying rate. Clinical deployment would therefore require considerably more validation than merely passing an internal benchmark.

---

# 10. Abstention should be a feature

The system needs an explicit state:

**"Evidence insufficient to answer."**

Other acceptable states might be:

**Evidence conflicting**

**Source outdated**

**Population mismatch**

**No authoritative source found**

**Jurisdiction unclear**

**Outside validated capability**

The model should receive a higher safety score for appropriate abstention than for producing a plausible but unsupported answer.

---

# 11. Retrieval gate

Even an excellent LLM cannot repair consistently poor retrieval.

I would therefore independently evaluate the retrieval system.

For a curated medical benchmark, I'd want something like:

**≥98% authoritative-source recall@k for questions where an authoritative source exists.**

For high-consequence questions, target as close to **100% observed recall** as practical in the validation set.

Otherwise the model can faithfully synthesise exactly the wrong documents.

---

# 12. Evidence conflict detector

The architecture should actively search for disagreement.

Suppose:

- Australian guideline says A;
- American guideline says B;
- a newer RCT suggests C.

The system shouldn't merge them into an invented compromise.

It should output something structurally like:

**Australia:** A  
**US:** B  
**Recent evidence:** C  
**Reason for difference:** unknown / population / evidence date / methodology / policy context

This is particularly important for an international medical evidence engine.

---

# 13. Claim-level provenance

Every substantive medical claim should internally carry something like:

```text id="yi9ndt"
claim_id
claim_text
source_id
source_version
source_passage
retrieval_timestamp
jurisdiction
population
evidence_type
certainty
model_id
prompt/workflow_version
verification_status
```

The user doesn't need to see all of this.

But the system should be able to reconstruct it.

Think of it as a **medical answer audit trail**.

---

# 14. Workflow reproducibility

Every answer should record:

- retrieval query;
- databases searched;
- retrieved documents;
- ranking scores;
- document versions;
- model/version;
- system prompt version;
- tool calls;
- extracted evidence;
- generated claims;
- citation mappings;
- verifier results;
- safety flags.

That makes an answer reproducible enough to investigate when something goes wrong.

TGA's software guidance emphasizes lifecycle controls including design, version control, risk management, verification, validation, configuration/change management and problem resolution. ([tga.gov.au](https://www.tga.gov.au/products/medical-devices/software-and-artificial-intelligence-ai/overview/standards-software-based-medical-devices?utm_source=chatgpt.com))

---

# 15. Change-control gate

Changing any of these should trigger regression testing:

- LLM
- embedding model
- reranker
- chunking algorithm
- retrieval strategy
- prompt
- source
- terminology mapping
- drug database
- guideline version
- safety classifier

A model update from, say, version X to version Y should therefore be treated as a potentially meaningful **system change**, not automatically deployed because benchmark marketing says the new model is better.

Current FDA guidance similarly treats AI-enabled medical software through a lifecycle/change-management lens, including verification and monitoring of planned changes. ([fda.gov](https://www.fda.gov/medical-devices/artificial-intelligence-enabled-medical-devices/predetermined-change-control-plans-machine-learning-enabled-medical-devices-guiding-principles?utm_source=chatgpt.com))

---

# 16. Separate "evidence confidence" from "model confidence"

This distinction is critical.

The UI should not say:

**Confidence: 94%**

simply because an LLM returned a probability.

Instead represent concepts such as:

**Evidence certainty:** High / Moderate / Low / Very Low  
**Source authority:** Regulatory / Guideline / Systematic review / Primary research  
**Agreement:** Concordant / Mixed / Conflicting  
**Applicability:** Direct / Partial / Indirect  
**Freshness:** Current / potentially outdated

Those dimensions actually tell the user something.

---

# 17. Human oversight threshold

The required human role should increase with consequence.

I would design four operating levels:

| Level | Use | Requirement |
|---|---|---|
| **L0** | Search/discovery | Automated |
| **L1** | Educational explanation | Automated with citations |
| **L2** | Clinician evidence synthesis | Strong provenance + verification |
| **L3** | Patient-specific decision support | Separate clinical/regulatory validation |
| **L4** | Autonomous diagnosis/treatment | Out of v1 scope |

This is particularly relevant in Australia. TGA states that some basic CDSS can qualify for an exemption, but software performing more advanced analysis, diagnosis/treatment specification, or opaque AI-generated recommendations may fall outside that exemption and may require ARTG inclusion if it is a medical device. ([tga.gov.au](https://www.tga.gov.au/resources/guidance/understanding-clinical-decision-support-system-software-regulation?utm_source=chatgpt.com))

---

# 18. Bias and representativeness gate

Before approving a model for clinical-data-derived tasks, document:

- training/validation population;
- geography;
- age distribution;
- sex;
- ethnicity where relevant and lawful;
- disease prevalence;
- care setting;
- language;
- device/data source;
- inclusion/exclusion criteria.

Then evaluate clinically meaningful subgroups separately.

I would trigger investigation when an important subgroup's safety/performance metric falls more than roughly **5 percentage points** below overall performance, unless there is a defensible clinical reason.

Don't hide subgroup failure inside a high aggregate score.

FDA/Health Canada/MHRA transparency guidance specifically recommends communicating dataset characteristics, population gaps, known biases, confidence intervals, failure modes and limitations. ([fda.gov](https://www.fda.gov/medical-devices/artificial-intelligence-enabled-medical-devices/transparency-machine-learning-enabled-medical-devices-guiding-principles?utm_source=chatgpt.com))

---

# 19. Privacy gate

This sits slightly outside evidence quality, but should still be mandatory.

A component that receives identifiable health information should **not automatically become approved just because its medical performance is excellent**.

PHI-capable workflows need a separate approval covering:

- data minimisation;
- retention;
- encryption;
- access controls;
- logging;
- data residency where applicable;
- vendor contractual terms;
- whether inputs are used for model training;
- breach procedures;
- deletion;
- jurisdiction-specific privacy obligations.

So maintain two independent flags:

**Medical evidence approved**

and

**PHI approved**

A component may receive the first and fail the second.

---

# 20. Post-deployment monitoring

Passing pre-release evaluation is not enough.

Track:

- unsupported claim rate;
- citation failure rate;
- retrieval failure rate;
- abstention rate;
- user-reported medical errors;
- high-risk queries;
- outdated-source incidents;
- model drift;
- retrieval drift;
- subgroup failures;
- source outages;
- latency-related fallbacks.

WHO and medical-device regulators increasingly frame AI safety as a lifecycle governance problem rather than a one-time benchmark exercise. ([who.int](https://www.who.int/publications/i/item/9789240084759?utm_source=chatgpt.com))

---

# The minimum production rule I would actually implement

Before any component can **influence** a user-facing medical answer, it must pass five gates:

### **E — Evidence**
Is the underlying evidence admissible for this particular claim?

### **P — Provenance**
Can we trace the claim to an exact, current source?

### **V — Validation**
Has this component/workflow passed task-specific testing?

### **S — Safety**
Does it pass high-consequence, adversarial, subgroup and abstention testing?

### **M — Monitoring**
Can we identify its version, detect failures and remove/roll back it?

So:

> **Influence allowed = E ∧ P ∧ V ∧ S ∧ M**

Fail any one → the component does not get production influence.

---

## And I would add one unusually strict architectural rule

**No model gets direct write-access to medical truth.**

The final answer generator should be constrained by a structured evidence object assembled upstream:

```text id="7spkkw"
QUESTION
    ↓
RETRIEVAL
    ↓
SOURCE ADMISSIBILITY
    ↓
EVIDENCE OBJECTS
    ↓
CLAIM GENERATION
    ↓
CLAIM ↔ EVIDENCE VERIFICATION
    ↓
SAFETY / CONFLICT / FRESHNESS CHECK
    ↓
USER ANSWER
```

The LLM becomes the **reasoning and communication layer over an evidence system**, rather than the evidence system itself.

That distinction could become one of the central architectural principles of the entire Medical Evidence MCP Gateway.