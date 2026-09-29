from __future__ import annotations

import re

TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9+\-/.]*")
STOP = {
    "what", "which", "who", "why", "how", "when", "where", "is", "are", "was", "were", "do", "does", "did",
    "the", "a", "an", "of", "for", "in", "on", "with", "about", "whether", "evidence", "show", "shows", "showing",
    "find", "list", "identify", "there", "any", "please", "tell", "me", "clinical", "trial", "trials", "study", "studies",
}


def normalize_search_query(question: str) -> str:
    tokens = [m.group(0) for m in TOKEN.finditer(question)]
    kept = [t for t in tokens if t.lower() not in STOP]
    # Fall back to original rather than silently producing an empty query.
    return " ".join(kept) if kept else question.strip()
