"""Stable-identity collection closure for projected report evidence routes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from ladon.report_contract import copy_json
from ladon.report_stratification import (
    projection_stratum_key,
    stratifiable_rows,
)


_ROW_IDENTITY_FIELDS = (
    "id",
    "stable_key",
    "module",
    "path",
    "name",
)


@dataclass
class EvidenceClosure:
    """Mutable projected sections plus collections expanded for exact routes."""

    canonical: Mapping[str, Any]
    projected: dict[str, Any]
    changed: dict[str, tuple[Any, Any]]
    limit: int
    _slots: dict[int, dict[int, int]] = field(default_factory=dict)
    _stratified: dict[int, bool] = field(default_factory=dict)

    def can_rebase_all(self, references: list[str]) -> bool:
        """Check exact routes and per-stratum capacity before mutating output."""

        requirements: dict[tuple[int, tuple[str, ...] | None], set[int]] = {}
        lists: dict[int, list[Any]] = {}
        for reference in references:
            routed = _canonical_route_requirements(self.canonical, reference)
            if routed is None:
                return False
            for current, index in routed:
                identity = id(current)
                lists[identity] = current
                key = (identity, self._stratum(current, index))
                requirements.setdefault(key, set()).add(index)
        return all(
            self._requirements_fit(
                lists[identity],
                stratum=stratum,
                required=required,
            )
            for (identity, stratum), required in requirements.items()
        )

    def _requirements_fit(
        self,
        canonical: list[Any],
        *,
        stratum: tuple[str, ...] | None,
        required: set[int],
    ) -> bool:
        protected = {
            index
            for index in self._slots.get(id(canonical), {})
            if self._stratum(canonical, index) == stratum
        }
        capacity = min(
            self.limit,
            sum(
                self._stratum(canonical, index) == stratum
                for index in range(len(canonical))
            ),
        )
        return len(protected | required) <= capacity

    def rebase(self, reference: str) -> str | None:
        """Retain and return the exact projected target of one local reference."""

        tokens = local_pointer_tokens(reference)
        if tokens is None:
            return None if reference.startswith("#") else reference
        canonical_value: Any = self.canonical
        projected_value: Any = self.projected
        projected_tokens: list[str] = []
        for token in tokens:
            current_pointer = pointer(projected_tokens)
            advanced = self._advance(
                canonical_value,
                projected_value,
                token,
                current_pointer=current_pointer,
            )
            if advanced is None:
                return None
            canonical_value, projected_value, projected_token = advanced
            projected_tokens.append(projected_token)
        return pointer(projected_tokens)

    def _advance(
        self,
        canonical: Any,
        projected: Any,
        token: str,
        *,
        current_pointer: str,
    ) -> tuple[Any, Any, str] | None:
        if isinstance(canonical, Mapping):
            return self._advance_mapping(
                canonical,
                projected,
                token,
                current_pointer=current_pointer,
            )
        if isinstance(canonical, list):
            return self._advance_list(
                canonical,
                projected,
                token,
                current_pointer=current_pointer,
            )
        return None

    def _advance_mapping(
        self,
        canonical: Mapping[str, Any],
        projected: Any,
        token: str,
        *,
        current_pointer: str,
    ) -> tuple[Any, Any, str] | None:
        if token not in canonical or not isinstance(projected, dict):
            return None
        if token not in projected:
            projected[token] = _minimal_projection(
                canonical[token],
                limit=self.limit,
            )
            self.changed[current_pointer] = (canonical, projected)
            child_pointer = pointer([*local_pointer_tokens(current_pointer), token])
            self._track_nested_collections(
                canonical[token],
                projected[token],
                current_pointer=child_pointer,
            )
        return canonical[token], projected[token], token

    def _advance_list(
        self,
        canonical: list[Any],
        projected: Any,
        token: str,
        *,
        current_pointer: str,
    ) -> tuple[Any, Any, str] | None:
        if not isinstance(projected, list):
            return None
        index = _array_index(token)
        if index is None or index >= len(canonical):
            return None
        item = canonical[index]
        slots = self._slots.setdefault(id(canonical), {})
        projected_index = slots.get(index)
        if projected_index is None:
            projected_index = _matching_row_index(
                canonical,
                index,
                projected,
                excluded=set(slots.values()),
            )
        if projected_index is None:
            projected_index = self._replacement_index(
                canonical,
                index,
                projected,
                protected=set(slots.values()),
            )
            if projected_index is None:
                return None
            projected_item = _minimal_projection(item, limit=self.limit)
            if projected_index == len(projected):
                projected.append(projected_item)
            else:
                projected[projected_index] = projected_item
            self.changed[current_pointer] = (canonical, projected)
            self._track_nested_collections(
                item,
                projected_item,
                current_pointer=pointer(
                    [
                        *local_pointer_tokens(current_pointer),
                        str(projected_index),
                    ]
                ),
            )
        slots[index] = projected_index
        return item, projected[projected_index], str(projected_index)

    def _replacement_index(
        self,
        canonical: list[Any],
        index: int,
        projected: list[Any],
        *,
        protected: set[int],
    ) -> int | None:
        stratum = self._stratum(canonical, index)
        matching = [
            projected_index
            for projected_index, row in enumerate(projected)
            if self._projected_stratum(canonical, row) == stratum
        ]
        capacity = min(
            self.limit,
            sum(
                self._stratum(canonical, candidate) == stratum
                for candidate in range(len(canonical))
            ),
        )
        if len(matching) < capacity:
            return len(projected)
        return next(
            (candidate for candidate in matching if candidate not in protected),
            None,
        )

    def _stratum(
        self,
        canonical: list[Any],
        index: int,
    ) -> tuple[str, ...] | None:
        if not self._is_stratified(canonical):
            return None
        row = canonical[index]
        return projection_stratum_key(row) if isinstance(row, Mapping) else ()

    def _projected_stratum(
        self,
        canonical: list[Any],
        row: Any,
    ) -> tuple[str, ...] | None:
        if not self._is_stratified(canonical):
            return None
        return projection_stratum_key(row) if isinstance(row, Mapping) else ()

    def _is_stratified(self, canonical: list[Any]) -> bool:
        identity = id(canonical)
        if identity not in self._stratified:
            self._stratified[identity] = stratifiable_rows(canonical)
        return self._stratified[identity]

    def _track_nested_collections(
        self,
        canonical: Any,
        projected: Any,
        *,
        current_pointer: str,
    ) -> None:
        if isinstance(canonical, list) and isinstance(projected, list):
            self.changed[current_pointer] = (canonical, projected)
            return
        if not isinstance(canonical, Mapping) or not isinstance(projected, Mapping):
            return
        self.changed[current_pointer] = (canonical, projected)
        for key, canonical_child in canonical.items():
            projected_child = projected.get(key)
            if not isinstance(canonical_child, (list, Mapping)) or not isinstance(
                projected_child,
                (list, Mapping),
            ):
                continue
            self._track_nested_collections(
                canonical_child,
                projected_child,
                current_pointer=pointer(
                    [*local_pointer_tokens(current_pointer), str(key)]
                ),
            )


def local_pointer_tokens(reference: str) -> tuple[str, ...] | None:
    """Decode a report-section JSON pointer or identify an external reference."""

    prefix = "#/sections"
    if reference == prefix:
        return ()
    if not reference.startswith(f"{prefix}/"):
        return None
    try:
        return tuple(
            _pointer_untoken(part) for part in reference[len(prefix) + 1 :].split("/")
        )
    except ValueError:
        return None


def _canonical_route_requirements(
    canonical: Mapping[str, Any],
    reference: str,
) -> tuple[tuple[list[Any], int], ...] | None:
    tokens = local_pointer_tokens(reference)
    if tokens is None:
        return None if reference.startswith("#") else ()
    current: Any = canonical
    requirements: list[tuple[list[Any], int]] = []
    for token in tokens:
        if isinstance(current, Mapping):
            if token not in current:
                return None
            current = current[token]
            continue
        if not isinstance(current, list):
            return None
        index = _array_index(token)
        if index is None or index >= len(current):
            return None
        requirements.append((current, index))
        current = current[index]
    return tuple(requirements)


def pointer(tokens: list[str]) -> str:
    """Encode section-relative tokens as a local report JSON pointer."""

    suffix = "/".join(_pointer_token(token) for token in tokens)
    return f"#/sections/{suffix}" if suffix else "#/sections"


def _matching_row_index(
    canonical: list[Any],
    index: int,
    projected: list[Any],
    *,
    excluded: set[int],
) -> int | None:
    item = canonical[index]
    exact = _exact_match_index(item, projected, excluded=excluded)
    if exact is not None:
        return exact
    identity = _row_identity(item)
    if (
        identity is not None
        and sum(_row_identity(row) == identity for row in canonical) == 1
    ):
        identity_match = _identity_match_index(
            item,
            projected,
            identity=identity,
            excluded=excluded,
        )
        if identity_match is not None:
            return identity_match
    return None


def _identity_match_index(
    canonical: Any,
    projected: list[Any],
    *,
    identity: tuple[Any, ...],
    excluded: set[int],
) -> int | None:
    """Return one unambiguous stable-identity match."""

    matches = [
        index
        for index, row in enumerate(projected)
        if index not in excluded and _row_identity(row) == identity
    ]
    if len(matches) == 1:
        return matches[0]
    return _exact_match_index(
        canonical,
        projected,
        indexes=matches,
        excluded=excluded,
    )


def _exact_match_index(
    canonical: Any,
    projected: list[Any],
    *,
    indexes: list[int] | None = None,
    excluded: set[int],
) -> int | None:
    """Return one exact match from a complete or identity-filtered list."""

    candidates = indexes if indexes is not None else list(range(len(projected)))
    exact = [
        index
        for index in candidates
        if index not in excluded and projected[index] == canonical
    ]
    return exact[0] if exact else None


def _row_identity(value: Any) -> tuple[Any, ...] | None:
    if not isinstance(value, Mapping):
        return ("scalar", type(value).__name__, value)
    for key in _ROW_IDENTITY_FIELDS:
        item = value.get(key)
        if isinstance(item, str) and item:
            return key, item
    descriptors = tuple(
        (field, value[field])
        for field in ("type", "kind", "subject", "target", "declaration", "role")
        if isinstance(value.get(field), (str, int, bool))
    )
    return ("descriptor", *descriptors) if descriptors else None


def _minimal_projection(value: Any, *, limit: int) -> Any:
    """Retain scalar row identity without copying omitted nested populations."""

    if isinstance(value, list):
        if all(not isinstance(child, (list, Mapping)) for child in value):
            return copy_json(value[:limit])
        return []
    if not isinstance(value, Mapping):
        return copy_json(value)
    if _is_source_range(value):
        return copy_json(value)
    if value and all(isinstance(child, Mapping) for child in value.values()):
        return {}
    return {
        str(key): _minimal_projection(child, limit=limit)
        for key, child in value.items()
    }


def _is_source_range(value: Mapping[str, Any]) -> bool:
    """Recognize the exact two-coordinate record used by source anchors."""

    if set(value) != {"start", "end"}:
        return False
    return all(
        isinstance(coordinate, Mapping)
        and {"line", "column"}.issubset(coordinate)
        for coordinate in value.values()
    )


def _array_index(token: str) -> int | None:
    if token == "0":
        return 0
    if not token or token[0] == "0" or not token.isascii() or not token.isdecimal():
        return None
    return int(token)


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _pointer_untoken(value: str) -> str:
    decoded: list[str] = []
    index = 0
    while index < len(value):
        character = value[index]
        if character != "~":
            decoded.append(character)
            index += 1
            continue
        if index + 1 >= len(value) or value[index + 1] not in {"0", "1"}:
            raise ValueError("invalid JSON pointer escape")
        decoded.append("~" if value[index + 1] == "0" else "/")
        index += 2
    return "".join(decoded)


__all__ = ["EvidenceClosure", "local_pointer_tokens", "pointer"]
