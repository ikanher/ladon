# Bounded exposition compaction fallback repair — r63

A schema-valid four-target public guide regression reproduces the r05 synthetic
finding: the first compaction level exceeds24KiB but a smaller row can fit.
`InspectionRowOverflow`, a narrow `ResultManifestError` subtype, now permits
retrying the next exposition level. Invalid inputs and missing omission references
continue to propagate. Existing24KiB row/32KiB page limits, exact omissions,
JSON/text framing, pagination and default-section behavior remain.

Only `src/ladon/result_inspection_page.py` changes at runtime. Red, green and
independent integrated audit were real distinct Luna-medium workers. Root
replayed the public-path failure, froze the tests, integrated the proposal and
renewed the full candidate qualification. Independent audit post927 found no
remaining issue;28 focused tests passed. This is maintenance, not an observed
reader obstacle or presentation redesign.

Candidate `404c8f4c556c0c1306f0ed427b12e1b3431fd36f` passes strict
Radon/Vulture/Ruff, compileall,3,167 maintained tests, isolated installed result/
presentation contracts onPython3.11/3.12, package/resource/collection-parity,
installed distribution, required real-Lean integration and portable benchmark
gates. [Acceptance](acceptance.json) binds identities and all required command
receipts. Runtime/tests still match the snapshot, and root HEAD/index are
unchanged. Reader sessions used the prior qualified r62 candidate.

Two first baseline candidates failed strict Radon: initially the page function
and regression each had rankC, then the page function still had C11 after the
first helper split. Root moved the unchanged candidate loop into a small helper;
assertions moved unchanged into their own helper. The superseded test's original
bytes are separately frozen, its replacement/supersession explicit, and all109
registry records verify. Both failed candidates and diagnostic excerpts remain.
The integrated audit checked the final helper and assertion equivalence.

No checking, capture, replay, trust, backend, dependency or schema owner changes.
The [separate offset report](../offset-bridge-r63/REPORT.md) owns mathematical
results and the consolidation decision; these gates do not establish reader
benefit or close umbrella task9.1.
