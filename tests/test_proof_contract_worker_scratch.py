"""Isolated no-Lean reproducer for killed route-worker goal scratch residue."""

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from ladon.lean_toolchain import (
    LeanToolchainError,
    resolve_toolchain_context,
    verify_toolchain_identities,
)
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_contract_obligation_supervision import _execute_job


def _repo(root):
    root.mkdir()
    (root / "lean-toolchain").write_text("leanprover/lean4:v4.32.1\n")
    source = root / "Source.lean"
    source.write_text("theorem original : True := True.intro\n")
    unrelated = root / ".ladon/correspondence/goal-preexisting/Existing.lean"
    unrelated.parent.mkdir(parents=True)
    unrelated.write_text("-- preexisting source material\n")
    concurrent = root / ".ladon/correspondence/goal-concurrent/Concurrent.lean"
    concurrent.parent.mkdir(parents=True)
    concurrent.write_text("-- preexisting concurrent job source\n")
    scripts = root.parent / "fake-toolchain"
    scripts.mkdir()
    lake = scripts / "lake"
    lake.write_text(
        f"#!{sys.executable}\nprint('Lake version 5.0.0 Lean version 4.32.1')\n"
    )
    lean = scripts / "lean"
    lean.write_text(f"#!{sys.executable}\nprint('Lean version 4.32.1')\n")
    lake.chmod(0o755)
    lean.chmod(0o755)
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    subprocess.run([
        "git", "-C", str(root), "add", "--", "lean-toolchain", "Source.lean",
        ".ladon/correspondence/goal-preexisting/Existing.lean",
        ".ladon/correspondence/goal-concurrent/Concurrent.lean",
    ], check=True)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    context = resolve_toolchain_context(
        root, lake_path=lake, lean_path=lean, environment=os.environ,
    )
    return root, source, unrelated, concurrent, lake, lean, source_hash, context


def _shim(path):
    path.mkdir()
    (path / "route_worker_bootstrap.py").write_text(r'''import json
import os
import time
from pathlib import Path
from types import SimpleNamespace

from ladon.process_supervisor import ProcessResult
from ladon.lean_toolchain import (
    LeanToolchainError, resolve_toolchain_context, verify_toolchain_identities,
)

def _fake_pinned(root):
    return resolve_toolchain_context(
        Path(root), lake_path=Path(os.environ["LADON_FAKE_LAKE"]),
        lean_path=Path(os.environ["LADON_FAKE_LEAN"]), environment=os.environ,
    )

import ladon.proof_contract_route_context_worker as route_worker
route_worker._verify_route_inputs = lambda root, binding: None

import ladon.proof_slice as proof_slice
proof_slice.pinned_toolchain = _fake_pinned

import ladon.correspondence_check as correspondence_check
correspondence_check.pinned_toolchain = _fake_pinned
correspondence_check.prepare_direct_lean_execution = lambda *args, **kwargs: SimpleNamespace(
    command=(os.environ["LADON_FAKE_LEAN"],), environment={},
)

def _fake_typing(command, **kwargs):
    generated = Path(command[-1])
    marker = Path(os.environ["LADON_MARKER"])
    if os.environ.get("LADON_FAKE_TYPING_MODE") == "fail":
        marker.write_text(json.dumps({
            "typingReached": generated.is_file(),
            "generatedPath": str(generated),
        }))
        return ProcessResult(tuple(command), 1, "", "synthetic typing failure", 0.0)
    frame = {"subject": {"structural": "synthetic-typed-subject"}}
    return ProcessResult(
        tuple(command), 0, "LADON_TYPED_SUBJECT " + json.dumps(frame) + "\n", "", 0.0,
    )

def _block_at_capture(request):
    root = Path(request.repo_root)
    generated = root / request.source_path
    before_tamper = generated.read_bytes()
    generated.write_bytes(before_tamper + b"\n-- live tamper control\n")
    try:
        verify_toolchain_identities(request.toolchain)
        tamper_rejected = False
    except LeanToolchainError as error:
        tamper_rejected = "source tree identity changed" in str(error)
    concurrent = root / ".ladon/correspondence/goal-concurrent/Concurrent.lean"
    concurrent.write_text("-- changed by concurrent source job\n")
    Path(os.environ["LADON_MARKER"]).write_text(json.dumps({
        "captureReached": True,
        "generatedPath": request.source_path,
        "generatedBytes": len(generated.read_bytes()),
        "pinnedSourceTreeIdentity": request.toolchain.source_tree_identity,
        "liveGoalTamperRejected": tamper_rejected,
        "concurrentPath": concurrent.relative_to(root).as_posix(),
    }))
    while True:
        time.sleep(1)

correspondence_check.run_bounded_target_process = _fake_typing
correspondence_check.capture_source_goal = _block_at_capture

raise SystemExit(route_worker.main())
''')


def _run_worker(root, shim, lake, lean, marker, *, typing_mode="success"):
    source = root / "Source.lean"
    request = {
        "repoRoot": str(root),
        "sourcePath": "Source.lean",
        "sourceDigest": "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest(),
        "goal": "True",
        "term": "True.intro",
        "symbols": {},
        "binding": {},
    }
    job = {"version": 1, "operation": "check-route-context-goal", "request": request}
    bounds = {
        "timeout_seconds": 2,
        "max_output_bytes": 8 * 1024**2,
        "max_rss_bytes": 12 * 1024**3,
        "deadlineMonotonic": time.monotonic() + 10,
    }
    state = {"receipt": None, "inputDigest": None, "bounds": None}

    def runner(command, **kwargs):
        assert command[-1] == "ladon.proof_contract_route_context_worker"
        environment = dict(kwargs["env"])
        environment.update({
            "PYTHONPATH": str(shim) + os.pathsep + environment["PYTHONPATH"],
            "LADON_FAKE_LAKE": str(lake),
            "LADON_FAKE_LEAN": str(lean),
            "LADON_MARKER": str(marker),
            "LADON_FAKE_TYPING_MODE": typing_mode,
        })
        return run_bounded_target_process(
            [sys.executable, "-m", "route_worker_bootstrap"],
            cwd=kwargs["cwd"], env=environment,
            timeout_seconds=kwargs["timeout_seconds"],
            max_output_bytes=kwargs["max_output_bytes"],
            max_rss_bytes=kwargs["max_rss_bytes"], input_bytes=kwargs["input_bytes"],
        )

    result = _execute_job(
        job, bounds, state, runner,
        worker_module="ladon.proof_contract_route_context_worker",
    )
    return result, state


def _reached_capture(marker, result, state, source, source_hash, context):
    assert marker.is_file(), (result["diagnostic"], state["receipt"])
    reached = json.loads(marker.read_text())
    assert reached["captureReached"] is True
    assert reached["liveGoalTamperRejected"] is True
    assert reached["pinnedSourceTreeIdentity"] != context.source_tree_identity
    assert result["status"] == "incomplete"
    assert result["diagnostic"]["code"] == "timeout"
    assert state["receipt"]["timedOut"] is True
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    return reached


def _owned_scratch_gone(root, reached, unrelated, concurrent):
    owned_file = root / reached["generatedPath"]
    assert not owned_file.exists(), f"timed-out worker left owned goal source {owned_file}"
    assert unrelated.is_file()
    assert concurrent.is_file()


def _same_context_resume_and_real_mutation(context, concurrent, source, source_hash):
    with pytest.raises(LeanToolchainError, match="source tree identity changed"):
        verify_toolchain_identities(context)
    concurrent.write_text("-- preexisting concurrent job source\n")
    verify_toolchain_identities(context)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    source.write_text(source.read_text() + "-- genuine source mutation\n")
    with pytest.raises(LeanToolchainError, match="source tree identity changed"):
        verify_toolchain_identities(context)


def test_timeout_after_real_goal_write_cleans_only_the_owned_goal_tree(tmp_path):
    root, source, unrelated, concurrent, lake, lean, source_hash, context = _repo(tmp_path / "repo")
    shim = tmp_path / "worker-shim"
    _shim(shim)
    marker = tmp_path / "worker-marker.json"
    result, state = _run_worker(root, shim, lake, lean, marker)
    reached = _reached_capture(marker, result, state, source, source_hash, context)
    _owned_scratch_gone(root, reached, unrelated, concurrent)
    _same_context_resume_and_real_mutation(context, concurrent, source, source_hash)


def test_ordinary_typing_failure_uses_normal_temporary_cleanup(tmp_path):
    root, _source, unrelated, concurrent, lake, lean, _source_hash, context = _repo(tmp_path / "repo")
    shim = tmp_path / "worker-shim"
    _shim(shim)
    marker = tmp_path / "worker-marker.json"

    result, _state = _run_worker(root, shim, lake, lean, marker, typing_mode="fail")

    observed = json.loads(marker.read_text())
    assert observed["typingReached"] is True
    assert not Path(observed["generatedPath"]).exists()
    assert result["status"] == "completed"
    assert result["result"]["status"] == "unresolved"
    assert unrelated.is_file() and concurrent.is_file()
    verify_toolchain_identities(context)
