#!/usr/bin/env python3
"""Build and verify the selected real-exposition lineage field fixture.

This utility reads the declared source lineage database through a read-only
SQLite connection and copies only one selected closure into a fresh database
created by Ladon's existing schema builder. It is local field evidence, not a
product snapshot or freshness check.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
FIELD = Path(__file__).resolve().parent
OUTPUT_DB = FIELD / "selected-lineage.sqlite"
REPORT = FIELD / "field-report.json"
LINEAGE_INPUTS = ROOT / ".codex/state/dossier-r46/real-lineage-inputs.json"
ASSEMBLED = Path(
    "/home/codex/projects/lean/matrix-factorization/latex/lean/"
    "poisson_fixed_epoch_exposition_evidence_r02/target-capture-r44/assembled"
)
MANIFEST = ASSEMBLED / "note.canonical.result.json"
RESOLUTIONS = ASSEMBLED / "manifest-resolve.stdout"
GUIDE = ROOT / "openspec/changes/ladon-proof-reading-guides/evidence/guide-r47/field/guide.json"
SOURCE_DB = Path(
    "/home/codex/projects/lean/matrix-factorization/.ladon/index/"
    "fixed-epoch-field-u4t2qh3h.sqlite"
)
CLOSURE_ID = "cca9fd8a42d4e39267003768ff4650f1abc86fa20addebfdc92e1bf910cc2f12"
TARGET_ID = "uniform-total"
THEOREM = "Mf.DP.poissonFixedEpochTotalAverageVariance_fullBatch_lt_allEnergy_of_epochUniformSignal"
TABLES = (
    "lineage_closures",
    "lineage_nodes",
    "lineage_edges",
    "lineage_trust",
    "lineage_scc_members",
    "lineage_omissions",
)
METADATA_KEYS = (
    "maxIndexBytes",
    "completeDatabaseMaxBytes",
    "completeDatabaseBudgetPolicy",
)
INPUTS = (LINEAGE_INPUTS, MANIFEST, RESOLUTIONS, GUIDE, SOURCE_DB)
MAX_OUTPUT_BYTES = 256 * 1024 * 1024


def digest_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return size, "sha256:" + digest.hexdigest()


def input_inventory() -> dict[str, dict[str, Any]]:
    paths = list(INPUTS)
    paths.extend(sorted((ASSEMBLED / "artifacts").glob("*.json")))
    result = {}
    for path in paths:
        size, digest = digest_file(path)
        result[str(path)] = {"bytes": size, "sha256": digest}
    return result


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def value_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def table_columns(connection: sqlite3.Connection, table: str) -> list[str]:
    return [str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")]


def primary_key_order(connection: sqlite3.Connection, table: str) -> str:
    ordered = sorted(
        ((int(row[5]), str(row[1])) for row in connection.execute(f"PRAGMA table_info({table})") if row[5]),
    )
    if not ordered:
        raise RuntimeError(f"selected table has no declared primary key: {table}")
    return ",".join(name for _, name in ordered)


def selected_rows(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for table in TABLES:
        where = " WHERE closure_id=?" if table != "lineage_closures" else " WHERE closure_id=?"
        result[table] = [
            dict(row)
            for row in connection.execute(
                f"SELECT * FROM {table}{where} ORDER BY {primary_key_order(connection, table)}",
                (CLOSURE_ID,),
            )
        ]
    result["metadata"] = [
        dict(row)
        for row in connection.execute(
            "SELECT key,value FROM metadata WHERE key IN (?,?,?) ORDER BY key", METADATA_KEYS
        )
    ]
    return result


def row_evidence(rows: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    evidence = {}
    for table, records in rows.items():
        encoded = [canonical_bytes(row) for row in records]
        aggregate = hashlib.sha256()
        for payload in encoded:
            aggregate.update(len(payload).to_bytes(8, "big"))
            aggregate.update(payload)
        evidence[table] = {
            "rows": len(records),
            "canonicalRowBytes": sum(map(len, encoded)),
            "rowsSha256": "sha256:" + aggregate.hexdigest(),
        }
    return evidence


def create_fixture(rows: dict[str, list[dict[str, Any]]]) -> None:
    if OUTPUT_DB.exists():
        existing = open_ro(OUTPUT_DB)
        try:
            existing.execute("BEGIN")
            if selected_rows(existing) != rows:
                raise RuntimeError(f"existing fixture differs from selected source rows: {OUTPUT_DB}")
        finally:
            existing.rollback()
            existing.close()
        return
    if OUTPUT_DB.with_name(OUTPUT_DB.name + "-wal").exists():
        raise RuntimeError(f"refusing to use an existing fixture WAL: {OUTPUT_DB}")
    sys.path.insert(0, str(ROOT / "src"))
    from ladon.proof_search_schema import create_proof_search_schema

    connection = sqlite3.connect(OUTPUT_DB)
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        create_proof_search_schema(connection)
        connection.execute("BEGIN")
        for table in TABLES:
            columns = table_columns(connection, table)
            placeholders = ",".join("?" for _ in columns)
            sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
            connection.executemany(sql, ([row[column] for column in columns] for row in rows[table]))
        connection.executemany(
            "INSERT INTO metadata(key,value) VALUES (?,?)",
            ((row["key"], row["value"]) for row in rows["metadata"]),
        )
        connection.commit()
    except BaseException:
        connection.rollback()
        connection.close()
        OUTPUT_DB.unlink(missing_ok=True)
        raise
    else:
        connection.close()


def open_ro(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def check_database(path: Path) -> dict[str, Any]:
    connection = open_ro(path)
    try:
        fk = [tuple(row) for row in connection.execute("PRAGMA foreign_key_check")]
        integrity = [str(row[0]) for row in connection.execute("PRAGMA integrity_check")]
        table_names = [
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        counts = {
            table: int(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
            for table in table_names
        }
        page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
        page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
        return {
            "foreignKeyViolations": fk,
            "integrityCheck": integrity,
            "tables": counts,
            "pageSize": page_size,
            "pageCount": page_count,
            "allocatedBytes": page_size * page_count,
        }
    finally:
        connection.close()


def strip_elapsed(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: strip_elapsed(item) for key, item in value.items() if key != "elapsedSeconds"}
    if isinstance(value, list):
        return [strip_elapsed(item) for item in value]
    return value


def differences(left: Any, right: Any, prefix: str = "") -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            result.append({"path": prefix or "/", "source": sorted(left), "fixture": sorted(right), "kind": "keys"})
        for key in sorted(left.keys() & right.keys()):
            result.extend(differences(left[key], right[key], f"{prefix}/{key}"))
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            result.append({"path": prefix, "sourceLength": len(left), "fixtureLength": len(right), "kind": "length"})
        for index, (a, b) in enumerate(zip(left, right)):
            result.extend(differences(a, b, f"{prefix}/{index}"))
    elif left != right:
        result.append({"path": prefix, "source": left, "fixture": right, "kind": "value"})
    return result


def replace_source_path(value: Any, source_path: str, fixture_path: str) -> Any:
    if isinstance(value, str):
        return fixture_path if value == source_path else value
    if isinstance(value, dict):
        return {key: replace_source_path(item, source_path, fixture_path) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_source_path(item, source_path, fixture_path) for item in value]
    return value


def replace_exact_value(value: Any, old: str, new: str) -> Any:
    if isinstance(value, str):
        return new if value == old else value
    if isinstance(value, dict):
        return {key: replace_exact_value(item, old, new) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_exact_value(item, old, new) for item in value]
    return value


def replace_storage_diagnostics(value: Any, fixture_storage: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        result = {key: replace_storage_diagnostics(item, fixture_storage) for key, item in value.items()}
        storage = result.get("storage")
        if isinstance(storage, dict):
            for key in ("pageCount", "allocatedBytes"):
                storage[key] = fixture_storage[key]
        return result
    if isinstance(value, list):
        return [replace_storage_diagnostics(item, fixture_storage) for item in value]
    return value


def allowed_projection_differences(items: list[dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:
    allowed = []
    unexpected = []
    for item in items:
        path = item["path"]
        if path.endswith("/database") or path.endswith("/revision") or path.endswith("/selectionRevision"):
            item["reason"] = "database-path-derived-reference"
            allowed.append(item)
        elif path.endswith("/storage/pageCount") or path.endswith("/storage/allocatedBytes"):
            item["reason"] = "truthful-fixture-physical-storage-diagnostic"
            allowed.append(item)
        else:
            unexpected.append(item)
    return not unexpected, allowed + unexpected


def projections(source_path: Path, fixture_path: Path, lineage_inputs: dict[str, Any], manifest: dict[str, Any], resolutions: dict[str, Any]) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "src"))
    from ladon.result_lineage import lineage_sections
    from ladon.result_lineage_store import read_lineage_selection
    from ladon.result_inspection_page import inspection_digest
    from ladon.theorem_lineage_store import LineageIdentity, inspect_lineage_closure
    from ladon.theorem_lineage_summary import summarize_lineage

    entry = next(row for row in lineage_inputs["entries"] if row["targetId"] == TARGET_ID)
    fixture_entry = {**entry, "database": str(fixture_path)}
    identity = LineageIdentity(**entry["identity"])

    def owner(path: Path) -> dict[str, Any]:
        connection = open_ro(path)
        try:
            connection.execute("BEGIN")
            status = inspect_lineage_closure(connection, THEOREM, identity)
            summary = summarize_lineage(connection, identity, THEOREM)
            connection.rollback()
            return {"inspection": status, "summary": strip_elapsed(summary)}
        finally:
            connection.close()

    source_owner = owner(source_path)
    fixture_owner = owner(fixture_path)
    owner_diffs = differences(source_owner["inspection"], fixture_owner["inspection"], "/owner")
    summary_diffs = differences(source_owner["summary"], fixture_owner["summary"], "/summary")
    ok_summary, summary_diff_rows = allowed_projection_differences(summary_diffs)

    source_selected = read_lineage_selection(entry, THEOREM, Path("/"))
    fixture_selected = read_lineage_selection(fixture_entry, THEOREM, Path("/"))
    selected_diffs = differences(strip_elapsed(source_selected), strip_elapsed(fixture_selected), "/selectedClosure")
    selected_ok, selected_diff_rows = allowed_projection_differences(selected_diffs)
    source_path_substituted = replace_source_path(source_selected, str(source_path), str(fixture_path))
    selected_after_path_diffs = differences(strip_elapsed(source_path_substituted), strip_elapsed(fixture_selected), "/selectedClosureAfterPathSubstitution")
    normalized_source_selected = replace_storage_diagnostics(source_path_substituted, fixture_selected["ownerSummary"]["storage"])
    expected_revision = inspection_digest({key: value for key, value in normalized_source_selected.items() if key != "revision"})
    normalized_source_selected["revision"] = expected_revision
    if expected_revision != fixture_selected["revision"]:
        raise RuntimeError("fixture selection revision is not derived from path plus truthful storage diagnostics")
    selected_rebased_diffs = differences(strip_elapsed(normalized_source_selected), strip_elapsed(fixture_selected), "/selectedClosureAfterPathAndStorageNormalization")
    selected_rebased_ok = not selected_rebased_diffs
    selected_rebased_diff_rows = selected_rebased_diffs

    resolution_map = {row["targetId"]: row for row in resolutions["targetResolutions"]}
    source_sections = lineage_sections(manifest, resolution_map, lineage_inputs, Path("/"))
    fixture_inputs = {**lineage_inputs, "entries": [fixture_entry]}
    fixture_sections = lineage_sections(manifest, resolution_map, fixture_inputs, Path("/"))
    result_diffs = differences(strip_elapsed(source_sections), strip_elapsed(fixture_sections), "/resultSections")
    result_ok, result_diff_rows = allowed_projection_differences(result_diffs)
    source_sections_path_substituted = replace_source_path(source_sections, str(source_path), str(fixture_path))
    source_entry_revision = inspection_digest(entry)
    fixture_entry_revision = inspection_digest(fixture_entry)
    source_sections_path_substituted = replace_exact_value(source_sections_path_substituted, source_entry_revision, fixture_entry_revision)
    source_sections_path_substituted = replace_exact_value(source_sections_path_substituted, source_selected["revision"], fixture_selected["revision"])
    result_rebased_diffs = differences(strip_elapsed(source_sections_path_substituted), strip_elapsed(fixture_sections), "/resultSectionsAfterPathSubstitution")
    normalized_source_sections = replace_storage_diagnostics(source_sections_path_substituted, fixture_selected["ownerSummary"]["storage"])
    result_normalized_diffs = differences(strip_elapsed(normalized_source_sections), strip_elapsed(fixture_sections), "/resultSectionsAfterPathAndStorageNormalization")
    result_rebased_ok = not result_normalized_diffs
    result_rebased_diff_rows = result_normalized_diffs

    if source_owner["inspection"].get("status") != "fresh" or fixture_owner["inspection"].get("status") != "fresh":
        raise RuntimeError("owner inspection did not retain fresh status")
    if not owner_diffs:
        pass
    else:
        raise RuntimeError(f"owner inspect_lineage_closure changed: {owner_diffs[:10]}")
    if not (ok_summary and selected_ok and selected_rebased_ok and result_ok and result_rebased_ok):
        unexpected = [row for row in summary_diff_rows + selected_diff_rows + selected_after_path_diffs + selected_rebased_diff_rows + result_diff_rows + result_rebased_diffs + result_rebased_diff_rows if "reason" not in row]
        raise RuntimeError(f"unexpected projection changes: {unexpected[:12]}")

    # Verify the selected-row byte and digest invariants through both databases.
    source_ro = open_ro(source_path)
    fixture_ro = open_ro(fixture_path)
    try:
        source_ro.execute("BEGIN")
        fixture_ro.execute("BEGIN")
        source_rows = selected_rows(source_ro)
        fixture_rows = selected_rows(fixture_ro)
        if source_rows != fixture_rows:
            raise RuntimeError("selected source and fixture rows differ")
        row_match = row_evidence(source_rows) == row_evidence(fixture_rows)
        source_ro.rollback()
        fixture_ro.rollback()
    finally:
        source_ro.close()
        fixture_ro.close()

    canonical_projection_digests = {
        "ownerInspectionSource": value_digest(source_owner["inspection"]),
        "ownerInspectionFixture": value_digest(fixture_owner["inspection"]),
        "ownerSummarySourceAfterStorageNormalization": value_digest(
            replace_storage_diagnostics(source_owner["summary"], fixture_owner["summary"]["storage"])
        ),
        "ownerSummaryFixture": value_digest(fixture_owner["summary"]),
        "legacySelectionSourceAfterPathAndStorageNormalization": value_digest(normalized_source_selected),
        "legacySelectionFixture": value_digest(fixture_selected),
        "resultSectionsSourceAfterPathAndStorageNormalization": value_digest(normalized_source_sections),
        "resultSectionsFixture": value_digest(fixture_sections),
    }
    for left, right in (
        ("ownerInspectionSource", "ownerInspectionFixture"),
        ("ownerSummarySourceAfterStorageNormalization", "ownerSummaryFixture"),
        ("legacySelectionSourceAfterPathAndStorageNormalization", "legacySelectionFixture"),
        ("resultSectionsSourceAfterPathAndStorageNormalization", "resultSectionsFixture"),
    ):
        if canonical_projection_digests[left] != canonical_projection_digests[right]:
            raise RuntimeError(f"normalized projection digest mismatch: {left} vs {right}")

    return {
        "ownerInspection": {
            "source": source_owner["inspection"],
            "fixture": fixture_owner["inspection"],
            "exactMatch": not owner_diffs,
        },
        "ownerSummary": {
            "source": source_owner["summary"],
            "fixture": fixture_owner["summary"],
            "allSemanticFieldsMatch": ok_summary,
            "differences": summary_diff_rows,
        },
        "legacySelectedClosure": {
            "source": source_selected,
            "fixture": fixture_selected,
            "matchAfterDatabasePathSubstitutionAndStorageAllowance": selected_rebased_ok,
            "sourceRevisionAfterPathAndStorageNormalization": expected_revision,
            "pathAndDerivedRevisionDifferences": [row for row in selected_diff_rows if row.get("reason") == "database-path-derived-reference"],
            "differences": selected_diff_rows,
            "storageAndDerivedRevisionDifferencesAfterPathSubstitution": selected_after_path_diffs,
            "remainingDifferencesAfterStorageNormalization": selected_rebased_diff_rows,
        },
        "resultLineageAndAssumptionSections": {
            "source": source_sections,
            "fixture": fixture_sections,
            "matchAfterDatabasePathSubstitutionAndStorageAllowance": result_rebased_ok,
            "pathAndDerivedRevisionDifferences": [row for row in result_diff_rows if row.get("reason") == "database-path-derived-reference"],
            "sourceEntryRevisionAfterPathSubstitution": fixture_entry_revision,
            "sourceSelectionRevisionAfterPathAndStorageNormalization": fixture_selected["revision"],
            "differences": result_diff_rows,
            "storageDifferencesAfterPathAndReferenceRevisionSubstitution": result_rebased_diffs,
            "remainingDifferencesAfterStorageNormalization": result_rebased_diff_rows,
        },
        "selectedRowsExact": row_match,
        "canonicalProjectionDigests": canonical_projection_digests,
    }


def main() -> None:
    if REPORT.exists():
        raise RuntimeError("field report already exists; refusing to overwrite")
    before = input_inventory()
    lineage_inputs = json.loads(LINEAGE_INPUTS.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    resolutions = json.loads(RESOLUTIONS.read_text(encoding="utf-8"))
    entry = next(row for row in lineage_inputs["entries"] if row["targetId"] == TARGET_ID)
    if Path(entry["database"]).resolve() != SOURCE_DB.resolve() or entry["closureId"] != CLOSURE_ID:
        raise RuntimeError("explicit lineage input no longer selects the assigned source closure")
    if manifest.get("revision") != lineage_inputs.get("manifestRevision"):
        raise RuntimeError("canonical manifest revision no longer matches the explicit selection")
    if next(row for row in manifest["targets"] if row["id"] == TARGET_ID)["revision"] != entry["targetRevision"]:
        raise RuntimeError("selected target revision no longer matches the explicit input")

    source = open_ro(SOURCE_DB)
    try:
        source.execute("BEGIN")
        selected = selected_rows(source)
        if len(selected["lineage_closures"]) != 1:
            raise RuntimeError("source selection did not resolve exactly one closure")
        if selected["lineage_closures"][0]["theorem_name"] != THEOREM:
            raise RuntimeError("selected source closure theorem disagrees with canonical target")
        create_fixture(selected)
        source.rollback()
    finally:
        source.close()

    source_evidence = row_evidence(selected)
    fixture_connection = open_ro(OUTPUT_DB)
    try:
        fixture_connection.execute("BEGIN")
        copied = selected_rows(fixture_connection)
        fixture_connection.rollback()
    finally:
        fixture_connection.close()
    if copied != selected:
        raise RuntimeError("fixture selected rows differ from the single-transaction source snapshot")
    if row_evidence(copied) != source_evidence:
        raise RuntimeError("canonical selected row bytes/digests changed during copy")

    projection_report = projections(SOURCE_DB, OUTPUT_DB, lineage_inputs, manifest, resolutions)
    fixture_checks = check_database(OUTPUT_DB)
    if fixture_checks["foreignKeyViolations"]:
        raise RuntimeError("foreign_key_check reported violations")
    if fixture_checks["integrityCheck"] != ["ok"]:
        raise RuntimeError("integrity_check did not return ok")
    fixture_bytes = OUTPUT_DB.stat().st_size
    if fixture_bytes > MAX_OUTPUT_BYTES:
        raise RuntimeError(f"fixture exceeds 256 MiB: {fixture_bytes}")
    after = input_inventory()
    if before != after:
        raise RuntimeError("one or more source input hashes changed during fixture creation")
    script_bytes, script_digest = digest_file(Path(__file__).resolve())
    report = {
        "schema": "ladon-result-bundle-r48-selected-lineage-field-fixture-v1",
        "preparationScript": {"path": str(Path(__file__).resolve()), "bytes": script_bytes, "sha256": script_digest},
        "authority": "selected producer-supplied lineage evidence; source freshness is not assessed",
        "selection": {
            "lineageInput": str(LINEAGE_INPUTS),
            "manifest": str(MANIFEST),
            "manifestRevision": manifest["revision"],
            "targetId": TARGET_ID,
            "targetRevision": entry["targetRevision"],
            "entryId": entry["id"],
            "closureId": CLOSURE_ID,
            "theorem": THEOREM,
            "sourceDatabase": str(SOURCE_DB),
            "fixtureDatabase": str(OUTPUT_DB),
            "transaction": "one read-only source transaction covers selected row reads",
        },
        "inputHashesBefore": before,
        "inputHashesAfter": after,
        "inputHashesUnchanged": before == after,
        "selectedRows": source_evidence,
        "sourceDatabase": {
            "bytes": SOURCE_DB.stat().st_size,
            "selectedTableRows": {table: len(selected[table]) for table in (*TABLES, "metadata")},
            "lineageSummaryStorage": projection_report["ownerSummary"]["source"]["storage"],
            "wholeCacheIntegrityScan": "not-run to avoid reading unrelated cache tables",
        },
        "fixtureDatabase": fixture_checks,
        "fixtureFileBytes": fixture_bytes,
        "fixtureLimitBytes": MAX_OUTPUT_BYTES,
        "projections": projection_report,
        "schemaBuilder": "src/ladon/proof_search_schema.py:create_proof_search_schema",
        "retainedDataTables": list(TABLES) + ["metadata"],
        "schemaOwnedFtsSupportRows": {
            "declaration_search_config": fixture_checks["tables"].get("declaration_search_config", 0),
            "declaration_search_data": fixture_checks["tables"].get("declaration_search_data", 0),
            "explanation": "FTS5 schema-created support rows from create_proof_search_schema; no source cache rows were copied.",
        },
        "limitations": [
            "Producer-selected source freshness is not assessed.",
            "This fixture is only a field transport fixture; it performs no Lean check or source verification.",
        ],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(REPORT),
        "fixture": str(OUTPUT_DB),
        "fixtureFileBytes": fixture_bytes,
        "retainedCounts": {name: count for name, count in fixture_checks["tables"].items() if count},
        "inputHashesUnchanged": before == after,
        "projectionChecks": {
            "ownerInspectionExact": projection_report["ownerInspection"]["exactMatch"],
            "ownerSummarySemanticMatch": projection_report["ownerSummary"]["allSemanticFieldsMatch"],
            "legacySelectedClosureMatch": projection_report["legacySelectedClosure"]["matchAfterDatabasePathSubstitutionAndStorageAllowance"],
            "resultSectionsMatch": projection_report["resultLineageAndAssumptionSections"]["matchAfterDatabasePathSubstitutionAndStorageAllowance"],
            "selectedRowsExact": projection_report["selectedRowsExact"],
        },
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
