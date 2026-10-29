# Final Task 3.1 qualification matrix (bounded scope)

## Outcome

The final v3 implementation completed the frozen seven-case generic matrix and
both informed route controls. The generic cases returned **3 connected, 4
unresolved, 0 unavailable**. The informed five-order control returned connected;
the selected four-order route returned unresolved. No result promotes authored
admission, NL fidelity, the original theorem proof, mathematical falsity, parent
propagation, or unfamiliar-source discovery.

This is a finite public-consumer qualification over the listed cases. It is not a
whole-paper review or a claim that Ladon detects arbitrary exposition errors.

## Inputs and source preservation

The original generic matrix root was a deleted pytest temporary directory. Its
saved formal/authored records also carried an obsolete observer identity. I
reconstructed the same generic test project from the preserved source bytes and
compiled-library roots, then freshly produced its formal input, authored input,
and set connection before running the matrix. SHA256 values for `Context.lean`,
`claim.txt`, and `lean-toolchain` match the surviving source copy. Fresh input
production avoids reusing stale identities; the original matrix cases and proof
terms were retained.

Before/after file manifests match for all **2,680** files outside `.lake` and
`.git` in the informed formalization root, all **4** files in the prose source
root, and the **3** generic source files. The reconstructed generic toolchain
inventory and all 11 compiled-library roots also match their pre-run identities.
The shipped implementation identity for every current connection is
`sha256:60d9c92cd2ba792641f9cc3557528863a170aa42626d32c45778e8f57dffa636`.
The detailed hashes, paths and toolchain receipt are in `SOURCE-MANIFESTS.json`
and `BASELINE.json`.

## Generic matrix

For each distinct case, the connection worker freshly admitted the formal input
and re-authored the prose input. In every result the formal status is `admitted`,
the authored status is `authored`, and authored admission remains `unresolved`.
The result statuses and costs are:

| Case | Result | Command time | Peak RSS |
| --- | --- | ---: | ---: |
| Global estimate | connected | 168.63 s | 4.25 GiB |
| Set estimate with fresh replay | connected | 167.35 s | 4.27 GiB |
| Wrong carrier | unresolved | 134.02 s | 4.24 GiB |
| Wrong set | unresolved | 146.33 s | 4.24 GiB |
| Ordered conditional premise | connected | 162.09 s | 4.26 GiB |
| Uniform-constant reading | unresolved | 131.22 s | 4.24 GiB |
| Reverse direction | unresolved | 131.54 s | 4.25 GiB |

The extended runner repeated the conditional and uniform-constant cases; both
repeated results matched. The base and extended controllers completed within
the 600-second, 12-GiB RSS and 8-MiB output caps. The largest outer-controller
peak was 4.35 GiB. All case records and both sets of receipts are retained.

The separate preserved target-override falsifier again captured a `True` goal
but returned `unresolved` because its owner-target commitment did not match. It
recorded **0 false promotions in 1 adversarial control**. The earlier v1 result
remains a known historical false promotion (1/1 before repair); the repaired
control is a regression check, not a general accuracy estimate.

## Informed matrix

The five-order run is the current-revision v3 record from the preceding
Task 2.2 transport gate. The four-order case was freshly run on the same formal
record, current implementation identity, and preserved source roots.

| Case | Result | Controller time | Worker time | Controller peak RSS | Worker peak RSS |
| --- | --- | ---: | ---: | ---: | ---: |
| Five-order | connected | 496.74 s | 427.94 s | 5.93 GiB | 5.84 GiB |
| Four-order route | unresolved | 420.49 s | 357.26 s | 5.92 GiB | 5.85 GiB |

Neither hit timeout, RSS, or output limits. Each contains a fresh admitted
formal replay and authored prose result; authored admission remains unresolved.
The five-order v3 snapshot validates directly from retained wire bytes without
local recompression. The four-order result stays unresolved; this is not evidence
that its endpoint is false.

Across the nine distinct matrix cases (seven generic plus two informed), all
nine contain completed authored observations and fresh formal admissions. Four
connections are connected and five are unresolved; none is unavailable. All
nine preserve `admission: unresolved`, `sourceTheoremProof: not-checked`, and
`mathematicalFalsity: not-established`. The separate adversarial control adds
one unresolved attempt and no false promotion.

## Verification

The affected compatibility suite passed **154 tests, 30 skipped** in 163.07
seconds. It covered bounded JSON transport, connection v2/v3 histories and
boundaries, CLI, owner commitments, environment binding, resources, scratch
cleanup, witness checks, exact-goal boundaries and source-goal completion
round trips. Ruff and targeted strict Radon/Vulture/compile checks passed for the
four transport production modules and four transport regression-test modules.
OpenSpec strict validation passed. Both local and shared Ladon skills pass the
system skill validator after their qualification guidance was updated.

The repository-wide strict suite was not rerun on this v3 revision. Its earlier
pre-v3 run recorded 5,516 passed, 86 skipped and 3 failures: two proof-contract
worker fixture shims and the project-wide complexity assertion. The exact
failures and unrelated Radon items remain in the prior transport report's
`VERIFICATION.txt`; none was a transport test failure.

The independent read-only source/evidence audit is recorded on the durable
board as post #2071. It found no substantive matrix/result discrepancy and
independently confirmed the implementation identity, source manifests, skill
snapshots, resource claims, and verification scope. After that review, the task
record was closed and the packet hash inventory was generated and verified in
`ARTIFACTS.json`. The matrix verifies only the cases above. Parent propagation,
unfamiliar-source benefit, whole-paper mathematical correctness, and discovery
completion remain unestablished. Nothing was committed or pushed.
