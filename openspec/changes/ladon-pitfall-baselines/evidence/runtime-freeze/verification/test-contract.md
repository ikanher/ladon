# Task 1.1 independent red-test proposal

Recorded against repository HEAD `31df2116ee217e958edb9206afbd5f04e16697f0` (observed in this checkout; context only). Preliminary helper hashes:

- `scripts/freeze_runtime.py`: `88dcfec1a618b27b2b9372ef2991a3e5c5c7d068c182d637cac36f189abf09ae`
- `scripts/ladon-checkout`: `f7bf87a4fc958f2d6bc9c310323b0692d79ea028f97261c2ffd89ed8f1103adf`

The current preliminary inventory only records tracked `src/ladon`, `pyproject.toml`, and `uv.lock` state and the current interpreter; it cannot recover dirty bytes, relevant untracked runtime files, or its launcher. Tests should exercise the new CLI as an external process with only Python stdlib and temporary directories, so they do not privilege an implementation layout.

## Black-box fixture

Create a temporary git repository with tracked `src/ladon/__init__.py`, `src/ladon/entrypoint.py`, and `src/ladon/deleted.py`. Delete `deleted.py` after committing. Add untracked `src/ladon/recovered.py` after commit. The fake entrypoint prints `ladon.__file__` and accepts an arbitrary argument. Add a component directory with a tiny representative dependency/toolchain tree and pass it as `--component fixture=<path>`. Save all fixture bytes before capture.

For each subprocess, use `[sys.executable, runtime_custody.py, ...]`, a short timeout, captured stdout/stderr, and assert the specified zero/nonzero status. Require failure cases to have a useful diagnostic naming the rejected bundle/root/integrity condition; avoid matching exact prose.

## Required executable cases

1. **Capture and reconstruct dirty runtime state.** Run `capture --repo REPO --bundle BUNDLE --component fixture=COMPONENT`; then `restore --bundle BUNDLE --destination RESTORED`. Assert the untracked module has identical bytes, the tracked-but-deleted file remains absent, tracked files and component files have exact bytes, and restore lands outside the original repo. This proves capture retained actual state, not only HEAD.
2. **Verify pristine restored tree and execute it.** Run `verify --bundle BUNDLE --root RESTORED`. Run `run --bundle BUNDLE --root RESTORED -- --probe`. Assert success and that printed `ladon.__file__` resolves under `RESTORED`, outside both the donor repo and any installed `site-packages`. Also run with a hostile `PYTHONPATH` containing a second fake `ladon` and assert preserved origin still wins.
3. **Reject changed and new runtime files.** In separate restored copies, modify `src/ladon/entrypoint.py` and add `src/ladon/extra.py`; each `verify` and `run` must fail before the entrypoint executes. Test a removed frozen-present file too. The diagnostic should identify the path/state difference.
4. **Reject corrupted archive/artifact bytes.** Copy a valid bundle, flip one byte in an archived payload or captured component artifact while leaving its manifest untouched, then require `verify` and `restore` to fail. The test can obtain payload paths from the emitted manifest, but should not assume tar/zip format.
5. **Reject source/artifact mismatch.** Put a `.lean` source and corresponding `.olean` in the selected component. The inventory must retain both rows and a source-to-artifact link with each digest. Mutate only the source bytes in a copied bundle while keeping the old artifact/link metadata; verification must reject. Also mutate only the `.olean`; verification must reject. This case requires capture to record/validate source-to-compiled-artifact relationships, not merely hash two unrelated files.
6. **Reject import from pip/site-packages.** Place a second importable `ladon` package in an external fake `site-packages`, expose it through `PYTHONPATH`, and run the restored launcher. The loaded origin must be the restored preserved package. If launcher uses an interpreter that can resolve `ladon` only from the external location, it must fail closed rather than run the wrong package.
7. **Repeatability and no donor dependency.** After capture, rename or make the donor repo inaccessible (best effort on platform), then restore, verify, and run from the bundle alone. The bundle must contain the launcher bytes and all required runtime source/component data; no command may resolve source from the mutable donor path.

## Interface questions for implementation

- The listed CLI has no explicit launcher selector. Include launcher bytes as a required first-class manifest object (or a named component), and make `run` execute that frozen launcher identity.
- The CLI has no explicit Lean source/`.olean` pair argument. Either discover Lean source/artifact pairs in selected components using the actual import layout, or add a repeatable pair option. A generic directory hash cannot prove that the artifact was built from the frozen source.
- Keep the manifest schema inspectable and retain full inventory rows, including missing-file state and `sourceHash`/`artifactHash` link rows. Hash-only summary output does not meet the contract.
- Root paths should be relocatable: a restored tree outside the donor checkout must pass after any donor path disappears. The `--root` argument should identify the reconstructed checkout, while all expected bytes/identities come from `--bundle`.

The implementation may choose other internal formats; these are behavioral assertions. Source/artifact freshness is the one case that cannot be proven through the command surface as currently stated unless the implementation has a defined discovery rule.
