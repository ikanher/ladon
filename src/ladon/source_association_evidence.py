"""Source association evidence for exact source-to-compiled observations."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from ladon.process_supervisor import ProcessResult
from ladon.proofir_attachment_policy import POLICY_DIGEST, POLICY_VERSION
from ladon.proofir_v3 import (
    make_envelope,
)
from ladon.source_association_io import (
    _AssociationError,
    _digest,
    _strict_json,
)


def _resource_result(process: ProcessResult) -> dict[str, Any]:
    return {
        "elapsedMilliseconds": max(0, int(process.elapsed_seconds * 1000)),
        "peakRssBytes": process.peak_rss_bytes,
        "returnCode": process.returncode,
    }


def _bounded_status(process: ProcessResult) -> str | None:
    if process.timed_out:
        return "timeout"
    if process.memory_limited:
        return "memory-limited"
    if process.output_limited:
        return "output-limited"
    return None


def _anchor_from_ilean(raw: bytes, module: str, candidate: str, source: bytes,
                        source_path: str, owner: Mapping[str, Any], declaration: Mapping[str, Any]) -> dict[str, Any]:
    positions = _fresh_ilean_positions(raw, module, candidate)
    decoded = source.decode("utf-8")
    full_start, full_end = _full_range(decoded, positions)
    subject = {
        "artifactRef": owner["artifactId"],
        "kind": "declaration",
        "localId": declaration["localId"],
    }
    return {
        "subjectRef": subject,
        "sourcePath": source_path,
        "module": module,
        "declName": candidate,
        "declarationRef": declaration["localId"],
        "declarationFingerprint": declaration["fingerprint"]["digest"],
        "start": full_start,
        "end": full_end,
        "contentDigest": _digest(source),
        "matchMethod": "environment-fingerprint",
    }


def _fresh_ilean_positions(raw: bytes, module: str, candidate: str) -> list[int]:
    value = _strict_json(raw)
    _validate_ilean_metadata(value, module)
    positions = value["decls"].get(candidate)
    if not isinstance(positions, list) or len(positions) != 8 or any(type(item) is not int or item < 0 for item in positions):
        raise _AssociationError("unavailable", "ilean-declaration", "fresh .ilean has no unique valid declaration entry")
    return positions


def _validate_ilean_metadata(value: Any, module: str) -> None:
    fields = {"version", "module", "directImports", "references", "decls"}
    if not isinstance(value, dict):
        raise _AssociationError("stale", "ilean-identity", "fresh .ilean metadata is not an object")
    if set(value) != fields:
        raise _AssociationError("stale", "ilean-identity", "fresh .ilean metadata uses unsupported fields")
    if type(value["version"]) is not int or value["version"] != 5 or value["module"] != module:
        raise _AssociationError("stale", "ilean-identity", "fresh .ilean metadata has the wrong version or module")
    if not isinstance(value["directImports"], list) or not isinstance(value["references"], dict) or not isinstance(value["decls"], dict):
        raise _AssociationError("stale", "ilean-identity", "fresh .ilean metadata has the wrong version or module")


def _full_range(source: str, positions: list[int]) -> tuple[dict[str, int], dict[str, int]]:
    full_start = _utf16_position(source, positions[0], positions[1])
    full_end = _utf16_position(source, positions[2], positions[3])
    selection_start = _utf16_position(source, positions[4], positions[5])
    selection_end = _utf16_position(source, positions[6], positions[7])
    if not (
        full_start["byte"]
        <= selection_start["byte"]
        <= selection_end["byte"]
        <= full_end["byte"]
    ):
        raise _AssociationError("stale", "ilean-range", "fresh .ilean selection range is outside its declaration range")
    return full_start, full_end


def _utf16_position(source: str, line_number: int, character: int) -> dict[str, int]:
    lines = source.split("\n")
    if line_number >= len(lines):
        raise _AssociationError("stale", "ilean-range", "fresh .ilean line is outside source bytes")
    line_start = sum(len(line.encode("utf-8")) + 1 for line in lines[:line_number])
    line = lines[line_number].removesuffix("\r")
    units = 0
    prefix = ""
    for char in line:
        if units == character:
            break
        width = 2 if ord(char) > 0xFFFF else 1
        if units + width > character:
            raise _AssociationError("stale", "ilean-range", "fresh .ilean UTF-16 position splits a surrogate pair")
        units += width
        prefix += char
    if units != character:
        raise _AssociationError("stale", "ilean-range", "fresh .ilean character is outside source line")
    return {
        "byte": line_start + len(prefix.encode("utf-8")),
        "line": line_number + 1,
        "column": len(prefix) + 1,
    }


def _make_source_map(owner: Mapping[str, Any], declaration: Mapping[str, Any], module: str,
                     anchor: dict[str, Any], source_digest: str,
                     observation: Mapping[str, Any]) -> dict[str, Any]:
    anchor.update({"contentDigest": source_digest})
    source_map_id = "source-map:" + hashlib.sha256(
        (owner["artifactId"] + declaration["localId"] + source_digest).encode()
    ).hexdigest()
    return make_envelope(
        artifact_kind="proofir.source-map",
        producer={"name": "ladon-source-association", "version": "1", "implementation": "fresh-lean-compile-stdin"},
        environment_ref=owner["environmentRef"],
        subject_refs=[declaration],
        coverage={"status": "complete", "observed": 1},
        payload={
            "sourceMapId": source_map_id,
            "anchors": [anchor],
            "policy": {"version": POLICY_VERSION, "digest": POLICY_DIGEST},
        },
        limitations=[
            {
                "id": "source-association-limited-scope",
                "message": "Source association observes source-to-compiled coherence for the recorded module set; it does not establish full environment freshness.",
            },
            {
                "id": "checking-and-correspondence-not-assessed",
                "message": "Checking acceptance and informal result correspondence are not assessed by this source map.",
            },
        ],
        extensions={"ladon.source-association-observation/v1": dict(observation)},
    ).to_dict()


def _result(status: str, source: Mapping[str, Any], compiled: Mapping[str, Any],
            resources: Mapping[str, Any], artifacts: list[dict[str, Any]],
            code: str | None, message: str | None) -> dict[str, Any]:
    return {
        "schema": "ladon-source-association-v1",
            "operation": "source-compiled-coherence",
        "status": status,
        "artifacts": artifacts,
        "diagnostic": {"code": code, "message": message[:4096] if message else message} if code else None,
        "source": dict(source),
        "compiled": dict(compiled),
        "resources": dict(resources),
        "checking": "not-assessed",
        "correspondence": "not-assessed",
        "nonclaims": [
            "This observation does not establish complete environment freshness or caller authenticity.",
            "Source association is separate from checker acceptance and informal correspondence.",
        ],
    }

