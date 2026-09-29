# Decisions and Risks — alpha2

## Consequential decisions

**DEC-001 — Keep the medical answer path extractive-first.**
Rationale: prove source/provenance/verification behaviour before adding generative synthesis. Reconsider only after retrieval and citation evaluation are quantitatively established.

**DEC-002 — Keep a single-process FastAPI architecture.**
Rationale: current requirements do not justify service boundaries. Reconsider at real independent deployment/ownership/scaling boundaries.

**DEC-003 — Use SQLite only for minimal local audit metadata.**
Rationale: durable trace identifiers are useful now; no multi-user distributed database invariant exists. Raw question/source text is excluded.

**DEC-004 — Patient-specific wording fails closed before public connectors.**
Rationale: PubMed/ClinicalTrials routes are not PHI-approved. This is a protective alpha rule, not a claim that heuristic detection identifies all PHI.

**DEC-005 — ClinicalTrials.gov is trial discovery, not treatment evidence authority.**
Rationale: a registry record can establish registered study facts; registration does not prove efficacy/safety.

**DEC-006 — No multi-agent build wave for alpha2.**
Rationale: planner/schema/orchestration/API/test changes share contracts. Parallel lanes would create coordination/merge cost without stable low-overlap ownership.

## Material risks

| Risk | Current control | Residual / next trigger |
|---|---|---|
| RISK-001 Unsupported medical generation | No generative synthesis; exact-passage verifier | Re-open when synthesis model is introduced; requires new eval gate |
| RISK-002 Patient-identifying data sent to public source | UI warning + deterministic patient-specific cue block + `phi_approved=false` connector metadata | Heuristic detection is incomplete. Public/PHI deployment remains blocked until robust intake/routing and privacy obligations are implemented/tested |
| RISK-003 Wrong source class/jurisdiction | Deterministic source routing and regulator fail-closed | Add TGA/PBS authoritative adapters before AU regulatory claims |
| RISK-004 Trial registry misrepresented as efficacy evidence | Trial-specific source class + renderer limitation | Add tests whenever results-section interpretation is introduced |
| RISK-005 Retrieval misses authoritative evidence | No generative fallback; recall@k harness | Build reviewed gold set and live benchmark before synthesis |
| RISK-006 Source/API change | Connector errors fail safe | Add live contract tests/version/freshness monitoring in alpha3 |
| RISK-007 Audit store becomes health-data repository | content-minimising payload, query digest only | Reassess retention/access/encryption before shared/public deployment |
| RISK-008 UI looks authoritative beyond validated scope | persistent intended-use/privacy notices + explicit answer states | Usability study and clinical-human-factors review before external clinical-facing release |
| RISK-009 Git/release provenance gap | package checksum + local artifact evidence | D3 GitHub/local baseline remains unproven until exact repo is verified |
