# UI/UX and Routes — alpha2

## Primary browser path

**Actor:** medical student, clinician or researcher.

**Task:** ask a general/de-identified evidence question, understand the system state, inspect admitted sources and see why a claim was or was not allowed.

### Route `/`

The workbench provides:
- clearly labelled question textarea;
- user-mode selector;
- jurisdiction selector;
- source-limit selector;
- explicit search action;
- persistent intended-use and privacy warning;
- live status text;
- answer panel;
- source inspection panel;
- expandable execution-trace explanation.

### Reachable result states

The API retains its exact canonical status codes. The user interface translates those codes into short, plain-language descriptions without changing their meaning or turning a blocked or uncertain result into apparent success. Important states include:

- `ANSWER_SUPPORTED_WITH_QUALIFICATIONS`
- `EVIDENCE_INSUFFICIENT`
- `NO_AUTHORITATIVE_SOURCE`
- `HIGH_CONSEQUENCE_VERIFICATION_FAILED`
- `OUTSIDE_VALIDATED_CAPABILITY`
- `SOURCE_UNAVAILABLE`

## Accessibility design target

The alpha2 shell uses native form controls, explicit labels, keyboard-visible focus, a status `aria-live` region, textual state names, responsive single-column fallback and no required mouse-only interaction. External source content is inserted with `textContent`, not HTML interpretation.

### Evidence still required

- real browser keyboard walkthrough;
- focus order and result focus/recovery observation;
- zoom/reflow at target browser sizes;
- automated accessibility scan as a limited check;
- screen-reader smoke test for the target platform/browser;
- contrast review in both supported color-scheme states.

No WCAG conformance claim is made by this design/automated shell inspection.

## Plain-language Evidence Atlas update (7 November 2026)

The authenticated workbench prioritises the search question, source-backed result, original source and exact supporting passage. Public-facing labels avoid internal authority and trace terminology; technical status codes and decision records remain in the existing protected API and safety checks. The interface still withholds all claims on an inconsistent response or an authorisation failure, and it labels missing clinical certainty and Australian medicines coverage explicitly. The invitation screen uses plain language without changing its access enforcement.

This is an interface presentation change only. It does not establish real-world clinical correctness, source freshness, Australian medical-device approval, public release, or native mobile availability. Review the exact pull-request head and browser QA before acceptance.
