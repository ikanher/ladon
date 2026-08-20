"""Versioned lexical command-shape evidence from one canonical source mask.

The normalizer consumes the same comment/string-safe mask used by source
indexing.  It removes trivia, replaces numeric literals and numeric serial
fragments inside identifiers, and preserves all other visible identifiers and
delimiters.  The stored value is a digest of that normalized token stream, not
Lean syntax or proof evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator

from ladon.ir import LeanCommandSkeleton, LeanModule

COMMAND_SKELETON_VERSION = "command-skeleton-v1"
COMMAND_SKELETON_NONCLAIM = (
    "Lexical command-shape similarity only; not parsed Lean syntax, equal "
    "statements, equal proofs, tactic execution, proof success, or generated "
    "provenance."
)
_TOKEN_RE = re.compile(
    r"«[^»]*»"
    r"|(?:[^\W\d]|_)[\w']*[!?]?"
    r"|0[xX][0-9A-Fa-f_]+"
    r"|0[bB][01_]+"
    r"|0[oO][0-7_]+"
    r"|[0-9][0-9_]*(?:\.[0-9_]+)*(?:[eE][+-]?[0-9_]+)?"
    r"|[^\w\s()\[\]{},;\"'«»]+"
    r"|\S"
)
_NUMERIC_TOKEN_RE = re.compile(
    r"(?:"
    r"0[xX][0-9A-Fa-f_]+"
    r"|0[bB][01_]+"
    r"|0[oO][0-7_]+"
    r"|[0-9][0-9_]*(?:\.[0-9_]+)*(?:[eE][+-]?[0-9_]+)?"
    r")"
)
_SERIAL_FRAGMENT_RE = re.compile(r"[0-9₀-₉]+")


def scan_command_skeleton(
    masked: str,
    *,
    module: str,
    path: str,
) -> tuple[LeanCommandSkeleton, ...]:
    """Return one module-level skeleton when visible command tokens exist."""

    tokens = tuple(_normalized_tokens(masked))
    if not tokens:
        return ()
    encoded = json.dumps(
        {
            "version": COMMAND_SKELETON_VERSION,
            "tokens": tokens,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    value = f"sha256:{hashlib.sha256(encoded).hexdigest()}"
    identifier_payload = json.dumps(
        {
            "version": COMMAND_SKELETON_VERSION,
            "module": module,
            "path": path,
            "value": value,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    identifier = (
        f"ladon.command_skeleton.{hashlib.sha256(identifier_payload).hexdigest()[:24]}"
    )
    return (
        LeanCommandSkeleton(
            identifier=identifier,
            module=module,
            path=path,
            value=value,
            token_count=len(tokens),
            normalization_version=COMMAND_SKELETON_VERSION,
            nonclaim=COMMAND_SKELETON_NONCLAIM,
        ),
    )


def command_skeleton_evidence_complete(module: LeanModule) -> bool:
    """Return whether the current normalizer's module-level row is usable."""

    rows = module.command_skeletons
    return module.command_skeletons_complete and (
        not rows or (len(rows) == 1 and valid_command_skeleton_row(rows[0], module))
    )


def valid_command_skeleton_row(
    row: LeanCommandSkeleton,
    module: LeanModule,
) -> bool:
    """Validate one row against its canonical producer and module join."""

    value = row.value
    digest = value.removeprefix("sha256:")
    return (
        row.module == module.name
        and row.path == module.path
        and row.normalization_version == COMMAND_SKELETON_VERSION
        and row.status == "observed"
        and row.authority == "lexical_text"
        and row.token_count > 0
        and value.startswith("sha256:")
        and len(digest) == 64
        and all(character in "0123456789abcdef" for character in digest)
    )


def _normalized_tokens(masked: str) -> Iterator[str]:
    """Yield canonical tokens without retaining strings or numeric serials."""

    string_open = False
    char_open = False
    for match in _TOKEN_RE.finditer(masked):
        token = match.group(0)
        if token == '"':
            if not string_open:
                yield "<string>"
            string_open = not string_open
        elif token == "'":
            if not char_open:
                yield "<char>"
            char_open = not char_open
        elif _NUMERIC_TOKEN_RE.fullmatch(token):
            yield "<number>"
        elif token.startswith("«") or token[0].isalpha() or token[0] == "_":
            yield _SERIAL_FRAGMENT_RE.sub("<serial>", token)
        else:
            yield token


__all__ = [
    "COMMAND_SKELETON_NONCLAIM",
    "COMMAND_SKELETON_VERSION",
    "command_skeleton_evidence_complete",
    "scan_command_skeleton",
    "valid_command_skeleton_row",
]
