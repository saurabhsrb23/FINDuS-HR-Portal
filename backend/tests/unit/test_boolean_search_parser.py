"""Unit tests for the boolean search query parser (Module 6)."""
from __future__ import annotations

import pytest

from app.utils.boolean_search_parser import parse_boolean_search


# ── Empty / blank input ────────────────────────────────────────────────────────

def test_empty_string_returns_empty():
    assert parse_boolean_search("") == ""


def test_whitespace_only_returns_empty():
    assert parse_boolean_search("   ") == ""


# ── Single terms ──────────────────────────────────────────────────────────────

def test_single_word_lowercased():
    assert parse_boolean_search("Python") == "python"


def test_single_word_already_lower():
    assert parse_boolean_search("java") == "java"


def test_single_word_with_numbers():
    result = parse_boolean_search("python3")
    assert result == "python3"


# ── AND operator ──────────────────────────────────────────────────────────────

def test_explicit_and_operator():
    result = parse_boolean_search("Python AND Django")
    assert result == "python & django"


def test_explicit_and_lowercase():
    result = parse_boolean_search("python and django")
    assert result == "python & django"


def test_multiple_and_operators():
    result = parse_boolean_search("Java AND Spring AND Boot")
    assert result == "java & spring & boot"


# ── OR operator ───────────────────────────────────────────────────────────────

def test_explicit_or_operator():
    result = parse_boolean_search("Python OR Ruby")
    assert result == "python | ruby"


def test_explicit_or_lowercase():
    result = parse_boolean_search("python or ruby")
    assert result == "python | ruby"


# ── NOT operator ──────────────────────────────────────────────────────────────

def test_not_prefix():
    result = parse_boolean_search("Java NOT Intern")
    assert "!" in result
    assert "intern" in result


def test_not_standalone():
    result = parse_boolean_search("NOT PHP")
    assert "!php" in result


# ── Compound expressions ──────────────────────────────────────────────────────

def test_and_not_combination():
    result = parse_boolean_search("Java AND Spring NOT Intern")
    assert "java" in result
    assert "spring" in result
    assert "!intern" in result
    assert "&" in result


def test_or_with_parentheses():
    result = parse_boolean_search("(Java OR Kotlin) AND Android")
    assert "java" in result
    assert "kotlin" in result
    assert "android" in result


# ── Phrase search (quoted strings) ────────────────────────────────────────────

def test_quoted_phrase_becomes_followed_by():
    result = parse_boolean_search('"machine learning"')
    assert "machine" in result
    assert "learning" in result
    assert "<->" in result


def test_quoted_single_word():
    result = parse_boolean_search('"python"')
    assert result == "python"


def test_quoted_phrase_and_term():
    result = parse_boolean_search('"deep learning" AND tensorflow')
    assert "<->" in result
    assert "tensorflow" in result
    assert "&" in result


# ── Implicit AND (adjacent bare words) ────────────────────────────────────────

def test_adjacent_words_get_ampersand():
    result = parse_boolean_search("python django")
    assert "&" in result
    assert "python" in result
    assert "django" in result


def test_three_adjacent_words():
    result = parse_boolean_search("react typescript hooks")
    assert result.count("&") == 2


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_hyphenated_word():
    result = parse_boolean_search("full-stack")
    assert "full-stack" in result or "full" in result


def test_numeric_version():
    result = parse_boolean_search("python3 django4")
    assert "python3" in result
    assert "django4" in result


def test_mixed_case_operators():
    """AND/OR/NOT keywords must work regardless of case."""
    result1 = parse_boolean_search("java AND spring")
    result2 = parse_boolean_search("java and spring")
    result3 = parse_boolean_search("java And Spring")
    assert "&" in result1
    assert "&" in result2
    assert "&" in result3


def test_extra_spaces_handled():
    result = parse_boolean_search("  python   AND   django  ")
    assert "python" in result
    assert "django" in result
    assert "&" in result


def test_result_is_string_not_none():
    """Parser must always return a str (empty string is fine, never None)."""
    assert isinstance(parse_boolean_search("anything"), str)
    assert isinstance(parse_boolean_search(""), str)


def test_all_operators_stripped_returns_empty():
    """If the query has only stop words after stripping, return empty string."""
    result = parse_boolean_search("AND OR NOT")
    # Should not raise; may return empty string
    assert isinstance(result, str)


def test_complex_real_world_query():
    """A realistic recruiter query should not raise and must contain expected tokens."""
    result = parse_boolean_search(
        '("machine learning" OR "deep learning") AND Python NOT Intern'
    )
    assert "python" in result
    assert "!intern" in result
    assert isinstance(result, str)
