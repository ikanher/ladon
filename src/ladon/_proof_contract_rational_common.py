"""Shared validation primitives for rational branch native artifacts."""

from __future__ import annotations

import hashlib
import json
import re

from ladon.proof_contract_payloads import closed, identifier

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def _validate_spans(spans):
    if type(spans) is not list or len(spans) > 64:
        raise ValueError("rational branch source-span identities are invalid")
    for span in spans:
        _validate_span(span)


def _validate_span(span):
    closed(
        span,
        {"constraintId", "path", "startLine", "endLine", "sha256", "quoteIdentity"},
        "rational branch source span",
    )
    identifier(span["constraintId"], "constraint ID")
    if (
        type(span["path"]) is not str
        or not span["path"]
        or len(span["path"].encode("utf-8")) > 4096
        or span["path"].startswith("/")
        or ".." in span["path"].split("/")
    ):
        raise ValueError("rational branch source path is invalid")
    if (
        type(span["startLine"]) is not int
        or type(span["endLine"]) is not int
        or span["startLine"] <= 0
        or span["endLine"] < span["startLine"]
    ):
        raise ValueError("rational branch source span lines are invalid")
    _require_digest(span["sha256"], "source digest")
    _require_digest(span["quoteIdentity"], "source quote identity")


def _validate_checker(identity):
    closed(identity, {"name", "schema"}, "rational checker identity")
    if (
        identity["name"] != "ladon.rational_witness.check_witness"
        or identity["schema"] != "ladon-rational-witness-v1"
    ):
        raise ValueError("unsupported rational checker identity")


def _goal_digest(goal, expected, label):
    if type(goal) is not dict or _digest(goal) != expected:
        raise ValueError(f"{label} digest does not match its contents")


def _require_digest(value, label):
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ValueError(f"{label} must be a SHA-256 digest")


def _digest(value):
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _text_digest(value):
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()
