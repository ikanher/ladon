# Matrix-factorization fixed-epoch field feedback — 2026-10-02

The subsequent [exposition baseline v1](baselines/fixed-epoch-v1/README.md)
completes the scoped qualitative test with a frozen claim inventory, partial
manifest, explicit correspondence differences and nine installed CLI scenarios.
The report below retains the earlier navigation and resource observations.

The latest [capacity fix](#canonical-capacity-fix-r42) captures the polynomial
application on both installed runtimes with the full 10,517-module environment.
Its remaining exact-resolution gap is the missing source-map anchor. The
[earlier October 3 follow-up](#october-3-refreshed-exposition-and-capture) retains
the pre-fix failure; no prose regeneration was needed for this repair.

Installed Ladon found the main finite-horizon theorem and counterexample in the
user-selected matrix-factorization project. Reading the exposition's formal
coverage addendum was still necessary to distinguish its claims from the pinned
formalization. Compiled operations crossed 8 GiB, but a user-authorized 32 GiB
retry observed peaks of about 8.2 GiB. With a longer timeout, lineage completed
in 88.4 seconds at a sampled peak of 8.35 GiB. Direct checking reached a
10,000-module evidence limit and did not produce acceptance evidence. One
confirmed output-size problem was fixed and reproduced through the installed CLI.

This is qualitative feedback from the implementing Codex agent, also acting as
the LLM reviewer. It is not independent review, a mathematical correctness
audit, or a measured understanding benefit. The core dossier/guide/bundle
scenario is not implemented, so this does not complete umbrella tasks 6.1–6.6.

## Identity and reproduction

- Target: `/home/codex/projects/lean/matrix-factorization`, HEAD
  `193f8bcea30940d2dbb295c0b1a89f90bffcff1a`, dirty working tree. HEAD alone does
  not identify the inputs; the accompanying JSON records source-file digests.
- Lean pin: `leanprover/lean4:v4.33.0`; actual Lean commit `d8b18978322de05a8f3dba51ef03cf5461676c17`.
- Initial installed Ladon candidate: `5d57c77a479421da7d59bcafb48b75fb8ec716a9`.
  Explanation fix first reproduced at `b18f967fd2642aa2c6729da140b64a472e325b28`;
  final candidate `a31a6d64d4017abd72be0ba6983462f88a37ed37` changes only unused
  test callback argument names from that intermediate candidate.
- Console: `/tmp/ladon-isolation-authority-vetts2n2/py311/bin/ladon`.
- One explicit, ignored index:
  `/home/codex/projects/lean/matrix-factorization/.ladon/index/fixed-epoch-field-u4t2qh3h.sqlite`.
- [Machine-readable field record](field-feedback-matrix-fixed-epoch.json)
  retains exact argument vectors, working directories, available exit/timing
  records, input hashes, and hashes/paths of stdout and stderr. Raw captures are
  local under `/tmp/ladon-matrix-fixed-epoch-u4t2qh3h`, not a portable bundle.

The run used existing compiled artifacts, without a Lake build or dependency
reconciliation. Before/after hashes cover the manifest, Lake configuration,
toolchain pin, two target sources and their `.olean` files; package-directory
names/mtimes and full Git-status bytes were also compared. These observations
do not constitute a recursive snapshot of all ignored files.
All selected file hashes, additional exposition/coverage inputs and package
snapshots remained unchanged. Aggregate Git status matched through the early
attempts but changed during the extended retries (75,740 to 75,742 entries).
The run does not attribute that change or claim the entire working tree stayed
unchanged; the new index and stored closure are expected ignored artifacts.

## Observations

| Workflow | Observed outcome | Interpretation |
| --- | --- | --- |
| Index build, default 1 GiB database ceiling | 241,431 declarations, 7,671 modules, 17,782 imports; 769,318,912 bytes; 96.8 seconds wall time; fresh lexical fallback | Successful large-project navigation index; no structural Lean authority |
| Concept search: `fixed epoch large batch optimality`, all words, project scope | Zero results | Paper terminology does not directly recover the formal theorem |
| Refined name searches: `fixed epoch full batch`, `epoch uniform` | Eight results each, truncated; helper modules compete with the main result | Useful foothold, but bounds and module-token matches matter |
| Exact main-theorem name | One result in `Mf.DP.PoissonFixedEpochEpochUniformDomain`, line 156 | Exact navigation works after learning the formal name |
| Type-text `poissonFixedEpochTotalAverageVariance` in the main theorem's module | Three results, complete bounded population | Module-scoped search narrows the relevant declarations |
| Exact counterexample fragment | One result: `Mf.DP.strictInterior_totalVariance_lt_fullBatch_zeroEnergy`, line 243 | Exposition's counterexample can be located |
| Explain the main theorem against its conclusion | `unavailable`: `indexed type is not structurally rendered` | Correctly refuses structural comparison from lexical signatures |
| Main theorem lineage | RSS operational failures at 2, 4 and 8 GiB; 60-second timeout at 32 GiB; successful 180-second retry in 88.4 seconds, sampled peak 8.346 GiB | Compiled dependency closure available; 640 project declarations, 2,045 external frontier declarations, 64,824 edges; not theorem replay |
| Explicit pinned check of `Mf.DP.PoissonFixedEpochPoint.horizon_pos` | `memory-limited` at 4 and 8 GiB; at 32 GiB, sampled peak 8.184 GiB, `invalid-worker-output`: 10,500 imported modules exceed the 10,000-module evidence limit | No candidate acceptance or semantic rejection; execution binding stays explicit-pinned while checking authority is not-assessed |

The initial compiled attempts used 60-second inner timeouts. Lineage bounds were 1,500
nodes, 3,000 edges, 50 routes and 524,288 output bytes. Candidate checks allowed
8 MiB worker output and requested compact `llm` projection. The two 8 GiB
and subsequent 32 GiB retries followed explicit user authorization; lower-limit
failures are retained. RSS was sampled at requested 50 ms intervals over the CLI
and its descendants; these are observed peaks, not allocation sizes or guaranteed
instantaneous maxima. The direct check finished in 10.0 seconds. Its module
limit was not bypassed. The successful lineage attempt retained the 32 GiB
ceiling with a 180-second inner timeout; its capture is included in the field
record. The published closure occupies another 27,222,016 database bytes,
bringing allocation to 796,540,928 bytes. The summary reports zero project
declared-axiom nodes, but its 2,045 external frontier declarations remain a
boundary: zero must not be read as an axiom-free theorem. Its evidence receipt
is a derived stored observation, with theorem checking `not-run`.
A repeat with the same `--refresh missing` policy reused the stored closure:
2.52 seconds wall time, sampled peak 0.053 GiB, with no new Lean process.
Subsequent explanation reads retained the fresh
generation identity, so these failures did not invalidate the published index.

## Exposition-to-formalization findings

The requested TeX file concerns frozen-gradient variance under independent
Poisson participation at fixed expected epoch count. It does not establish
training-loss or optimizer-trajectory claims. The active `lean-poisson-fixed-epoch-*`
OpenSpec umbrellas provide historical implementation context; the current
formal coverage addendum supplies the article-specific mapping.

That addendum explicitly pins source supplement **r05**, archive SHA-256
`f8e2839b485b073353df435dd3a9ea3f7d53abb48b14b99f55f3238e0096327b`.
It attributes the all-horizon transcript conclusion under
`a² ≤ 6Eε/(3E+2)`, every finite `T > E`, and nonnegative energy to
`Mf.DP.poissonFixedEpochTotalAverageVariance_fullBatch_lt_allEnergy_of_epochUniformSignal`.
The working-tree declaration's indexed hypotheses agree with the inspected
source. This run did not replay r05 or verify source/archive equivalence.

The addendum identifies average-only results and the symmetric pointwise
endpoint `T = 2E, a² = 2ε` as conventional additions beyond the exact pinned
formal claims, alongside other listed additions. These are reported coverage
boundaries, not newly discovered mathematical gaps or a claim that no related
formal declaration exists anywhere. Ladon did not derive this correspondence:
the agent read the TeX, coverage addendum and declaration sources manually.

This is a concrete future dossier fixture: distinguish article revisions,
pinned archive statements, current working-tree declarations, formalized
hypotheses and conventional-only components. A successful build or matching
name must not collapse those distinctions.

## Fix and remaining work

The explanation initially emitted **47,682 bytes**, repeating SQL schema,
index and storage diagnostics inside each match and at the top level.
`proof_search_explain._freshness` now selects the finite identity, freshness,
status and limitation fields relevant to navigation. Full storage diagnostics
remain available through index status. The same installed query now emits
**4,016 bytes**, preserving the diagnosis, declaration information and retained
identity fields exactly. Three regression cases cover fresh, stale and
unavailable states; the stale/unavailable paths still refuse comparison.

The focused 22-test suite passes from both supported installed Python versions.
The first clean-candidate gate found an unused callback argument in the new
test; that was corrected without changing production behavior. Final full-gate
evidence is recorded in the run state.

Remaining priorities from this field test:

1. Make claim-to-declaration mappings and their revision boundaries discoverable
   from the exposition, using the planned manifest/dossier owners.
2. Improve conceptual search guidance and ranking; no semantic-search change
   has been made based on this single example.
3. Improve helper resource diagnostics and evidence capacity on this import closure. Diagnostics should
   expose the configured limit and observed peak where available, with a
   useful next action. The 32 GiB experiment shows the observed working set is
   only slightly above 8 GiB; it does not establish the cause of memory use.
4. Rerun direct candidate checks after addressing the module-count limit.
   Maintain the distinction between operational failure and theorem rejection.

## October 3 refreshed exposition and capture

The supplied `poisson_fixed_epoch_exposition_evidence_r02` now contains a valid
installed-schema manifest: 15 exact theorem-like statements and 26 components.
Its 25 source targets remain in a separate pending inventory because no
canonical environment references were captured. All 25 owner hashes and the
document/capture checks pass. The supplied incremental Lean builds and
`#check`/`#print axioms` observations passed; this follow-up did not rerun Lean
builds or independently audit the mathematics. Differences between transcript
and average-only claims, strict and closed endpoints, and unchecked adapters
remain explicitly attributed in the supplied component assessments.

The user's earlier 32 GiB allowance was not carried into the proof-note handoff:
its one capture attempt used the skill's 4 GiB example and failed. The Ladon
follow-up reran that exact nested-lambda polynomial goal with only the RSS bound
changed to 32,768 MiB and the same installed executable resolved to its absolute
path. It retained the 120-second and 8 MiB output bounds.

| Operation | Outcome |
| --- | --- |
| Supplied supplement verifier | Passed: 15 statements, 26 components, 25 source targets and 25 retained axiom reports |
| Installed `result validate` | Valid; zero formal targets/links, 26 unmapped components |
| Installed `result resolve`, no artifacts | Valid reader operation; zero resolved targets, all 26 components unmapped |
| Polynomial capture, 32 GiB | Exit 1, `invalid-worker-output`; 10,517 imported modules exceed the evidence limit of 10,000 |
| Resources | 11.528 seconds total; 4.490 seconds checker time; checker peak 8,706,572,288 bytes (8.109 GiB) |
| Mutation observation | Before/after Git-status hash, document/toolchain/manifest bytes, and selected directory metadata matched; not a full dependency/cache byte inventory |

This repeats the earlier capacity limitation with a different actual theorem;
it is neither a proof rejection nor a new need to regenerate the exposition.
No canonical artifacts were emitted. The other 24 targets were not retried
after the shared environment limit was reached. The original frozen baseline
and both supplied exposition captures remain historical evidence. Their
different statement populations do not establish a coverage improvement score.

The durable retry capture is in the target repository at
`latex/lean/poisson_fixed_epoch_exposition_evidence_r02/canonical-retry-32g/`.
Its `summary.json` SHA-256 is
`0ad99bfc6ad88b18b08945dd4ca9ed8cf76e96698c715509e058233a0ab09bc1`;
it inventories exact commands, stdout/stderr, installed content identity,
input hashes, before/after observations and resource measurements. The
machine-readable field record links the same capture.

The next Ladon action is bounded support for this import closure throughout
canonical production and consumption. The producer's `MAX_IMPORTED_MODULES`
and the ProofIR v3 collection validator both currently cap lists at 10,000;
changing only the producer or truncating imports cannot yield valid complete
evidence. Preserve exact environment identity, test producer/reader/registry
round trips and oversize rejection, then rerun capture with 32 GiB and refresh
the evidence supplement. Until then, canonical associations stay unavailable.
This field test does not complete the dossier/guide/bundle tasks; umbrella
progress remains **11/50**.

The two proof-note/Ladon skills now explicitly carry existing authorized
budgets into handoffs, separate process limits from format limits, and avoid
rewriting prose for a capture-only failure. The proof-note type-text example
was also corrected to the installed command's `--pattern` option.

## Canonical capacity fix r42

The canonical producer and Python/Rust encoders now support **32,768 compiled
modules** in a root environment payload/envelope. Other collections still have
the 10,000-item limit, with unchanged 8 MiB artifact and 32 MiB batch bounds.
The payload reader now rejects duplicate module names. Encoding and existing
content IDs are unchanged; older readers may reject the larger environments,
and previously tolerated duplicate-name environments now fail validation.

The actual polynomial capture succeeds on both isolated installed runtimes:

| Runtime | Total wall time | Checker time | Checker peak RSS | Outcome |
| --- | ---: | ---: | ---: | --- |
| Python 3.11 | 15.569 s | 5.198 s | 8.0925 GiB | Accepted application, complete analysis |
| Python 3.12 | 16.702 s | 5.080 s | 8.1455 GiB | Accepted application, complete analysis |

Both use the existing 32 GiB / 120-second / 8 MiB process budget and preserve
all **10,517** compiled module rows. They emit the same environment identity,
`sha256:c911232de3f09aacaebccec9893bb7a62a3cb43c007a3e769796fc2f2e2db6b5`,
and three artifacts per run: environment, check-run and derivation. Selected
source/compiled file hashes, Git-status bytes and package directory observations
match before and after each run. This is a bounded mutation observation and
an explicit pinned application check, not cache-clean replay.

Installed artifact validation/canonicalization, actual semantic-registry
registration/reload, and manifest validation/resolution all succeed as reader
operations. The new predecessor-linked manifest carries the captured polynomial
subject/type/environment and one producer-declared component link. Exact target
resolution correctly remains `unresolved` with
`canonical-source-anchor-unavailable`: the checker currently emits no
source-map artifact. There are 25 unmapped components and no review approvals;
the other 24 source targets have not been captured. No artificial source map or
checker receipt was added to turn the association green.

The durable target-project handoff is
`latex/lean/poisson_fixed_epoch_exposition_evidence_r02/canonical-capacity-r42/`.
Its README links the emitted artifacts and the new manifest and gives offline
reader commands. The exposition, original r02 manifest, previous capture and
frozen fixed-epoch baseline remain unchanged. The tested wheel SHA-256 is
`ceea3812be33e5b983eafa61a1b61b4e0c5bd625aead803ae1c9c787d2407f00`.
Detailed qualification and input/output hashes are recorded in
`canonical-capacity-r42.json` beside this report.

Strict Python quality passed 2,709 tests; installed contracts passed 536 tests
on each supported runtime; Rust, clean-checkout and required real-Lean gates
passed. The initial isolated gate attempts triggered a new Lean download under
their temporary HOME and hit a storage quota. The retained diagnostic identifies
the Elan shim; using the existing pinned toolchain's `bin` directory on PATH
made the minimal reproduction and unchanged gates pass. The qualified wheel
is now installed at `/home/codex/miniconda3/bin/ladon`, and its large-artifact
reader check passes. The handoff retains the wheel, logs and file inventory.

The follow-up tiny Lean 4.33.0 probe confirms that imported declarations expose
owner and exact range observations. It also confirms that those observations
remain unchanged after the owner source is edited without rebuilding its
compiled artifact. The next action is to establish source/compiled coherence
or frontend the exact owner source before emitting source maps, then resolve
and capture further targets. Hashing the current source beside an imported
range alone would be insufficient. The candidate helper currently emits
neither owner source bytes nor a declaration range; the generated probe cannot
stand in for the declaration's source. The capacity repair does
not implement the remaining dossier/guide/bundle features or change the
umbrella's **11/50** task progress. Independent architecture labels and
historical child-order acceptance remain separate upstream conditions.
