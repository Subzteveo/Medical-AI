# Alpha2.1 source import provenance

## Original artifact

- Package: `medical-ai-v0.1.0-alpha2.1-remediation.zip`.
- SHA-256 of the complete, unchanged ZIP: `9f574ff4998ee11ca3ff2a77e6014312159bc96d63457e25f41702fac74f95d8`.
- [Original ZIP in the Medical AI Drive folder](https://drive.google.com/file/d/1dEBbF8thjJekjGu7rodFIWPO6ArQWLrt/view?usp=drivesdk).
- [Earlier verification record](https://drive.google.com/file/d/1HlpyBmHaTwmut_-3aTrFfODyzODZXOnm/view?usp=drivesdk). Its 63/63 passing tests are historical evidence, not evidence that this GitHub PR or live connectors passed.
- The ZIP has 110 files: 109 entries listed in its own `RELEASE_SHA256SUMS` and the manifest itself. Keep the original ZIP and full manifest together for archive-level replay.

## Curated repository import

The import takes the application source, policies, tests, prompts, evaluation fixture, and documents from that ZIP. Of the 73 artifact paths tracked in `provenance/SOURCE_SHA256SUMS`, 72 initially match the ZIP byte for byte. The exception is `tests/test_ultrareview_regressions.py`: its checksum-script test now points at the repository's source verifier because the archive-only release script and full ZIP manifest do not describe this curated GitHub tree.

The source manifest is a **repository-revision checksum list**, not a claim that a later edited source tree is byte-identical to the original ZIP. It is checked, never regenerated, in CI. Future PRs that change a listed file must make a deliberate, reviewable manifest update and describe the deviation. The ZIP hash above remains the fixed reference for the original artifact.

The import omits duplicate `build/lib/` files (24), generated `src/*.egg-info/` metadata (5), the archive-only `scripts/generate_release_checksums.py` and `scripts/release_checksums.py`, and the original workflow (replaced by this repository's checks). It preserves governance files already on `main` (`AGENTS.md`, `README.md`, `.gitignore`, `project_docs/PROJECT_INDEX.md`, `project_docs/STATUS.md`, `project_docs/DEVELOPMENT_WORKFLOW.md`) instead of replacing them with older packaged versions; the index, status, and README are updated for the import. The original full archive remains accessible from the link above for anyone who needs to replay its release checksum procedure.

`docs/Medical MCP Landscape.txt` is historical product research from the Medical AI ZIP. Its evaluations of third-party tools and dated assertions are not verified connector behavior or authority for medical claims. No App by AI or Make AI do Good application source is imported.

## Scope of current checks

The deterministic CI workflow verifies repository source checksums, tracked-file hygiene patterns, pinned dependency installation, tests, Python compilation and import, and that installed policy resources equal their repository copies. A targeted pattern scan cannot establish the absence of all secrets or patient information. Live PubMed/ClinicalTrials retrieval, clinical safety validation, accessibility, licensing of external datasets, deployment, and regulatory release remain separate work.
