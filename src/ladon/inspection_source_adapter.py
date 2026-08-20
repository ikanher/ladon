"""Canonical source-index inspection adapters."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ladon.coverage import CollectionCoverage
from ladon.inspection_adapter_common import (
    additive_row,
    artifact_fingerprint,
    declaration_mapping,
    declaration_row,
    filter_link,
    id_link,
    line_anchor,
    make_row,
    mapping_rows,
    module_id,
    noun_authority,
    noun_population,
    optional_int,
    ordered_int,
    population,
    source_anchor,
    stable_id,
    string_list,
    text,
    unknown_coverage,
)
from ladon.inspection_live_binding import (
    LiveInspectionBindingError,
    live_source_index_options,
)
from ladon.inspection_models import (
    ArtifactIdentity,
    InspectionCompatibilityError,
    InspectionDataset,
    InspectionRow,
)
from ladon.source_index_cache import manifest_digest
from ladon.source_index_models import (
    SOURCE_INDEX_AUDITS_COVERAGE,
    SOURCE_INDEX_DECLARATIONS_COVERAGE,
    SOURCE_INDEX_FINGERPRINT_VERSION,
    SOURCE_INDEX_IMPORTS_COVERAGE,
    SOURCE_INDEX_MODULES_COVERAGE,
    SOURCE_INDEX_OPTIONS_COVERAGE,
    SOURCE_INDEX_PROOF_MECHANISMS_COVERAGE,
    SOURCE_INDEX_RESOURCES_COVERAGE,
    SOURCE_INDEX_SCHEMA,
    SourceIndex,
    SourceIndexError,
    source_index_collection_mapping,
)

SOURCE_INDEX_COLLECTION_KEYS: Mapping[str, tuple[str, ...]] = {
    "audits": ("auditCommands", "audits"),
    "options": ("optionRows", "optionCommands", "genericOptions"),
    "resources": ("resourceSettings", "resourceDirectives", "resources"),
    "proof-mechanisms": (
        "proofMechanisms",
        "proofMechanismOccurrences",
        "tacticOccurrences",
        "attributeOccurrences",
    ),
}
SOURCE_INDEX_CACHE_ENVELOPE_KEYS = frozenset(
    {"fingerprintManifest", "payload"}
)


def source_index_dataset(
    payload: Mapping[str, Any],
    noun: str,
    *,
    repo_root: Path | None,
) -> InspectionDataset:
    """Adapt one validated immutable source index."""

    selected = _canonical_source_index_payload(payload)
    index = _validated_source_index(selected)
    artifact = ArtifactIdentity(
        kind="source-index",
        schema=index.schema,
        fingerprint=artifact_fingerprint(selected),
        source_fingerprint=index.fingerprint,
        live_fingerprint=_live_source_fingerprint(index, repo_root),
    )
    entries = mapping_rows(selected.get("entries"))
    rows, available = _selected_rows(entries, noun, artifact)
    return InspectionDataset(
        noun=noun,
        artifact=artifact,
        coverage=_selected_coverage(index, noun, len(rows), available),
        rows=tuple(sorted(rows, key=lambda row: row.order_key)),
        unavailable_reason=_unavailable_reason(noun, index.schema, available),
    )


def _canonical_source_index_payload(
    raw: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Unwrap only Ladon's exact content-addressed cache entry shape."""

    if raw.get("schema") == SOURCE_INDEX_SCHEMA:
        return raw
    if frozenset(raw) != SOURCE_INDEX_CACHE_ENVELOPE_KEYS:
        return raw
    manifest = raw.get("fingerprintManifest")
    payload = raw.get("payload")
    if not isinstance(manifest, Mapping) or not isinstance(payload, Mapping):
        raise InspectionCompatibilityError(
            "source-index cache envelope is malformed"
        )
    if payload.get("fingerprintManifest") != manifest:
        raise InspectionCompatibilityError(
            "source-index cache envelope manifest does not match its payload"
        )
    fingerprint = payload.get("fingerprint")
    if (
        not isinstance(fingerprint, str)
        or manifest_digest(manifest) != fingerprint
    ):
        raise InspectionCompatibilityError(
            "source-index cache envelope fingerprint does not match its manifest"
        )
    return payload


def _validated_source_index(payload: Mapping[str, Any]) -> SourceIndex:
    if payload.get("schema") != SOURCE_INDEX_SCHEMA:
        raise InspectionCompatibilityError(
            f"unsupported source-index schema: {payload.get('schema', '<missing>')}"
        )
    fingerprint = payload.get("fingerprint")
    if not isinstance(fingerprint, str) or not fingerprint:
        raise InspectionCompatibilityError("source-index fingerprint is missing")
    manifest = payload.get("fingerprintManifest")
    if not isinstance(manifest, Mapping):
        raise InspectionCompatibilityError(
            "source-index fingerprint manifest is malformed"
        )
    if manifest_digest(manifest) != fingerprint:
        raise InspectionCompatibilityError(
            "source-index fingerprint does not match its manifest"
        )
    _validate_analyzer_identity(manifest)
    if manifest.get("options") != payload.get("options"):
        raise InspectionCompatibilityError(
            "source-index options do not match its configuration fingerprint"
        )
    try:
        return SourceIndex.from_payload(
            Path("."),
            payload,
            expected_fingerprint=fingerprint,
        )
    except SourceIndexError as exc:
        raise InspectionCompatibilityError(str(exc)) from exc


def _validate_analyzer_identity(manifest: Mapping[str, Any]) -> None:
    from ladon.source_index import SOURCE_INDEX_ALGORITHM_VERSION

    if manifest.get("fingerprintVersion") != SOURCE_INDEX_FINGERPRINT_VERSION:
        raise InspectionCompatibilityError(
            "source-index fingerprint version is incompatible with this analyzer"
        )
    if manifest.get("indexSchema") != SOURCE_INDEX_SCHEMA:
        raise InspectionCompatibilityError(
            "source-index manifest schema is incompatible with this analyzer"
        )
    if manifest.get("algorithmVersion") != SOURCE_INDEX_ALGORITHM_VERSION:
        raise InspectionCompatibilityError(
            "source-index algorithm identity is incompatible with this analyzer"
        )


def _live_source_fingerprint(
    index: SourceIndex,
    repo_root: Path | None,
) -> str | None:
    if repo_root is None:
        return None
    from ladon.source_index import build_source_index

    try:
        current_options = live_source_index_options(index.options, repo_root)
        if current_options != dict(index.options):
            raise InspectionCompatibilityError(
                "stale source-index artifact; live configuration fingerprint "
                "does not match"
            )
        current = build_source_index(
            repo_root,
            options=current_options,
            use_cache=False,
        ).index.fingerprint
    except InspectionCompatibilityError:
        raise
    except (LiveInspectionBindingError, OSError, SourceIndexError, ValueError) as exc:
        raise InspectionCompatibilityError(
            f"live source-index validation failed: {exc}"
        ) from exc
    if current != index.fingerprint:
        raise InspectionCompatibilityError(
            "stale source-index artifact; live source fingerprint does not match"
        )
    return current


def _selected_rows(
    entries: Sequence[Mapping[str, Any]],
    noun: str,
    artifact: ArtifactIdentity,
) -> tuple[list[InspectionRow], bool]:
    builders = {
        "modules": _module_rows,
        "declarations": _declaration_rows,
        "imports": _import_rows,
    }
    if noun in builders:
        return builders[noun](entries, artifact), True
    keys = SOURCE_INDEX_COLLECTION_KEYS.get(noun, ())
    available = _collection_is_present(entries, keys)
    return _additive_rows(entries, artifact, noun, keys), available


def _module_rows(
    entries: Sequence[Mapping[str, Any]],
    artifact: ArtifactIdentity,
) -> list[InspectionRow]:
    rows: list[InspectionRow] = []
    for index, entry in enumerate(entries):
        module = _required_module(entry)
        name = text(module.get("name"))
        identifier = module_id(module)
        path = text(module.get("path"))
        rows.append(
            make_row(
                artifact,
                noun="modules",
                identifier=identifier,
                canonical_ref=f"#/entries/{index}/module",
                population_name=population(
                    module,
                    "discovered_internal_modules",
                ),
                scope="source_index_inventory",
                authority="source_index_manifest",
                anchor=source_anchor(path, None),
                coverage_ref=SOURCE_INDEX_MODULES_COVERAGE,
                fields={
                    "module": name,
                    "path": path,
                    "tag": string_list(module.get("tags")),
                    "role": string_list(module.get("roles")),
                    "status": "indexed",
                },
                order_key=(name, identifier),
                related=(
                    filter_link(
                        "imports",
                        "module",
                        name,
                        "outgoing imports",
                    ),
                    filter_link(
                        "declarations",
                        "module",
                        name,
                        "contained declarations",
                    ),
                ),
            )
        )
    return rows


def _declaration_rows(
    entries: Sequence[Mapping[str, Any]],
    artifact: ArtifactIdentity,
) -> list[InspectionRow]:
    rows: list[InspectionRow] = []
    for entry_index, entry in enumerate(entries):
        module = _required_module(entry)
        for row_index, raw in enumerate(_module_declarations(module)):
            rows.append(
                declaration_row(
                    artifact,
                    declaration_mapping(raw),
                    module,
                    canonical_ref=(
                        f"#/entries/{entry_index}/module/"
                        f"declarationEvidence/{row_index}"
                    ),
                    coverage_ref=SOURCE_INDEX_DECLARATIONS_COVERAGE,
                    scope="source_index_inventory",
                )
            )
    return rows


def _module_declarations(module: Mapping[str, Any]) -> list[Any]:
    evidence = module.get("declarationEvidence")
    if isinstance(evidence, list):
        return evidence
    return [{"name": name} for name in string_list(module.get("declarations"))]


def _import_rows(
    entries: Sequence[Mapping[str, Any]],
    artifact: ArtifactIdentity,
) -> list[InspectionRow]:
    rows: list[InspectionRow] = []
    for entry_index, entry in enumerate(entries):
        module = _required_module(entry)
        for site_index, site in enumerate(_import_sites(module)):
            rows.append(
                _import_row(
                    artifact,
                    module,
                    site,
                    entry_index,
                    site_index,
                )
            )
    return rows


def _import_row(
    artifact: ArtifactIdentity,
    module: Mapping[str, Any],
    site: Mapping[str, Any],
    entry_index: int,
    site_index: int,
) -> InspectionRow:
    importer = text(module.get("name"))
    target = text(site.get("module"))
    path = text(module.get("path"))
    line = optional_int(site.get("line"))
    identifier = stable_id(
        "import",
        importer,
        target,
        path,
        str(line),
        str(site_index),
    )
    return make_row(
        artifact,
        noun="imports",
        identifier=identifier,
        canonical_ref=f"#/entries/{entry_index}/module/importSites/{site_index}",
        population_name="lexical_import_occurrences",
        scope="source_index_inventory",
        authority="lexical_text",
        anchor=line_anchor(path, line),
        coverage_ref=SOURCE_INDEX_IMPORTS_COVERAGE,
        fields={
            "module": importer,
            "target": target,
            "path": path,
            "boundary": "unclassified",
        },
        order_key=(
            importer,
            path,
            ordered_int(line),
            target,
            identifier,
        ),
        related=(id_link("modules", module_id(module), "source module"),),
        nonclaims=(
            ("Lexical import occurrence only; not a Lean name-resolution or "
            "build result."),
        ),
    )


def _import_sites(module: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw = module.get("importSites")
    if isinstance(raw, list) and raw:
        return mapping_rows(raw)
    return [{"module": value} for value in string_list(module.get("imports"))]


def _additive_rows(
    entries: Sequence[Mapping[str, Any]],
    artifact: ArtifactIdentity,
    noun: str,
    keys: Sequence[str],
) -> list[InspectionRow]:
    rows: list[InspectionRow] = []
    for entry_index, entry in enumerate(entries):
        module = _required_module(entry)
        for key in keys:
            rows.extend(
                _adapt_module_collection(
                    artifact,
                    noun,
                    module,
                    entry_index,
                    key,
                )
            )
    return rows


def _adapt_module_collection(
    artifact: ArtifactIdentity,
    noun: str,
    module: Mapping[str, Any],
    entry_index: int,
    key: str,
) -> list[InspectionRow]:
    return [
        additive_row(
            artifact,
            noun,
            _with_scope_context(raw, module),
            module,
            canonical_ref=(f"#/entries/{entry_index}/module/{key}/{row_index}"),
            coverage_ref=f"source_index.{noun.replace('-', '_')}",
            scope="source_index_inventory",
        )
        for row_index, raw in enumerate(_compact_collection_rows(module, key))
    ]


def _compact_collection_rows(
    module: Mapping[str, Any],
    key: str,
) -> list[Mapping[str, Any]]:
    raw = module.get(key)
    if not isinstance(raw, list):
        return []
    module_name = text(module.get("name"))
    path = text(module.get("path"))
    try:
        return [
            (
                dict(row)
                if isinstance(row, Mapping)
                else source_index_collection_mapping(
                    key,
                    row,
                    module=module_name,
                    path=path,
                )
            )
            for row in raw
        ]
    except SourceIndexError as exc:
        raise InspectionCompatibilityError(str(exc)) from exc


def _with_scope_context(
    row: Mapping[str, Any],
    module: Mapping[str, Any],
) -> Mapping[str, Any]:
    identifier = row.get("scopeContextId")
    if not isinstance(identifier, str) or not identifier:
        return row
    context = next(
        (
            value
            for value in _compact_collection_rows(
                module,
                "scopeContextRows",
            )
            if value.get("id") == identifier
        ),
        None,
    )
    return {**row, "scopeContext": context}


def _collection_is_present(
    entries: Sequence[Mapping[str, Any]],
    keys: Sequence[str],
) -> bool:
    return any(any(key in _required_module(entry) for key in keys) for entry in entries)


def _selected_coverage(
    index: SourceIndex,
    noun: str,
    visible: int,
    available: bool,
) -> dict[str, Any]:
    canonical_id = {
        "modules": SOURCE_INDEX_MODULES_COVERAGE,
        "declarations": SOURCE_INDEX_DECLARATIONS_COVERAGE,
        "imports": SOURCE_INDEX_IMPORTS_COVERAGE,
        "audits": SOURCE_INDEX_AUDITS_COVERAGE,
        "options": SOURCE_INDEX_OPTIONS_COVERAGE,
        "resources": SOURCE_INDEX_RESOURCES_COVERAGE,
        "proof-mechanisms": SOURCE_INDEX_PROOF_MECHANISMS_COVERAGE,
    }.get(noun)
    if canonical_id is not None:
        coverage = index.coverage_registry().require(canonical_id)
        if coverage.visible != visible:
            raise InspectionCompatibilityError(
                f"{canonical_id} coverage exposes {coverage.visible} rows but "
                f"inspection found {visible}"
            )
        return coverage.to_dict()
    identity = f"source_index.{noun.replace('-', '_')}"
    if available and index.index_status == "complete":
        return CollectionCoverage.exact(
            identity=identity,
            pointer="#/entries",
            visible=visible,
            total=visible,
            population=noun_population(noun),
            scope="source_index_inventory",
            authority=noun_authority(noun),
            source_fingerprint=index.fingerprint,
        ).to_dict()
    return _unknown_source_coverage(index, noun, visible, available)


def _unknown_source_coverage(
    index: SourceIndex,
    noun: str,
    visible: int,
    available: bool,
) -> dict[str, Any]:
    reason = (
        "source-index extraction is partial"
        if available
        else f"{noun} collection is absent from this source-index schema"
    )
    return unknown_coverage(
        identity=f"source_index.{noun.replace('-', '_')}",
        pointer="#/entries",
        visible=visible,
        population_name=noun_population(noun),
        scope="source_index_inventory",
        authority=noun_authority(noun),
        source_fingerprint=index.fingerprint,
        reason=reason,
        completeness="partial" if available else "unavailable",
    )


def _required_module(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    module = entry.get("module")
    if not isinstance(module, Mapping):
        raise InspectionCompatibilityError("source-index entry module is malformed")
    return module


def _unavailable_reason(
    noun: str,
    schema: str,
    available: bool,
) -> str | None:
    if available:
        return None
    return f"{noun} evidence is unavailable in source-index schema {schema}"


__all__ = ["source_index_dataset"]
