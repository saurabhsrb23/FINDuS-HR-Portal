"""
Boolean search query parser.

Converts a user-friendly boolean search string into a PostgreSQL tsquery string.

Examples:
  "Python AND Django"            → "python & django"
  "Python OR Ruby"               → "python | ruby"
  "(Java AND Spring) NOT Intern" → "(java & spring) & !intern"
  '"machine learning"'           → "machine <-> learning"   (phrase search)
  "React"                        → "react"
  ""                             → ""  (empty string = no filter)
"""
from __future__ import annotations

import re


# Words that are boolean operators (not search terms)
_OPERATORS = {"AND", "OR", "NOT"}


def parse_boolean_search(query: str) -> str:
    """
    Convert a user boolean search string to a PostgreSQL tsquery expression.

    Returns an empty string when input is blank (caller should skip the
    ``search_vector @@ to_tsquery(...)`` clause entirely).
    """
    q = query.strip()
    if not q:
        return ""

    try:
        return _transform(q)
    except Exception:
        # Fall back to plain prefix search rather than crashing
        words = [w.lower() for w in re.split(r"\s+", q) if w and w not in _OPERATORS]
        return " & ".join(f"{w}:*" for w in words) if words else ""


# ── Internal helpers ──────────────────────────────────────────────────────────

def _transform(q: str) -> str:
    """Multi-pass transformation: phrase → operators → terms → cleanup."""

    # 1. Replace quoted phrases with a <-> (followed-by) chain
    def _phrase(m: re.Match) -> str:
        raw_words = m.group(1).strip().split()
        if not raw_words:
            return ""
        cleaned = [_clean_word(w) for w in raw_words if _clean_word(w)]
        if not cleaned:
            return ""
        if len(cleaned) == 1:
            return cleaned[0]
        return "(" + " <-> ".join(cleaned) + ")"

    q = re.sub(r'"([^"]*)"', _phrase, q)

    # 2. Map boolean keywords → tsquery operators
    #    Process NOT first (unary) before AND / OR (binary)
    #    "NOT foo"  → "!foo"   |   "foo NOT bar" → "foo & !bar"
    q = re.sub(r"\bNOT\b\s*", "!", q, flags=re.IGNORECASE)
    q = re.sub(r"\bAND\b", "&", q, flags=re.IGNORECASE)
    q = re.sub(r"\bOR\b", "|", q, flags=re.IGNORECASE)

    # 3. Lowercase all remaining bare words (non-operator tokens)
    def _lower_word(m: re.Match) -> str:
        w = m.group(0)
        return _clean_word(w)

    q = re.sub(r"[A-Za-z][A-Za-z0-9_\-]*", _lower_word, q)

    # 4. Collapse multiple spaces
    q = re.sub(r"\s{2,}", " ", q).strip()

    # 5. If two raw terms are adjacent with no operator between them, add &
    #    e.g. "python django" → "python & django"
    q = re.sub(r"(?<=[A-Za-z0-9_*)])\s+(?=[A-Za-z(!])", " & ", q)

    # 6. Tidy edge cases: "& !" → "& !", duplicate operators
    q = re.sub(r"[&|]\s*[&|]", "&", q)
    q = q.strip("&| ")

    return q if q else ""


def _clean_word(w: str) -> str:
    """Lowercase and strip non-alphanumeric characters from a bare word."""
    cleaned = re.sub(r"[^a-z0-9_\-]", "", w.lower())
    return cleaned
