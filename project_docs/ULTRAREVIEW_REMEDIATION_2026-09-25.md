# Ultrareview Remediation Record — 25 September 2026

## Baseline

Canonical alpha2 ZIP SHA-256 reported and reproduced by external review:

`b2f46775c6b68f62f390830ffcff631903ff0bdb3160ae32c53314fa56319bf9`

The canonical ZIP is preserved unchanged. Remediation occurs in a separate working copy.

## Red regression checkpoint

The supplied ultrareview narrative and script fragment were converted into 41 deterministic pytest cases covering the reproduced critical findings and material minor findings available in the review.

Combined suite before implementation fixes:

`34 failed, 29 passed`

This establishes that the regression suite actually reproduced failures on the alpha2 implementation.

## Remediation implemented

- runtime consequence categories now mirror and load the packaged consequence policy;
- regex/category handling covers inflections and previously missing high-consequence categories;
- claim text is independently consequence-classified, not merely inheriting query level;
- patient/identifier detection covers the five reproduced examples while the UI remains explicit that detection is heuristic;
- PubMed publication types are captured and retracted records marked superseded;
- ClinicalTrials.gov narrative descriptions cannot become efficacy/safety EvidenceUnits;
- retrieval questions are normalized before public-source search;
- empty search results are distinguished from absence of an authoritative connector;
- sentence splitting protects common abbreviations such as `vs.` and `i.e.`;
- trace query digests use keyed HMAC;
- regulatory routing avoids `registered nurse`/`approved outcome measure` false positives and uses requested jurisdiction in refusal text;
- default trace path no longer depends on current working directory;
- browser output renders structured claims/links rather than literal Markdown;
- runtime/development dependencies are pinned;
- checksum verification no longer regenerates the manifest;
- overlapping instruction-injection sentences are filtered from evidence extraction;
- all four packaged policy files are loaded by the runtime path, with consequence policy categories checked against implementation.

## Green checkpoint

Combined suite after remediation:

`63 passed`

## What this does not prove

This does not prove clinical safety, complete PHI detection, live-source behavior on the final package, retrieval recall targets, independent high-consequence verification, accessibility conformance, regulatory status, or readiness for public/commercial release.
