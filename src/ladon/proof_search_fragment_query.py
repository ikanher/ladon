"""Rank normalized fragment matches before bounding the SQLite result set."""
from __future__ import annotations

import re
import sqlite3
from functools import lru_cache

from ladon.proof_search_fragments import contains_tokens, tokenize_lean_text


def fragment_rows(connection: sqlite3.Connection, columns, clauses, values, request):
    # Store one bit per distinct query fragment. OR allows fragments in different
    # fields, while each bit requires a contiguous match inside a single field.
    needles = [tokenize_lean_text(fragment) for fragment in request.fragments]
    patterns = [re.compile(r"\s*".join(map(re.escape, needle))) for needle in needles]

    @lru_cache(maxsize=16)
    def field_mask(text):
        if not text:
            return 0
        possible = [i for i, pattern in enumerate(patterns) if pattern.search(text)]
        if not possible:
            return 0
        tokens = tokenize_lean_text(text)
        return sum(1 << i for i in possible if contains_tokens(tokens, needles[i]))

    # At least one eligible field must contain this token verbatim on every
    # full match. SQLite can reject unrelated rows before crossing into Python.
    anchor = max((token for needle in needles for token in needle), key=len)
    extracted = "(d.authority = 'lean_environment' AND d.type_status = 'lean-rendered')"
    prefilter = f"""(instr(d.type_text, ?) > 0 OR
        ({extracted} AND (instr(d.rendered_type, ?) > 0 OR instr(d.conclusion_text, ?) > 0)))"""
    where = " AND ".join([prefilter, *clauses])
    sql = f"""
        SELECT {columns}, {extracted} AND length(d.conclusion_text) > 0,
               ladon_fragment_mask(d.type_text) AS signature_hits,
               CASE WHEN {extracted} THEN ladon_fragment_mask(d.rendered_type) ELSE 0 END AS rendered_hits,
               CASE WHEN {extracted} THEN ladon_fragment_mask(d.conclusion_text) ELSE 0 END AS conclusion_hits
        FROM declarations d
        WHERE {where} AND (signature_hits | rendered_hits | conclusion_hits) = ?
        ORDER BY ladon_fragment_popcount(conclusion_hits) DESC,
                 d.type_status DESC, d.candidate_name, d.module, d.line, d.id LIMIT ?
    """
    connection.create_function("ladon_fragment_mask", 1, field_mask, deterministic=True)
    connection.create_function("ladon_fragment_popcount", 1, int.bit_count, deterministic=True)
    try:
        cap = request.limit + request.diagnostic_limit + 1
        return connection.execute(
            sql, (anchor, anchor, anchor, *values, (1 << len(needles)) - 1, cap)
        ).fetchall()
    finally:
        connection.create_function("ladon_fragment_mask", 1, None)
        connection.create_function("ladon_fragment_popcount", 1, None)


def fragment_evidence(row, fragments):
    available, signature, rendered, conclusion = row[14:18]
    masks = {"typeText": signature, "renderedType": rendered, "conclusionText": conclusion}
    evidence = [
        {"fragment": text, "fields": [name for name, mask in masks.items() if mask & (1 << i)]}
        for i, text in enumerate(fragments)
    ]
    return {
        "fragmentMatches": list(fragments),
        "fragmentEvidence": evidence,
        "fieldContributions": {field: bool(mask) for field, mask in masks.items()},
        "conclusionText": row[13] if available else None,
        "renderedType": row[12] if row[8] == "lean-rendered" else None,
        "conclusionAvailable": bool(available),
        "conclusionMatchCount": conclusion.bit_count(),
        "bucket": "normalized-fragment-match",
    }
