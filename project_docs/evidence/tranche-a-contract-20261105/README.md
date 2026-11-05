# Tranche A contract preservation record — 5 November 2026

**Issue:** [#26 Preserve verbatim owner-approved Tranche A contract](https://github.com/Subzteveo/Medical-AI/issues/26)
**Base `main`:** `24bd8332da86cae4a2a0509b763835edd4f00bdc`
**Recorded:** 5 November 2026, Australia/Darwin
**Disposition:** the original contract has been **recovered and owner-signed-off**. By owner decision, its full text is **held privately by the owner, outside this public repository**. This record pins it by SHA-256 so any copy can be checked. It does not reproduce, summarise or rewrite the contract.

This is engineering-governance evidence only. It says nothing about medical safety, clinical validation, privacy compliance or release readiness, and it does not mark A1, A2 or any runtime capability as implemented, approved or released.

## 1. What is preserved

| Item | Value |
| --- | --- |
| Title | Medical AI — Alpha3 Tranche A: Medical Evidence Influence Control Kernel |
| File name | `Medical_AI_Alpha3_Tranche_A_Implementation_Contract_2026-10-11.md` |
| Size | 332 lines, 37,883 bytes (UTF-8, LF line endings, final newline) |
| **SHA-256** | `bfa250de6be76084d84c26f827928c59c740e12a8280b2a4182bdb4c2a10786c` |
| SHA-256 without the final newline | `55a8819eeb161e0088c9a3bbc18737101372bd06c7c768d40fe456403577cc93` |
| Pinned inspection revision named in the contract | `13fadd41e628ff60de2cdfff933b3e2be19f1327` |
| Where the full text lives | Owner's private copy (not in this repository) |

A copy is the approved contract only if `sha256sum` (or `Get-FileHash -Algorithm SHA256`) returns the first hash above exactly.

## 2. Source and approval provenance

| Item | Value |
| --- | --- |
| Source | ChatGPT conversation "Draft Alpha3 Contract", ID `6aca6223-1fcc-83ec-8543-cbf52a9ebafe`, in the owner's Medical AI project (owner-only access) |
| Contract written | 10 October 2026 16:12:04 UTC (11 October 01:42 Darwin), message `9d5d0e85-4f57-43ed-839a-4a18597d6538` |
| Summary reply shown to the owner | message `ef19c0aa-7e06-47b8-9137-6bc4e132131b`, 8,330 bytes, SHA-256 `5719af5d2f74e4174b51d15c79c254d3aded9ee29d62fb2d73e129a0a8f48244`; links to the contract file |
| **Owner approval** | `Approved`, message `bbb21608-8997-4f32-a76d-433866ab08d4`, from the owner, 10 October 2026 19:11:54 UTC (11 October 04:41 Darwin); its parent is the summary reply |
| Owner sign-off of this recovery | 5 November 2026 about 13:43 Darwin: the owner confirmed that (1) this is the contract he approved, and (2) his `Approved` covers the full 37,883-byte file, not only the summary reply |

Machine-readable detail, including the cross-checks below, is in [`provenance.json`](provenance.json) (SHA-256 `6cb16634f38a94ab6bef7bc3985670eacab49d72b168b4260bcbe18478dad9ae`), stored unchanged from the recovery. It was written before the owner's sign-off, so its `status` field still reads "not yet owner-signed-off"; §2 above records the sign-off.

## 3. How it was recovered and checked

Recovered read-only on 5 November 2026 from the owner's signed-in ChatGPT session, with the owner's approval. Nothing in ChatGPT was changed.

- The text is the body of the command ChatGPT used to write the file. Size matches ChatGPT's own `wc` output at write time (`332 37883`).
- Structure is complete: 31 headings, sections 0–15, tests `A3A-001` to `A3A-024`, ending at the "Final contract decision" line.
- The conversation has a single path: no regenerated branches and no later edits.
- After approval ChatGPT re-read the file. Lines 240–332 match exactly. For lines 1–240 the first 8,028 and last 8,146 characters match; about 10,532 characters in between were cut by ChatGPT's display and have no post-approval readback.
- The three saved files were hashed on the owner's computer after saving; all matched the in-browser hashes.

## 4. Consistency with existing repository documents

- `project_docs/ALPHA3_TRANCHE_A_G0_CHECKPOINT.md` agrees with the recovered contract on title, 11 October date, pinned commit `13fadd41…`, CI runs `38063860401` and `38063858617`, the G0/A1–A4 sequence and the 24 tests. It remains a derivative record, not a substitute.
- `project_docs/ALPHA3_A1_SCHEMA_POLICY_REVIEW.md` (PR #23) references the contract but does not reproduce it. It remains derivative.

## 5. Limits

- The original sandbox file has expired. The text comes from ChatGPT's recorded write command, not from the file itself.
- A SHA-256 proves a copy is unchanged since capture. It does not by itself prove historical authenticity; that rests on the conversation record in §2.
- Because the full text is private, reviewers of this repository cannot read the contract here. Anyone who needs it must obtain the owner's copy and check it against §1.

## 6. Issue #26 checklist mapping

| #26 requirement | State |
| --- | --- |
| Locate the actual full approved text or an authoritative export | done (§2) |
| Verify scope, text, owner approval, date and exclusions with the owner | done: owner sign-off (§2) |
| Store the verbatim contract as a revisioned, labelled artifact with its digest | stored privately by owner decision; digest pinned here (§1) |
| Link from `PROJECT_INDEX.md` and the G0 checkpoint | this PR |
| Human owner/reviewer verifies the import is exact | owner sign-off recorded; reviewing and merging this PR is the owner's act |
| Mark DOCUMENTED/PRESERVED only on evidence | this record: **PRESERVED (private, hash-pinned)**. No ENFORCED, IMPLEMENTED, APPROVED or RELEASE_READY claim |

Closing #26, and deciding whether private hash-pinned storage satisfies it, is the owner's decision.
