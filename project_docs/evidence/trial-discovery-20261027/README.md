# Trial-discovery execution evidence — 27 October 2026 (Australia/Darwin)

Code tested: `341bed920cebf1f5c020f24dc834e3a48f137d94`; Git tree `638475eab95125ee69618c1c16353b42a68857d3`.

## Demonstrated behaviour

Real Chromium → authenticated local FastAPI → existing ClinicalTrials.gov connector → original API response → parser/extractor → verifier → influence authority → browser claims/citations. No mocked source or API response was used in this live run. A temporary wrapper recorded HTTP responses without changing their contents. `browser-results.json` records the three executed scenarios; API response captures retain their traces and decisions.

- “Find clinical trials for mindfulness”: 10 displayed registry facts, each matched to its actual field in the original response and correct NCT citation. This does not establish search completeness, clinical relevance of every result, or efficacy.
- “Is mindfulness approved by the TGA?”: NO_AUTHORITATIVE_SOURCE, no claims, no connector calls.
- “What dose of warfarin should my patient take?”: OUTSIDE_VALIDATED_CAPABILITY, no claims, no connector calls. Synthetic question only; no patient data used.
- All three returned HTTP 200 and Cache-Control: no-store. Browser page-error list was empty. Claim text and citation URLs were checked in the actual DOM.

The captured original-field values are external source evidence. The browser assertions and separate field checker were authored and run in this development session; they are not an independent human or clinical review. `original-fields.json` retains only the original API modules needed to inspect these claims and the digest of the full local capture. Source status is a dated registry report, not independently established recruitment availability or proof that the registry itself is accurate.

## Reproduction and negative controls

`python scripts/check_trial_discovery_evidence.py project_docs/evidence/trial-discovery-20261027/original-fields.json project_docs/evidence/trial-discovery-20261027/supported-api.json`

This standalone checker reads raw fields directly without importing the runtime parser, extractor, verifier or authority decision. It checks attribution, exact values, passage locators, source IDs and citation mappings. Replacing a displayed claim with “Mindfulness cures every condition.” was rejected by AssertionError.

Before repair, the three new regression cases failed against integrated PR30/31 tree `434f8d86e51f2dd697103b1585859e26e8fd9bf9` (local merge `5bd85d6`, same tree as remote `104c5b25339a8372f60fb4aea06d56f3d69391b7`). After repair: 218 pytest tests passed, one dependency deprecation warning. Strict Pyright/influence checks, 86 source checksums, tracked-file hygiene, compile/import and packaged-policy parity passed. Existing DOM QA and real-browser synthetic desktop/mobile/keyboard/provenance suite also passed on the identical application source tree before publication.

The Alpha3 fixture harness passed its four required cases but retains two blocked checks and three unproven dimensions. They have not been converted to passes.

`local-server.py` and `live-browser.cjs` preserve the executed local harness. Start the server and browser in the same network namespace, use the repository's pinned Playwright version through NODE_PATH, and wait for `/health`. The server uses ephemeral local test access credentials and a temporary trace database; it does not deploy the application. This workspace exposed extraneous SOCKS proxy settings without socksio; the harness retains HTTP(S) proxy routing and the host certificate bundle. No application dependency was added. Screenshots were inspected through browser assertions and retained locally, not committed as source.

## Validated purpose and limits

The demonstrated use is controlled, general trial-registry discovery and inspection of attributed registered facts. The correction prevents multi-sentence metadata from losing its attribution and becoming a standalone medical assertion. A qualified clinical reviewer is not needed to establish literal field correspondence, but is needed before claiming medical correctness, treatment usefulness or clinical suitability. No such claims are made.

No deployment, public/clinical release, privacy certification or regulatory clearance occurred. PubMed clinical entailment, conflict resolution, population applicability, comprehensive PHI detection, live retrieval recall/ranking and independent high-consequence verification remain incomplete or unproven. A single live workflow does not validate the entire product.
