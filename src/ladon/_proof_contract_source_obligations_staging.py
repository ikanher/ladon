"""Fixed-root source staging and digest construction."""
from __future__ import annotations

import hashlib
import json
import time
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from pathlib import Path

from ladon.proof_slice import pinned_toolchain
from ladon.source_association_io import _read_regular

CONSTRUCTION_POLICY = "source-bound-nat-atom-v1/strict-prefix"
_SCOPE_CLOSURE = (
    "run_cmd do\n"
    "  let count := (← Lean.Elab.Command.getScopes).length - 1\n"
    "  for _ in List.range count do\n"
    "    let scope ← Lean.Elab.Command.getScope\n"
    "    if scope.header.isEmpty then\n"
    "      Lean.Elab.Command.elabCommand (← `(command| end))\n"
    "    else\n"
    "      Lean.Elab.Command.elabCommand (← `(command| end $(Lean.mkIdent (Lean.Name.mkSimple scope.header))))\n"
)


def _absence_guard(parent, indent):
    declaration = parent["selection"]["declaration"]
    module = parent["selection"]["module"]
    return (
        f"{indent}let env ← Lean.getEnv\n"
        f"{indent}if env.contains `{declaration} then throwError \"parent declaration imported\"\n"
        f"{indent}if env.header.moduleNames.contains `{module} then throwError \"original source module imported\"\n"
    )


def _stage_prefix_check(root, rel, prefix, parent, digest, deadline, created):
    anchor = "LadonContractPrefix_" + digest[:16]
    source = (b"import Lean\n" + prefix + (
        "\nrun_cmd do\n" + _absence_guard(parent, "  ")
        + f"theorem _root_.{anchor} : _root_.True := by trivial\n" + _SCOPE_CLOSURE
    ).encode())
    path = rel.parent / "prefix" / "Probe.lean"
    _check_stage_deadline(deadline)
    _safe_create_parent(root, (root / path).parent)
    _check_stage_deadline(deadline)
    _write_probe(root / path, source, created=created)
    return {"path": path.as_posix(), "declaration": anchor,
            "digest": "sha256:" + hashlib.sha256(source).hexdigest()}


def _stage_source(root, parent, provider, expected, request, deadline):
    _check_stage_deadline(deadline)
    _, prefix = _source_prefix(root, parent, provider)
    _check_stage_deadline(deadline)
    digest = _request_digest(request, parent, provider, expected, prefix)
    rel = Path(".ladon") / "contract-obligations" / digest / "Probe.lean"
    target = root / rel
    expression = (f"∀ (s : Nat) (x : Nat), {expected['leftOperator']} s "
        f"({expected['map']} x) ≤ {expected['constantName']} * "
        f"{expected['inputScale']} (s + {expected['offset']}) x")
    theorem = (f"\ntheorem ladonCandidate_{digest[:16]} : {expression} := by\n"
        "  run_tac\n"
        + _absence_guard(parent, "    ")
        +
        "    if (← Lean.Core.getMessageLog).hasErrors then throwError \"prior source errors\"\n"
        "  skip\n"
        + _SCOPE_CLOSURE)
    generated = b"import Lean\n" + prefix + theorem.encode("utf-8")
    context_before = pinned_toolchain(root).context_identity
    with _staging_transaction() as created:
        _check_stage_deadline(deadline)
        _safe_create_parent(root, target.parent)
        _check_stage_deadline(deadline)
        _write_probe(target, generated, created=created)
        guard = _stage_prefix_check(root, rel, prefix, parent, digest, deadline, created)
        _verify_context(root, parent, deadline, context_before)
    prefix_digest = hashlib.sha256(prefix).hexdigest()
    generated_digest = hashlib.sha256(generated).hexdigest()
    skip_start = generated.rfind(b"  skip\n")
    if skip_start < 0:
        raise ValueError("generated target lost its selected skip token")
    line = generated[:skip_start].count(b"\n") + 1
    column = 2  # start of `skip`, after preceding guards, before the no-op itself
    return digest, rel.as_posix(), line, column, prefix_digest, generated_digest, generated, guard


def _source_prefix(root, parent, provider):
    raw = _read_regular(root / parent["source"]["path"], 8 * 1024**2)
    if hashlib.sha256(raw).hexdigest() != parent["source"]["sha256"]:
        raise ValueError("parent source bytes changed after observation")
    lines = raw.decode("utf-8").splitlines(keepends=True)
    location = parent["observation"]["declarationRange"]
    start = location["startLine"]
    if (provider["observation"]["declarationRange"]["endLine"] >= start
            or parent["selection"]["module"] != provider["selection"]["module"]):
        raise ValueError("provider is not inside the exact parent source prefix")
    prefix_text = "".join(lines[:start-1]) + lines[start-1][:location["startColumn"]]
    return raw, prefix_text.encode("utf-8")


def _write_probe(target, generated, *, created=None):
    if len(generated) > 8 * 1024**2:
        raise ValueError("generated source exceeds output bound")
    if target.exists():
        _check_existing_probe(target, generated)
    if not target.exists():
        try:
            with target.open("xb") as stream:
                if created is not None:
                    created.append(target)
                stream.write(generated)
        except FileExistsError:
            _check_existing_probe(target, generated)


def _check_stage_deadline(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("shared absolute deadline expired before source staging")


@contextmanager
def _staging_transaction():
    created = []
    try:
        yield created
    except BaseException:
        # Only files exclusively created by this attempt belong to its rollback.
        for target in reversed(created):
            target.unlink(missing_ok=True)
        raise


def _check_existing_probe(target, generated):
    if target.is_symlink() or _read_regular(target, len(generated)) != generated:
        raise ValueError("probe path collision")


def _verify_context(root, parent, deadline, before):
    if time.monotonic() >= deadline:
        raise TimeoutError("shared absolute deadline expired before context recheck")
    after = pinned_toolchain(root).context_identity
    if before != after or after != parent["environment"]:
        raise ValueError("staging changed source-tree or execution context identity")


def _safe_create_parent(root, target):
    base = root / ".ladon" / "contract-obligations"
    current = root
    for part in target.relative_to(root).parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError("probe path contains symlink")
    target.mkdir(parents=True, exist_ok=True)
    if not target.resolve().is_relative_to(base.resolve()):
        raise ValueError("probe path escapes fixed root")


def _request_digest(request, parent, provider, expected, prefix):
    body = {"constructionPolicy": CONSTRUCTION_POLICY,
        "request": _plain(request), "parentSnapshotId": parent["snapshotId"],
        "providerSnapshotId": provider["snapshotId"], "expectedSymbols": expected,
        "prefixDigest": hashlib.sha256(prefix).hexdigest()}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                  ensure_ascii=False).encode()).hexdigest()


def _plain(value):
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


