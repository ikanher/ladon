"""Route-safe owner selection for audit and resource review signals."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ladon.report_projection_evidence_closure import EvidenceClosure
from ladon.report_projection_routes import (
    inspection_owner_pointers,
    inspection_region_noun,
    mapping_rows,
)
from ladon.report_stratification import (
    projection_stratum_key,
    stratified_selection,
)


def select_inspection_signals(
    regions: list[Any],
    *,
    canonical_by_id: Mapping[str, Mapping[str, Any]],
    canonical_owners: Mapping[str, Mapping[str, str]],
    canonical_sections: Mapping[str, Any],
    projected_sections: dict[str, Any],
    limit: int,
) -> tuple[
    dict[str, tuple[Mapping[str, Any], ...]],
    Mapping[str, tuple[Any, Any]],
]:
    """Prefer surviving owners, then restore bounded missing signal owners."""

    closure = EvidenceClosure(
        canonical=canonical_sections,
        projected=projected_sections,
        changed={},
        limit=limit,
    )
    selected: dict[str, tuple[Mapping[str, Any], ...]] = {}
    for region in regions:
        noun = inspection_region_noun(region)
        identity = region.get("id") if isinstance(region, Mapping) else None
        canonical = canonical_by_id.get(str(identity))
        if noun is None or canonical is None:
            continue
        signals = mapping_rows(canonical.get("signals"))
        owners = inspection_owner_pointers(closure.projected)[noun]
        retained = stratified_selection(
            [
                signal
                for signal in signals
                if _inspection_signal_target(signal, noun) in owners
            ],
            limit=limit,
            pointer="#/inspection-selection",
            strata=[],
        )
        protected = _protect_inspection_owners(
            retained,
            noun=noun,
            canonical_owners=canonical_owners[noun],
            closure=closure,
        )
        selected[str(identity)] = tuple(
            _fill_inspection_signal_strata(
                protected,
                signals,
                noun=noun,
                canonical_owners=canonical_owners[noun],
                closure=closure,
                limit=limit,
            )
        )
    return selected, closure.changed


def _protect_inspection_owners(
    signals: list[Mapping[str, Any]],
    *,
    noun: str,
    canonical_owners: Mapping[str, str],
    closure: EvidenceClosure,
) -> list[Mapping[str, Any]]:
    """Protect already projected owner slots before any substitution."""

    protected: list[Mapping[str, Any]] = []
    for signal in signals:
        target = _inspection_signal_target(signal, noun)
        pointer = canonical_owners.get(target) if target is not None else None
        if pointer is not None and closure.rebase(pointer) is not None:
            protected.append(signal)
    return protected


def _fill_inspection_signal_strata(
    selected: list[Mapping[str, Any]],
    canonical: list[Mapping[str, Any]],
    *,
    noun: str,
    canonical_owners: Mapping[str, str],
    closure: EvidenceClosure,
    limit: int,
) -> list[Mapping[str, Any]]:
    """Fill each signal stratum while respecting owner-collection capacity."""

    result = list(selected)
    selected_ids, counts = _inspection_signal_state(selected)
    ordered = stratified_selection(
        canonical,
        limit=max(1, len(canonical)),
        pointer="#/inspection-selection",
        strata=[],
    )
    for signal in ordered:
        identity = _inspection_signal_id(signal)
        key = projection_stratum_key(signal)
        if identity in selected_ids or counts.get(key, 0) >= limit:
            continue
        if not _retain_inspection_signal_owner(
            signal,
            noun=noun,
            canonical_owners=canonical_owners,
            closure=closure,
        ):
            continue
        result.append(signal)
        if identity is not None:
            selected_ids.add(identity)
        counts[key] = counts.get(key, 0) + 1
    return result


def _inspection_signal_state(
    selected: Sequence[Mapping[str, Any]],
) -> tuple[set[str], dict[tuple[str, ...], int]]:
    """Index selected identities and per-stratum occupancy."""

    identifiers = {
        identity
        for signal in selected
        if (identity := _inspection_signal_id(signal)) is not None
    }
    counts: dict[tuple[str, ...], int] = {}
    for signal in selected:
        key = projection_stratum_key(signal)
        counts[key] = counts.get(key, 0) + 1
    return identifiers, counts


def _retain_inspection_signal_owner(
    signal: Mapping[str, Any],
    *,
    noun: str,
    canonical_owners: Mapping[str, str],
    closure: EvidenceClosure,
) -> bool:
    """Substitute one exact owner only when its collection has capacity."""

    target = _inspection_signal_target(signal, noun)
    pointer = canonical_owners.get(target) if target is not None else None
    return bool(
        pointer is not None
        and closure.can_rebase_all([pointer])
        and closure.rebase(pointer) is not None
    )


def _inspection_signal_id(signal: Mapping[str, Any]) -> str | None:
    """Return one nonempty producer identity."""

    identity = signal.get("id")
    return identity if isinstance(identity, str) and identity else None


def _inspection_signal_target(
    signal: Mapping[str, Any],
    noun: str,
) -> str | None:
    """Read the exact stable-row target from one ordinary inspection action."""

    action = signal.get("inspectionAction")
    if not isinstance(action, Mapping) or action.get("command") != "ladon":
        return None
    arguments = action.get("arguments")
    if (
        not isinstance(arguments, list)
        or len(arguments) != 4
        or arguments[:3] != ["inspect", noun, "--id"]
        or not isinstance(arguments[3], str)
        or not arguments[3]
    ):
        return None
    return arguments[3]


__all__ = ["select_inspection_signals"]
