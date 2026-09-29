# Canonical Status Review — 25 September 2026

The previously approved `v0.1.0-alpha2` ZIP remains an immutable historical artifact. Its exact bytes should be preserved for audit/reproduction.

However, the later ultrareview reproduced critical defects that invalidate several safety claims associated with that build. Therefore:

- keep alpha2 as the **historical canonical baseline**;
- do **not** use alpha2 as a release/deployment candidate;
- do **not** treat its original `22/22` suite as evidence that high-consequence or privacy gates were verified;
- consider `v0.1.0-alpha2.1-remediation` a **candidate successor**, not canonical-active, until its own final artifact is independently rerun/approved.

No Drive archive or prior approval record is modified by this document.
