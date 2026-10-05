"""Fail-closed parser for a narrow rendered Lean type-mismatch diagnostic."""
from __future__ import annotations

import hashlib
import re
from typing import Any

_SCHEMA = "ladon-compiler-goal-query-v1"
_HEADER = re.compile(r"^(.+):(\d+):(\d+): error: Type mismatch\s*$")
_ANY_HEADER = re.compile(r"^.+:\d+:\d+: (?:error|warning|info): .+$")


def parse_compiler_goal_query(
    text: str, diagnostic_ordinal: int | None = None,
) -> dict[str, Any]:
    """Parse only Lean's plain `has type` / `but is expected` rendering."""
    if not isinstance(text, str):
        raise TypeError("compiler diagnostic text must be a string")
    if diagnostic_ordinal is not None and (
        type(diagnostic_ordinal) is not int or diagnostic_ordinal < 0
    ):
        raise ValueError("diagnostic ordinal must be a nonnegative integer")
    records, malformed = _read_records(text.splitlines())
    status, selected, diagnostic = _select(records, malformed, diagnostic_ordinal)
    return {
        "schema": _SCHEMA, "status": status,
        "inputDigest": "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "evidenceBasis": "caller-supplied-compiler-text", "recordCount": len(records),
        "selected": selected, "diagnostic": diagnostic,
    }


def _read_records(lines: list[str]) -> tuple[list[dict[str, Any]], bool]:
    records: list[dict[str, Any]] = []
    malformed = False
    index = 0
    while index < len(lines):
        header = _HEADER.fullmatch(lines[index])
        if header is None:
            index += 1
            continue
        end = index + 1
        while end < len(lines) and not _ANY_HEADER.fullmatch(lines[end]):
            end += 1
        block = lines[index + 1:end]
        parsed = _parse_block(block)
        if parsed is None:
            malformed = True
        else:
            records.append({
                "ordinal": len(records), "file": header.group(1),
                "line": int(header.group(2)), "column": int(header.group(3)),
                **parsed,
            })
        index = end
    return records, malformed


def _select(records, malformed, ordinal):
    if malformed:
        return "unsupported", None, {
            "code": "malformed-type-mismatch",
            "message": "a type-mismatch diagnostic did not match the supported rendered form",
        }
    if not records:
        return "unsupported", None, {
            "code": "unsupported-or-malformed-diagnostic",
            "message": "no supported complete type-mismatch record was found",
        }
    if ordinal is None and len(records) > 1:
        return "ambiguous", None, {
            "code": "diagnostic-ordinal-required",
            "message": "multiple type-mismatch records require an explicit ordinal",
        }
    if ordinal is not None and ordinal >= len(records):
        return "unsupported", None, {
            "code": "diagnostic-ordinal-range",
            "message": "diagnostic ordinal is outside the matched record list",
        }
    return "parsed", records[ordinal or 0], None


def _parse_block(lines: list[str]) -> dict[str, str] | None:
    try:
        has_type = lines.index("has type")
        expected = lines.index("but is expected to have type", has_type + 1)
    except ValueError:
        return None
    if has_type < 1 or expected <= has_type + 1:
        return None
    expression = _fragment(lines[:has_type])
    actual = _fragment(lines[has_type + 1:expected])
    expected_type = _fragment(lines[expected + 1:])
    if not expression or not actual or not expected_type:
        return None
    return {"expression": expression, "actualType": actual, "expectedType": expected_type}


def _fragment(lines: list[str]) -> str:
    if not lines or any(not line.startswith("  ") for line in lines):
        return ""
    return "\n".join(line[2:] for line in lines).strip()
