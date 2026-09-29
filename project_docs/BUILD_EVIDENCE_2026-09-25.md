# Build Evidence — 25 September 2026

Environment: provided Linux container / Python 3.13 runtime. This is build-environment evidence, not Windows/macOS/browser/production evidence.

## Observed checks before final packaging

1. `python -m pytest` → **Passed**, `22 passed in 0.37s` on the integrated alpha2 source tree.
2. `python -m compileall -q src` → **Passed**.
3. Standard editable install with build isolation → **Blocked by environment** because pip attempted to resolve `setuptools>=68` from an unavailable package index. This did not establish a package defect.
4. `python -m pip install -e . --no-build-isolation` using already provisioned dependencies → **Passed**; package built/installed as `medical-ai-evidence-workbench==0.1.0a2` and import reported `0.1.0-alpha2`.
5. Installed-package static asset lookup for `medical_ai/static/index.html` → **Passed**.
6. Live PubMed connector smoke attempt → **Blocked**, DNS/name-resolution error in the build environment.
7. Live ClinicalTrials.gov connector smoke attempt → **Blocked**, connection timeout in the build environment.
8. Initial secret-pattern regex → **False positive** on the string `risk-based-security-privacy-engineer`; the scanner pattern was corrected to require a token boundary.
9. Corrected high-risk credential/private-key token scan → **Passed**, no target token patterns found.
10. Source-tree checksum generation + immediate checksum verification → **Passed** before this evidence document was added; the manifest is regenerated again as part of final packaging.

## Interpretation

These observations support source/test/package behavior only within this environment. They do not establish live connector compatibility, fresh-machine installation with network dependency resolution, accessibility conformance, PHI compliance, clinical safety validation, deployment or public-release readiness.

Exact ZIP hash and post-extraction package verification are recorded outside the ZIP after the immutable archive is produced, because writing those results into the archive would change the artifact being attested.


## 25 September 2026 ultrareview addendum

The original alpha2 green suite remains a historical execution fact, but later independent ultrareview demonstrated that the suite did **not** establish several safety claims it was being used to support. See `project_docs/ULTRAREVIEW_REMEDIATION_2026-09-25.md`. The alpha2 baseline must not be described as safety-verified on the basis of the original 22 tests.
