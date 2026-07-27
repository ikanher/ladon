"""Public artifact selection boundary for ordinary Ladon inspection."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.inspection_models import (
    INSPECTION_NOUNS,
    InspectionCompatibilityError,
    InspectionDataset,
    InspectionInvocationError,
)
from ladon.inspection_report_adapter import report_dataset
from ladon.inspection_source_adapter import source_index_dataset


def load_inspection_dataset(
    path: Path,
    noun: str,
    *,
    artifact_kind: str,
    repo_root: Path | None = None,
) -> InspectionDataset:
    """Load exactly one artifact and adapt one registered canonical noun."""

    if noun not in INSPECTION_NOUNS:
        raise InspectionInvocationError(f"unsupported inspection noun: {noun}")
    payload = _load_json_object(path)
    if artifact_kind == "source-index":
        return source_index_dataset(payload, noun, repo_root=repo_root)
    if artifact_kind == "report":
        if repo_root is not None:
            raise InspectionInvocationError(
                "--repo-root live binding is supported only with --source-index"
            )
        return report_dataset(payload, noun)
    raise InspectionInvocationError(
        f"unsupported inspection artifact kind: {artifact_kind}"
    )


def _load_json_object(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        raise InspectionCompatibilityError(
            f"cannot load inspection artifact {path}: {exc}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise InspectionCompatibilityError(
            f"inspection artifact must contain one JSON object: {path}"
        )
    return payload


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate keys before any fingerprint is trusted."""

    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    """Reject non-standard NaN and infinity tokens."""

    raise ValueError(f"non-finite JSON constant: {value}")


__all__ = ["load_inspection_dataset"]
