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

The UI must display the backend status verbatim rather than converting failure/abstention into apparent success. Important states include:

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
