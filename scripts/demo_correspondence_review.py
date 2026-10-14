#!/usr/bin/env python3
"""Exercise scoped providers and immutable v3 review using this checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


class PublicDemo:
    def __init__(self, output):
        self.checkout = Path(__file__).resolve().parents[1]
        self.output = output
        output.mkdir(parents=True, exist_ok=False)
        self.repo = output / "repo"
        shutil.copytree(self.checkout / "tests/fixtures/correspondence_m1", self.repo,
                        ignore=shutil.ignore_patterns(".ladon", "*.olean"))
        self.receipts = []
        self.env = {**os.environ, "PYTHONPATH": str(self.checkout / "src")}

    def write(self, name, value):
        path = self.output / name
        with path.open("x") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        return path

    def read(self, name):
        return json.loads((self.output / name).read_text())

    def invoke(self, *args, expected=0):
        command = [sys.executable, "-m", "ladon.entrypoint", *map(str, args)]
        started = time.monotonic()
        process = subprocess.run(command, cwd=self.checkout, env=self.env, capture_output=True,
                                 text=True, timeout=900, check=False)
        self.receipts.append({"command": command, "exitCode": process.returncode,
                              "elapsedSeconds": time.monotonic() - started,
                              "stdout": process.stdout, "stderr": process.stderr})
        (self.output / "commands.json").write_text(json.dumps(self.receipts, indent=2) + "\n")
        if process.returncode != expected:
            raise RuntimeError(process.stdout + process.stderr)
        print(args[0], args[1], "exit", process.returncode, flush=True)
        return json.loads(process.stdout) if process.stdout.strip() else None


def authored_record(repo):
    source = repo / "predecessor.txt"
    def positive(identity):
        return {"tag": "lt", "left": {"tag": "const", "name": "0"},
                "right": {"tag": "var", "id": identity}}
    formula = {"tag": "implies", "premise": positive("n"),
               "conclusion": {"tag": "and", "items": [positive("n"), positive("m")]}}
    for identity in ("m", "n"):
        formula = {"tag": "forall", "binder": {"id": identity, "name": identity,
                   "domain": "Nat"}, "body": formula}
    return {"id": "missing-second-provider", "source": {
        "path": source.name, "startLine": 1, "endLine": 1,
        "quote": source.read_text().strip(),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
        "formula": formula, "symbols": {}}


def check_argument(demo):
    out, repo = demo.output, demo.repo
    record = demo.write("record.json", authored_record(repo))
    mapping = demo.write("map.json", {"n": "n", "m": "m"})
    terms = demo.write("terms.json", [{"obligation": "premise-3", "mode": "refute", "term":
        "by intro h; have bad := h 1 0 (by decide); exact (Nat.lt_irrefl 0) bad"}])
    demo.invoke("proof-search", "proof", "slice", "--scoped", "--repo", repo,
                "--source", "Scoped.lean", "--module", "Scoped", "--declaration", "Scoped.chain",
                "--application", "Scoped.combine", "--output", out / "slice.json")
    demo.invoke("investigation", "interpret", "--record", record, "--root", repo,
                "--slice", out / "slice.json", "--output", out / "interpretation.json")
    demo.invoke("investigation", "align", "--interpretation", out / "interpretation.json",
                "--slice", out / "slice.json", "--map", mapping, "--root", repo,
                "--output", out / "bundle.json")
    demo.invoke("investigation", "check", "--plan", out / "bundle.json", "--terms", terms,
                "--repo", repo, "--root", repo, "--output", out / "checked.json")
    checked = demo.read("checked.json")
    assert checked["conditionalValidity"] == "supported"
    assert checked["providerValidity"] == "conditionally-supported"
    assert checked["premiseEstablishment"] == "refuted"
    assert checked["parentSupport"] == "refuted-correspondence"
    assert checked["methodCorrespondence"] == "unreviewed"
    demo.invoke("investigation", "inspect", "--plan", out / "checked.json",
                "--output", out / "native-inspection.json")
    return checked["planId"]


def example_response(packet, *, corrected):
    return {"reviewer": "demo-author-attribution", "subject": packet["subject"],
            "challengeDigest": packet["challengeDigest"],
            "classification": "mismatch" if corrected else "unresolved",
            "method": "different" if corrected else "unresolved",
            "sourceFidelity": "faithful" if corrected else "unresolved",
            "evidence": ("Demonstration attribution only; no independent reviewer was launched. "
                         "The generated missing-premise implication has a checked negation.")}


def review_argument(demo, subject):
    out, repo = demo.output, demo.repo
    demo.invoke("investigation", "init", "--correspondence", "--text", repo / "predecessor.txt",
                "--root", repo, "--output", out / "initial.json")
    plan = demo.read("initial.json")
    plan["units"][0].update(inventory="done", note="Demo author's attributed local inventory.")
    inventory = demo.write("inventory.json", plan)
    demo.invoke("investigation", "attach", "--plan", inventory, "--bundle", out / "checked.json",
                "--root", repo, "--output", out / "attached.json")
    demo.invoke("investigation", "challenge", "--plan", out / "attached.json", "--claim", subject,
                "--root", repo, "--output", out / "challenge.json")
    packet = demo.read("challenge.json")
    assert "checks" not in packet and "dimensions" not in packet["observedContext"]
    first = demo.write("first-response.json", example_response(packet, corrected=False))
    demo.invoke("investigation", "ingest", "--plan", out / "attached.json", "--packet",
                out / "challenge.json", "--response", first, "--root", repo,
                "--output", out / "reviewed.json")
    original = demo.read("reviewed.json")["responses"][0]
    correction = demo.write("correction.json", example_response(packet, corrected=True))
    demo.invoke("investigation", "reconcile", "--plan", out / "reviewed.json", "--packet",
                out / "challenge.json", "--response", correction, "--first", original["responseId"],
                "--root", repo, "--output", out / "reconciled.json")
    assert demo.read("reconciled.json")["responses"][0] == original
    demo.invoke("investigation", "inspect", "--plan", out / "reconciled.json", "--root", repo,
                "--output", out / "queue-inspection.json")
    status = demo.invoke("investigation", "status", "--plan", out / "reconciled.json", "--root", repo)
    assert status["mathematicalReview"] == "complete-attributed"
    assert status["formalCorrespondence"] == "incomplete-formal-links"
    assert status["mayFinalize"] is False
    demo.invoke("investigation", "finish", "--plan", out / "reconciled.json", "--root", repo,
                expected=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory, never overwrite")
    args = parser.parse_args()
    demo = PublicDemo(args.output.resolve())
    review_argument(demo, check_argument(demo))
    print(demo.output)


if __name__ == "__main__":
    main()
