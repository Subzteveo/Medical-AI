# Medical AI v0.2 — Evidence Influence Control Core

Status: **development / in-flight**. This control core does not establish clinical safety, regulatory compliance, or production readiness.

## Governing rule

**A model is never evidence.**

A verified claim is still not permitted to affect user-visible medical output until it passes the machine-enforced influence gate.

## Canonical objects

`src/medical_ai/schemas.py` now defines machine-readable canonical objects for `Source`, `EvidenceObject`, `Claim`, `CitationMapping`, `ConnectorApproval`, `PHIClassification`, `WorkflowRun`, and `VerificationResult` while retaining the alpha2 record types for compatibility.

## Independent authority dimensions

Every influence-capable subject presented to the control core carries two separate authority states:

- `evidence_authority`: whether the object may contribute evidence toward a medical proposition;
- `information_handling_authority`: whether the object may handle the information class involved in the transition.

`APPROVED`, `DENIED`, `UNKNOWN`, and `REVOKED` are distinct states. Unknown state fails closed. Approval in one dimension does not grant approval in the other.

## Data planes

The typed planes are:

- `EVIDENCE`
- `TERMINOLOGY`
- `CLINICAL`
- `RESEARCH`

The v0.2 core allows same-plane transitions only. In particular, clinical or research objects cannot directly transition into the evidence plane to establish a medical proposition. Future cross-plane operations must be added explicitly rather than inferred.

## Authorization flow

`InfluenceController.authorize()` is the authoritative gate for final medical influence in the current engine path. It evaluates:

1. evidence authority;
2. information-handling authority;
3. source and target data planes;
4. information classification;
5. provenance completeness;
6. validation state;
7. safety state; and
8. monitoring/trace availability.

Any failed or unknown required state yields a `DENY` decision. Every call emits an `InfluenceDecision` containing the object, proposition, policy version, evaluated dimensions, transition, reasons, and result. Allowed decisions are also registered as typed dependencies.

The evidence engine authorizes each verified claim before it is passed to the renderer. Claims denied by the influence controller are not included in user-visible claim output.

## Dependency and revocation semantics

Dependencies are typed by authority/gate dimension. `revoke_authority()` changes only the selected authority dimension and invalidates only downstream states with an edge on that dimension.

For example, revoking `EVIDENCE_AUTHORITY` invalidates an evidence-dependent claim but does not itself revoke `INFORMATION_HANDLING_AUTHORITY`, nor does it invalidate a separate downstream state that depends only on information-handling authority.

The controller stores the current authority state for admitted subjects, so a stale caller cannot bypass a prior revocation by resubmitting an older `APPROVED` object snapshot.

## Fail-closed cases covered by tests

`tests/test_influence_control.py` covers:

- evidence-approved but information-handling-denied;
- information-handling-approved but evidence-denied;
- unknown authority and unknown information classification;
- denied clinical/research-to-evidence transitions;
- missing provenance;
- failed validation;
- failed safety gate;
- missing monitoring state;
- authority-dimension-selective revocation; and
- stale approved-state replay after revocation.

Run the deterministic suite with:

```bash
python -m pytest
```

The repository checksum manifest must be updated deliberately whenever tracked source/test files change; CI verifies the committed manifest rather than regenerating it.
