"""Deterministic, source-compatible ProofIR-to-declaration attachments."""

from __future__ import annotations

import hashlib
import json
import sqlite3


def attach_surfaces(connection: sqlite3.Connection) -> dict[str, int]:
    candidates = selected = 0
    rows = connection.execute("SELECT surface_row_id,declaration_name,source_path,content_hash FROM proofir_surfaces ORDER BY surface_row_id").fetchall()
    for surface_id, name, path, content_hash in rows:
        admissible = _admissible_candidates(connection, name, path, content_hash)
        for declaration_id, method, confidence, freshness in admissible:
            candidate_id = hashlib.sha256(f"{surface_id}\x1f{declaration_id}".encode()).hexdigest()
            connection.execute("INSERT INTO proofir_attachment_candidates(candidate_id,surface_row_id,declaration_id,method,confidence,freshness,rejection_reason,details_json) VALUES(?,?,?,?,?,?,?,?)",
                (candidate_id, surface_id, declaration_id, method, confidence, freshness, None, "{}"))
            candidates += 1
        strongest = [row for row in admissible if row[2] == "highest"] or [row for row in admissible if row[2] == "high"]
        if len(strongest) == 1:
            declaration_id, method, confidence, freshness = strongest[0]
            connection.execute("INSERT INTO proofir_attachments(surface_row_id,declaration_id,method,confidence,freshness,details_json) VALUES(?,?,?,?,?,?)",
                (surface_id, declaration_id, method, confidence, freshness, json.dumps({"selection": "unique-strongest"})))
            selected += 1
    return {"attachmentCandidates": candidates, "attachments": selected}


def _admissible_candidates(connection: sqlite3.Connection, name: str, path: str, content_hash: str | None) -> list[tuple[str, str, str, str]]:
    declarations = connection.execute(
        "SELECT d.id,d.path,m.source_sha256 FROM declarations d JOIN modules m ON m.name=d.module WHERE d.name=? OR d.candidate_name=? ORDER BY d.id",
        (name, name),
    ).fetchall()
    return [candidate for row in declarations if (candidate := _candidate_for_row(row, path, content_hash)) is not None]


def _candidate_for_row(row: tuple[str, str, str], path: str, content_hash: str | None) -> tuple[str, str, str, str] | None:
    declaration_id, declaration_path, source_hash = row
    if content_hash and str(content_hash).removeprefix("sha256:") == str(source_hash):
        return declaration_id, "exact_path_name_source_hash", "highest", "fresh"
    if path and declaration_path != path:
        return None
    return declaration_id, "exact_path_name", "high", "stale" if content_hash else "unknown"
