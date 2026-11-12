#!/usr/bin/env python3
"""Independent stdlib black-box tests for runtime_custody.py.

Usage: python test_runtime_custody.py /path/to/runtime_custody.py
The tests intentionally exercise only the documented CLI.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


CLI = Path(sys.argv.pop(1)).resolve() if len(sys.argv) > 1 else None


class CustodyCli(unittest.TestCase):
    def setUp(self) -> None:
        if CLI is None or not CLI.is_file():
            self.fail("pass the runtime_custody.py path as the first argument")
        self.tmp = tempfile.TemporaryDirectory(prefix="runtime-custody-red-")
        self.base = Path(self.tmp.name)
        self.repo = self.base / "donor"
        self.repo.mkdir()
        subprocess.run(["git", "init", "--quiet", str(self.repo)], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.package = self.repo / "src" / "ladon"
        self.package.mkdir(parents=True)
        (self.package / "__init__.py").write_text("ORIGIN = __file__\n")
        (self.package / "entrypoint.py").write_text(
            "import ladon, sys\nprint(ladon.__file__)\nprint('ARGS:' + repr(sys.argv[1:]))\n"
        )
        (self.package / "tracked_deleted.py").write_bytes(b"tracked then deleted\n")
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Red Test"],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "red-test@example.invalid"],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(["git", "-C", str(self.repo), "add", "src/ladon"], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "--quiet", "-m", "runtime fixture"],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Capture a real tracked deletion and a distinct untracked recovered source.
        (self.package / "tracked_deleted.py").unlink()
        (self.package / "recovered.py").write_bytes(b"# recovered dirty source\nVALUE = 41\n")
        self.component = self.base / "component"
        (self.component / "lib").mkdir(parents=True)
        (self.component / "lib" / "identity.txt").write_bytes(b"selected dependency identity\n")
        self.bundle = self.base / "bundle"
        self.restored = self.base / "restored"
        self.call("capture", "--repo", self.repo, "--bundle", self.bundle,
                  "--component", f"fixture={self.component}")
        self.call("restore", "--bundle", self.bundle, "--destination", self.restored)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def call(self, *args: object, env: dict[str, str] | None = None,
             expected: int = 0) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run([sys.executable, str(CLI), *(str(a) for a in args)],
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              env=env, timeout=30)
        self.assertEqual(proc.returncode, expected,
                         f"command {args!r} returned {proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}")
        return proc

    def test_recovers_untracked_and_preserves_tracked_deletion(self) -> None:
        self.assertEqual((self.restored / "src/ladon/recovered.py").read_bytes(),
                         (self.repo / "src/ladon/recovered.py").read_bytes())
        self.assertFalse((self.restored / "src/ladon/tracked_deleted.py").exists())
        self.assertEqual((self.restored / "src/ladon/entrypoint.py").read_bytes(),
                         (self.repo / "src/ladon/entrypoint.py").read_bytes())
        self.assertEqual((self.restored / "fixture/lib/identity.txt").read_bytes(),
                         b"selected dependency identity\n")

    def test_verify_and_run_use_restored_import_origin(self) -> None:
        self.call("verify", "--bundle", self.bundle, "--root", self.restored)
        proc = self.call("run", "--bundle", self.bundle, "--root", self.restored,
                         "--", "--probe")
        origin = Path(proc.stdout.splitlines()[0]).resolve()
        self.assertTrue(origin.is_relative_to(self.restored.resolve()),
                        f"import resolved outside restored root: {origin}")
        self.assertIn("ARGS:['--probe']", proc.stdout)

    def test_hostile_external_ladon_does_not_override_preserved_package(self) -> None:
        hostile = self.base / "fake-site-packages" / "ladon"
        hostile.mkdir(parents=True)
        (hostile / "__init__.py").write_text("raise RuntimeError('external ladon imported')\n")
        env = dict(os.environ, PYTHONPATH=str(hostile.parent))
        proc = self.call("run", "--bundle", self.bundle, "--root", self.restored,
                         "--", "--probe", env=env)
        origin = Path(proc.stdout.splitlines()[0]).resolve()
        self.assertTrue(origin.is_relative_to(self.restored.resolve()), str(origin))

    def test_rejects_changed_source_new_file_and_missing_file(self) -> None:
        changed = self.base / "changed"
        shutil.copytree(self.restored, changed)
        target = changed / "src/ladon/entrypoint.py"
        target.write_text(target.read_text() + "# drift\n")
        self.call("verify", "--bundle", self.bundle, "--root", changed, expected=1)
        self.call("run", "--bundle", self.bundle, "--root", changed, "--", "--probe", expected=1)
        extra = self.base / "extra"
        shutil.copytree(self.restored, extra)
        (extra / "src/ladon/extra.py").write_text("EXTRA = True\n")
        self.call("verify", "--bundle", self.bundle, "--root", extra, expected=1)
        missing = self.base / "missing"
        shutil.copytree(self.restored, missing)
        (missing / "src/ladon/recovered.py").unlink()
        self.call("verify", "--bundle", self.bundle, "--root", missing, expected=1)

    def test_bundle_has_full_inventory_rows_including_missing_state(self) -> None:
        # The JSON manifest is part of the public evidence contract: retain rows,
        # not only a root digest. This recursively locates a JSON document to keep
        # the test independent of the chosen manifest filename.
        import json
        docs = []
        for path in self.bundle.rglob("*.json"):
            try:
                value = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(value, dict):
                docs.append(value)
        self.assertTrue(docs, "bundle has no inspectable JSON manifest")
        serialized = json.dumps(docs)
        self.assertIn("recovered.py", serialized)
        self.assertIn("tracked_deleted.py", serialized)
        self.assertIn("missing", serialized.lower(), "manifest omits deleted-file state")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
