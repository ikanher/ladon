"""Operational normalization and progress evidence for the scale gate."""

from __future__ import annotations

import json
from typing import Any, Mapping

from ladon.large_inventory_models import CacheEvidence


VOLATILE_CACHE_COUNTER_KEYS = frozenset(
    {
        "lean_cache_bypassed",
        "lean_cache_hits",
        "lean_cache_misses",
        "source_cache_hits",
        "source_cache_rebuilt",
    }
)
VOLATILE_EXACT_PATHS = frozenset(
    {
        ("metadata", "generated_at_utc"),
        ("sections", "discover", "cache"),
        ("sections", "lean_extraction", "cache"),
        ("sections", "lean_extraction", "helperElapsedSeconds"),
        ("sections", "module_dag", "helperElapsedSeconds"),
        ("sections", "module_dag", "source_index", "cache"),
        (
            "sections",
            "module_dag",
            "run_resources",
            "observed",
            "observedWallSeconds",
        ),
        (
            "sections",
            "module_dag",
            "run_resources",
            "observed",
            "peakRssBytes",
        ),
        (
            "sections",
            "module_dag",
            "run_resources",
            "crossed",
            "observed",
        ),
    }
)


def progress_cache_evidence(stderr: str) -> CacheEvidence:
    """Extract source/cache counters from JSON progress lines on stderr."""

    counters: dict[str, int] = {}
    for line in stderr.splitlines():
        row = _json_mapping(line)
        raw_cache = row.get("cache") if row is not None else None
        if not isinstance(raw_cache, Mapping):
            continue
        for key, value in raw_cache.items():
            if isinstance(key, str) and isinstance(value, int) and value >= 0:
                counters[key] = counters.get(key, 0) + value
    return CacheEvidence(
        hit_count=_counter_total(counters, ("hit", "reused")),
        miss_count=_counter_total(counters, ("miss", "invalidation", "bypass")),
        rebuilt_count=_counter_total(counters, ("rebuilt", "build")),
        keys=tuple(sorted(counters)),
    )


def progress_phase_evidence(
    stderr: str,
) -> tuple[Mapping[str, Any], ...]:
    """Return the last observed progress state for each pipeline phase."""

    phases: dict[str, dict[str, Any]] = {}
    for line in stderr.splitlines():
        row = _json_mapping(line)
        if row is None or not isinstance(row.get("phase"), str):
            continue
        if row.get("event") not in {"start", "update", "finish"}:
            continue
        phase = str(row["phase"])
        phases[phase] = {
            "phase": phase,
            "event": row.get("event"),
            "status": row.get("status"),
            "elapsedSeconds": row.get("elapsedSeconds"),
            "completed": row.get("completed"),
            "total": row.get("total"),
        }
    return tuple(phases.values())


def _json_mapping(line: str) -> Mapping[str, Any] | None:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, Mapping) else None


def _counter_total(
    counters: Mapping[str, int],
    needles: tuple[str, ...],
) -> int:
    return sum(
        value
        for key, value in counters.items()
        if any(needle in key.lower() for needle in needles)
    )


def normalized_report_bytes(
    payload: Mapping[str, Any],
) -> tuple[bytes, tuple[str, ...]]:
    """Return canonical bytes after only registered operational normalization."""

    normalized_fields: list[str] = []
    normalized = _normalize_report_value(
        payload,
        path=(),
        normalized_fields=normalized_fields,
    )
    return (
        json.dumps(
            normalized,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
        tuple(sorted(normalized_fields)),
    )


def _normalize_report_value(
    value: Any,
    *,
    path: tuple[str, ...],
    normalized_fields: list[str],
) -> Any:
    if isinstance(value, list):
        return [
            _normalize_report_value(
                item,
                path=(*path, str(index)),
                normalized_fields=normalized_fields,
            )
            for index, item in enumerate(value)
        ]
    if not isinstance(value, Mapping):
        return value
    result: dict[str, Any] = {}
    for key in sorted(value):
        name = str(key)
        item_path = (*path, name)
        if _is_volatile_path(item_path):
            normalized_fields.append(_json_pointer(item_path))
            result[name] = _normalized_runtime_value(item_path)
        else:
            result[name] = _normalize_report_value(
                value[key],
                path=item_path,
                normalized_fields=normalized_fields,
            )
    return result


def _is_volatile_path(path: tuple[str, ...]) -> bool:
    return (
        path in VOLATILE_EXACT_PATHS
        or _is_elapsed_path(path)
        or _is_cache_counter_path(path)
    )


def _is_elapsed_path(path: tuple[str, ...]) -> bool:
    """Recognize registered phase-duration fields in v2 and v3 reports."""

    return (
        len(path) == 3
        and path[0] == "phases"
        and path[2] == "elapsed_seconds"
        or len(path) == 4
        and path[:2] == ("pipeline", "timings")
        and path[3] == "elapsed_seconds"
    )


def _is_cache_counter_path(path: tuple[str, ...]) -> bool:
    """Recognize operational source-cache counters in v2 and v3 reports."""

    return (
        len(path) == 4
        and path[0] == "phases"
        and path[2] == "counters"
        and path[3] in VOLATILE_CACHE_COUNTER_KEYS
        or len(path) == 5
        and path[:2] == ("pipeline", "timings")
        and path[3] == "counters"
        and path[4] in VOLATILE_CACHE_COUNTER_KEYS
    )


def _normalized_runtime_value(path: tuple[str, ...]) -> Any:
    if path == ("metadata", "generated_at_utc"):
        return None
    if path in {
        ("sections", "discover", "cache"),
        ("sections", "lean_extraction", "cache"),
        ("sections", "module_dag", "source_index", "cache"),
    }:
        return {"normalizedOperationalCacheEvidence": True}
    if (
        len(path) == 4
        and path[2] == "counters"
        or len(path) == 5
        and path[3] == "counters"
    ):
        return 0
    return 0.0


def _json_pointer(path: tuple[str, ...]) -> str:
    return "/" + "/".join(_pointer_token(token) for token in path)


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


__all__ = [
    "normalized_report_bytes",
    "progress_cache_evidence",
    "progress_phase_evidence",
]
