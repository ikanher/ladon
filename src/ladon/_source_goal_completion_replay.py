"""Ordinary compiler source for a closed application and its axiom observation."""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from ladon.source_association_io import _MODULE, _AssociationError, _digest


def replay_source(frame: Mapping[str, Any], request: Mapping[str, Any]) -> tuple[bytes, dict[str, Any]]:
    imports = frame["directImports"]
    if not isinstance(imports, list) or any(not isinstance(name, str) or not _MODULE.fullmatch(name) for name in imports):
        raise _AssociationError("unavailable", "replay-imports", "completion helper imports are malformed")
    declaration = "ladonCompletion_" + request["requestId"]
    body = "import Lean\n" + "".join(f"import {name}\n" for name in imports if name != "Lean")
    body += f"\ndef {declaration} : {frame['closedTargetText']} :=\n{frame['closedProofText']}\n"
    expected = {
        "frame": "LADON_COMPLETION_REPLAY",
        "protocolVersion": "ladon-lean-source-completion-replay-v1",
        "requestId": request["requestId"], "captureId": request["captureId"],
        "termDigest": request["termDigest"], "sourceDigest": _digest(body.encode()),
        "declaration": declaration,
    }
    fields = [f"({json.dumps(key)}, Lean.toJson ({json.dumps(value)} : String))"
              for key, value in expected.items()]
    fields += [
        '("observedAxioms", Lean.toJson names)',
        '("coverage", Lean.toJson ("complete" : String))',
    ]
    observer = "\n-- LADON_COMPLETION_REPLAY_REQUEST " + json.dumps(expected, sort_keys=True) + f"""
run_cmd do
  let env ← Lean.getEnv
  unless (env.checked.get.find? `{declaration}).isSome do
    throwError "generated declaration unavailable to kernel axiom observation"
  let axioms ← Lean.collectAxioms `{declaration}
  let names := (axioms.map toString).qsort (fun a b => a < b)
  let value := Lean.Json.mkObj [{', '.join(fields)}]
  Lean.Elab.Command.liftIO <| IO.println ("LADON_COMPLETION_REPLAY " ++ Lean.Json.compress value)
"""
    return (body + observer).encode(), expected
