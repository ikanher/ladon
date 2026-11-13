"""Experiment runner: one activated unit, sequential bounded commands."""
import dataclasses
import datetime
import json
import os
from pathlib import Path
import sys
import time


workspace = Path(__file__).resolve().parent
state = workspace / "outputs"
manifest = json.loads((workspace / "LAUNCH.json").read_text())
source_root = Path(manifest["ladonSourceRoot"]).resolve()
if Path(sys.executable).resolve() != Path(manifest["pythonExecutable"]).resolve():
    raise SystemExit("Wrong Python runtime; use the registered invocation")
sys.path.insert(0, str(source_root))
from ladon.process_supervisor import run_bounded_target_process

if sys.argv[1:] == ["--activate"]:
    if list(state.iterdir()):
        raise SystemExit("Activation refused: outputs must be empty")
    now = time.time()
    with (state / "SESSION.json").open("x") as stream:
        json.dump({"startUnix": now, "deadlineUnix": now + 1200,
                   "startedAtUtc": datetime.datetime.now(datetime.timezone.utc).isoformat()}, stream)
    print("Activated; inspect source now. Deadline is 20 minutes from activation.")
    raise SystemExit(0)

if len(sys.argv) < 3 or sys.argv[1] != "--":
    raise SystemExit("Usage: CHECK.py --activate | CHECK.py -- COMMAND [ARG ...]")
session = json.loads((state / "SESSION.json").read_text())
remaining = session["deadlineUnix"] - time.time()
if remaining <= 0:
    raise SystemExit("Deadline reached; preserve partial report and stop")
lock = state / "ACTIVE"
try:
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
except FileExistsError:
    raise SystemExit("Parallel command or stale lock refused; report incident")
os.close(descriptor)
try:
    requests = list(state.glob("command-*.request.json"))
    if any(not Path(str(p).replace(".request.json", ".result.json")).exists() for p in requests):
        raise SystemExit("Incomplete command receipt; stop and report incident")
    count = len(requests)
    if count >= 20:
        raise SystemExit("20 checking commands consumed; stop")
    prefix = state / f"command-{count + 1:02d}"
    command = sys.argv[2:]
    with Path(str(prefix) + ".request.json").open("x") as stream:
        json.dump({"argv": command, "submittedAtUnix": time.time()}, stream)
    environment = dict(os.environ)
    for name in ["LEAN_PATH", "LEAN_SRC_PATH", "LAKE_PACKAGES_DIR"]:
        environment.pop(name, None)
    environment["PYTHONPATH"] = manifest["ladonSourceRoot"]
    environment["PATH"] = manifest["toolchainBin"] + os.pathsep + environment.get("PATH", "")
    remaining = session["deadlineUnix"] - time.time()
    if remaining <= 0:
        Path(str(prefix) + ".result.json").write_text(json.dumps({"status": "deadline-before-execution"}))
        raise SystemExit("Deadline reached; stop")
    result = run_bounded_target_process(
        command, cwd=workspace / "project", env=environment,
        timeout_seconds=min(600, remaining), max_rss_bytes=12 * 1024**3,
        max_output_bytes=16 * 1024**2, observe_resources=True,
    )
    record = dataclasses.asdict(result)
    for key in ["stdout", "stderr"]:
        Path(str(prefix) + "." + key).write_text(record.pop(key))
    Path(str(prefix) + ".result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"receiptPrefix": str(prefix), "succeeded": result.succeeded,
                      "remainingSeconds": max(0, session["deadlineUnix"] - time.time())}))
    raise SystemExit(0 if result.succeeded else 1)
finally:
    lock.unlink()
