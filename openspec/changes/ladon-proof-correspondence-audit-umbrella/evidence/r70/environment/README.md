# Elementary checking environment

The isolated fixture is `.codex/state/proof-correspondence-audit-r70/fixture` under the Ladon repository. It is ignored local state, not part of the evidence archive. The recorded working directory in each [run](../runs/) is this fixture; checks receive an absolute path to an ordinary Lean file.

Pinned configuration: [lean-toolchain](lean-toolchain), [lakefile.toml](lakefile.toml), [lake-manifest.json](lake-manifest.json). Lean is `leanprover/lean4:v4.33.0`; Mathlib is `db584cd6d46c92f209a44c0f1c829460d327499d` with eight manifest-listed dependencies. No dependency was added to Ladon's portable integration tests.

## The exercised setup route

We checked each prepared package's Git revision and tracked cleanliness, then copied its source and compiled library into an independent fixture. The donor `.lake/packages` path was a symlink into matrix-factorization; the resolved packages were read only, copied with `cp -a --reflink=auto`, and never built or mutated there. See [setup record](setup.json). All subsequent execution was in the physical isolated copy. Copying nine packages took 15.11 seconds; the corrected smoke completed in 1.34 seconds. A first smoke omitted the Real import and failed; both attempts are retained.

To prepare the same route with any compatible public-package cache:

1. Install the recorded Lean toolchain through Elan.
2. Create the fixture directory and copy these three configuration files into it.
3. Copy each pinned package into its `.lake/packages/NAME`, dereferencing donor paths so the result is independent. Verify each package revision against this manifest. The fixture needs the compiled Mathlib and dependency libraries as well as sources.
4. From the fixture, run `lake env lean ABSOLUTE_PATH_TO_CASE`. The recorded smoke source is [Smoke.lean](../cases/Smoke.lean).

Without a compatible prepared cache, the public route is `lake update`, then Mathlib's `lake exe cache get` from this fixture, or a normal pinned build. That fresh-fetch route was **not executed here**; its download/build costs and availability are not part of these observations. The sources are public, but this evidence directory does not contain the toolchain or six-gigabyte compiled population. Reading the audit has no such prerequisite.

## Evidence boundary

[Library population identity](library-population.json) hashes all copied files under each package's `.lake/build/lib/lean`, in sorted relative-path order. This identifies 113,020 files / 6,279,516,332 bytes; it does not freshly kernel-check imported libraries or authenticate their producer. The successful elementary runs are fresh ordinary elaboration/compilation against that copied population, with `#print axioms` for the named audit declarations.

The declared policy permits only `propext`, `Classical.choice`, and `Quot.sound`. The [replay recorder](../replay.py) uses Ladon's existing process supervisor with a 180-second command deadline, 8 MiB output ceiling and **32 GiB sampled process-tree RSS** ceiling. This is process-group supervision, not a cgroup or reservation. Retained actual peaks are in the run records; no memory or timeout limit was hit. Full Mathlib import costs about 7.2 GiB for the least-element case, while the selected matrix imports cost about 4.1 GiB. These costs include library loading and are not claims of proof-search complexity.

The published Navier–Stokes sources pin Lean `v4.34.0-rc2` and Mathlib `85e3a25e006c35636f0e53b0e9296caca2685bc0`. Those are **different prerequisites**, not supplied by this fixture. See the [published comparison](../PUBLISHED_COMPARISON.md).
