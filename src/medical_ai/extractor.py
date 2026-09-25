from __future__ import annotations

import hashlib
import re

from .schemas import EvidenceUnit, Passage, SourceRecord

WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-]+")
STOP = {"what","which","when","where","who","why","how","does","do","is","are","was","were","the","a","an","of","to","and","or","in","on","for","with","about","evidence","show","shows","find","trial","trials","clinical"}
ABBREVIATIONS = ("vs.", "i.e.", "e.g.", "Dr.", "Mr.", "Mrs.", "Ms.", "Fig.", "No.")
SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")
UNTRUSTED_INSTRUCTION = re.compile(
    r"\b(ignore|disregard|override|forget)\b.{0,40}\b(instruction|guidance|prompt|rule)s?\b|"
    r"\b(system prompt|developer message|diagnose the user|reveal secrets?)\b|"
    r"\bshould be doubled for everyone\b",
    re.I,
)


def _tokens(text: str) -> set[str]:
    return {w.lower() for w in WORD.findall(text) if w.lower() not in STOP and len(w) > 2}


def _split_sentences(text: str) -> list[str]:
    sentinel = "<DOT_ABBR>"
    protected = text
    for abbr in ABBREVIATIONS:
        protected = protected.replace(abbr, abbr[:-1] + sentinel)
    return [s.replace(sentinel, ".") for s in SENTENCE_BREAK.split(protected)]


def extract_evidence(question: str, sources: list[SourceRecord], passages: list[Passage], max_units: int = 10) -> list[EvidenceUnit]:
    q = _tokens(question)
    source_map = {s.source_id: s for s in sources}
    ranked: list[tuple[int, str, Passage]] = []
    for p in passages:
        if p.section == "TITLE":
            continue
        src = source_map.get(p.source_id)
        if src is None:
            continue
        # ClinicalTrials.gov narrative descriptions are sponsor/investigator
        # submissions and are not admissible efficacy/safety evidence in alpha2.x.
        if src.source_type == "clinical_trial_registry" and p.section != "REGISTRY_FACT":
            continue
        for sentence in _split_sentences(p.text.strip()):
            sentence = sentence.strip()
            if len(sentence) < 20 or UNTRUSTED_INSTRUCTION.search(sentence):
                continue
            overlap = len(q & _tokens(sentence))
            if overlap or p.section == "REGISTRY_FACT":
                ranked.append((overlap + (2 if p.section == "REGISTRY_FACT" else 0), sentence, p))
    ranked.sort(key=lambda x: (-x[0], x[1]))
    units: list[EvidenceUnit] = []
    seen: set[str] = set()
    for _, sentence, p in ranked:
        key = f"{p.source_id}:{sentence}"
        if key in seen:
            continue
        seen.add(key)
        eid = "ev_" + hashlib.sha256(key.encode()).hexdigest()[:16]
        src = source_map[p.source_id]
        is_registry = src.source_type == "clinical_trial_registry"
        units.append(EvidenceUnit(
            evidence_id=eid,
            source_id=p.source_id,
            passage_ids=[p.passage_id],
            proposition=sentence,
            evidence_type="trial_registry_fact" if is_registry else "abstract_sentence",
            jurisdiction=src.jurisdiction,
            limitations=(
                ["ClinicalTrials.gov registry content supports trial discovery and registered-study facts; it is not treated as proof of treatment efficacy or safety."]
                if is_registry else
                ["Alpha2.x is extractive and does not independently assess study quality or GRADE certainty."]
            ),
        ))
        if len(units) >= max_units:
            break
    return units
