import copy
import importlib.util
import json
import sys
from pathlib import Path

from ladon import __path__  # noqa: F401

base = Path(sys.argv[1])
for short in ("proofir_v3_batch", "proofir_v3", "proofir_v3_payloads"):
    name = "ladon." + short
    spec = importlib.util.spec_from_file_location(name, base / (short + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)

spec = importlib.util.spec_from_file_location("native_fixture", "tests/support/proofir_v3_native.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
v3 = sys.modules["ladon.proofir_v3"]

def record(label, operation):
    try:
        result = operation()
        if isinstance(result, tuple):
            content = [x.to_dict() for x in result]
            ids = [x.content_id for x in result]
        else:
            content, ids = result.to_dict(), [result.content_id]
        return {"case": label, "ok": True, "content": content, "ids": ids}
    except Exception as exc:
        diagnostic = getattr(exc, "diagnostic", None)
        return {"case": label, "ok": False, "type": type(exc).__name__, "message": str(exc), "diagnostic": repr(diagnostic)}

def reseal(a):
    a["artifactId"] = v3.detached_content_id(a)
    return a

cases = []
native = [fixtures.environment_artifact(), fixtures.claim_artifact(), fixtures.derivation_artifact(), fixtures.plan_artifact(), fixtures.attempt_log_artifact(), fixtures.check_run_artifact(), fixtures.source_map_artifact()]
for i, art in enumerate(native):
    cases.append(record(f"native-{i}", lambda art=art: v3.validate_envelope(art)))
    cases.append(record(f"batch-native-{i}", lambda art=art: v3.validate_envelope_batch([art, art])))

mutations = []
for i, art in enumerate(native):
    bad = copy.deepcopy(art); bad["artifactKind"] = "proofir.unknown"; mutations.append((f"unknown-kind-{i}", bad))
    bad = copy.deepcopy(art); bad["artifactId"] = "sha256:" + "0" * 64; mutations.append((f"bad-id-{i}", bad))
    bad = copy.deepcopy(art); bad["coverage"]["expected"] = True; mutations.append((f"bool-expected-{i}", bad))
for label, art in mutations:
    cases.append(record(label, lambda art=art: v3.validate_envelope(art)))

claim = fixtures.claim_artifact()
for label, transform in [
    ("surrogate", lambda x: x["extensions"]["example.fixture/v1"].update(note="\ud800")),
    ("float", lambda x: x["extensions"]["example.fixture/v1"].update(note=1.25)),
    ("unsafe-int", lambda x: x["extensions"]["example.fixture/v1"].update(note=9007199254740992)),
    ("extra-depth", lambda x: x["extensions"]["example.fixture/v1"].update(note=[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[0]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]])),
]:
    bad = copy.deepcopy(claim); transform(bad)
    cases.append(record(label, lambda bad=bad: v3.validate_envelope(bad)))

print(json.dumps(cases, ensure_ascii=True, sort_keys=True))
