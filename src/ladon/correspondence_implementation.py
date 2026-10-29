"""Bind generated-goal checking to stable Ladon implementation bytes."""

import hashlib
from pathlib import Path

from ladon.proof_slice import digest


def implementation_digest():
    root = Path(__file__).parent
    selected = {
        "correspondence_check.py", "correspondence_evidence.py",
        "correspondence_implementation.py", "correspondence_interpretation.py",
        "proofir_correspondence.py", "proofir_correspondence_payloads.py",
        "correspondence_preparation.py", "correspondence_execution_accounting.py",
        "_proof_contract_goal_scratch.py",
        "correspondence_import_cache.py", "correspondence_archive.py", "correspondence_transport.py",
        "investigation_correspondence_inputs.py",
        "correspondence_maps.py", "proof_slice.py", "proof_slice_validation.py", "proof_slice_limits.py",
        "scoped_slice.py", "slice_application_validation.py", "_proof_slice_runtime.py",
        "_expr_graph_protocol.py", "process_supervisor.py", "semantic_lean_execution.py",
        "lean/ladon_proof_slice_helper.lean", "lean/ladon_scoped_slice_helper.lean",
        "lean/ladon_roundtrip_print.lean",
        "lean/ladon_expr_graph.lean", "lean/ladon_typed_subject_helper.lean",
    }
    for pattern in ("*source_goal*.py", "*process_supervisor*.py", "*source_association*.py",
                    "*lean_toolchain*.py", "lean/*source_goal*.lean"):
        selected.update(str(path.relative_to(root)) for path in root.glob(pattern))
    identities = {name: "sha256:" + hashlib.sha256((root / name).read_bytes()).hexdigest()
                  for name in sorted(selected)}
    return "sha256:" + digest(identities)
