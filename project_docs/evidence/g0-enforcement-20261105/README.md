# G0 enforcement evidence — 5 November 2026

**Issue:** [#2 Repository hardening](https://github.com/Subzteveo/Medical-AI/issues/2)
**Observed `main`:** `9cb52ab549f81d01fb4a8accb8c92eb92f7e0220`
**Recorded:** 5 November 2026, Australia/Darwin
**Status:** partial G0 evidence. G0 remains **BLOCKED** until the unverified items below and Issue #26 are resolved.

This record is engineering-governance evidence only. It says nothing about medical safety, clinical validation, privacy compliance or release readiness.

## 1. Ruleset readback (public rules view, signed out)

Source: `https://github.com/Subzteveo/Medical-AI/rules/24023881`, read through the Claude desktop built-in browser at about 12:25 Darwin time. Nothing was changed.

| Setting | Observed | Evidence state |
| --- | --- | --- |
| Ruleset | ID `24023881`, named `Main PR + deterministic CI` (previously `LAB AI Sec`) | inspected |
| Enforcement | Active | inspected |
| Target | Default branch only | inspected |
| Restrict deletions | On | inspected |
| Require a pull request before merging | On | inspected |
| Required approvals | 0 | inspected |
| Required status check | `source-and-tests` (GitHub Actions) | inspected |
| Require branches to be up to date | `strict_required_status_checks_policy: true` (GitHub API readback via a ChatGPT conversation, about 12:46 Darwin time); also demonstrated in practice by §2 | inspected (API); executed (§2) |
| Do not require status checks on creation | `do_not_enforce_on_create: true` (same API readback): creating a new matching ref is not blocked by checks. `main` already exists, so this does not let changes into `main` without the check | inspected (API) |
| Block force pushes | On | inspected |
| Bypass actors | `"bypass_actors": []`, `"current_user_can_bypass": "never"` — GitHub API readback through the connected GitHub API in a ChatGPT conversation, reported by the owner at about 12:35 and re-confirmed at about 12:40 Darwin time; not independently re-read by Claude (API access refused in this session) | inspected (owner-reported) |
| Other rulesets | None listed (`/rules` shows one ruleset) | inspected |

Consequence of editing `LAB AI Sec` in place: non-default branches no longer have deletion or force-push protection from any ruleset.

## 2. Negative test: required check and up-to-date rule block a merge

Subject: [PR #40](https://github.com/Subzteveo/Medical-AI/pull/40), the owner-approved RED authority-origin regression for Issue #25. Head `d55828315c018ca04084048dad22615bf1733824`, base `93c20db`, so it is both failing and behind `main`.

Screenshot taken by the owner, signed in as `9TEVE-O`, on 5 November 2026 at about 12:28 Darwin time, cropped to the merge box: `pr40-merge-box.png`, SHA-256 `d1433b37942dd72559e6ca3c954a9813558f128a7790e263deb22b46c6b87353`. The image is not committed (the hygiene gate rejects binary files). At the time of writing it is held by the owner and **not yet attached to Issue #2**; attach it there and record the comment link before relying on it.

| Observed in the merge box | Meaning | Evidence state |
| --- | --- | --- |
| `Deterministic checks / source-and-tests (pull_request)` failing, marked **Required** | The ruleset's required check is attached to PR heads | executed |
| `Deterministic checks / source-and-tests (push)` failing, marked **Required** | Same check context on push | executed |
| "This branch is out-of-date with the base branch" | Up-to-date requirement is active | executed |
| **Merge pull request** button disabled | GitHub blocked the merge for the signed-in owner | passed |
| No "bypass rules and merge" option visible | Suggests the owner has no routine bypass; not proof | unproven |

PR #40 was not merged, updated or changed. Do not press **Update branch** on PR #40; that would add a merge commit and change its recorded head.

## 3. Not yet demonstrated

1. Bypass list: API readback reported empty (§1); the signed-in edit-view check is optional corroboration.
2. Signed-in visual check of the two settings in §1 that are API-verified only (optional corroboration).
3. A direct push to `main` being rejected. This is deliberately not attempted: if protection failed, the test itself would change `main`. The PR requirement and the readback above are used instead, unless the owner decides otherwise.
4. A green PR merging successfully under the same rules (positive control). The first ordinary docs PR will provide this.

## 4. Owner decisions recorded or pending

- **Required approvals = 0:** owner decision, 5 November 2026 ("confirm just 0 for approvals"); re-read live at about 12:33 Darwin time as `Required approvals: 0`. Reason: with one maintainer, GitHub does not allow self-approval, so a required approval would block every merge. The owner's merge click remains the human gate. Revisit when a second reviewer (needed for Issue #25) or a separate agent account exists.
- **All-branch protection:** pending owner decision whether to add a second ruleset restoring deletion and force-push protection on all branches.

## 5. Issue #2 closure

Acceptance criteria met by this record: protect `main` from direct merge without PR; require PRs; require exact-head / up-to-date checks; require the deterministic CI job; prevent force pushes and deletion on `main`.

Bypass policy: no bypass actors (§1, GitHub API readback via a ChatGPT conversation).

Still open: the positive control (§3 item 4). The pull request that adds this file is intended to be that control: it must pass `source-and-tests` at its exact head and merge through the normal path. Close #2 only after that merge is recorded.
