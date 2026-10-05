# Stored assumptions and lineage: fixed-epoch exposition, r46

`ladon result inspect` now accepts `--lineage-inputs` and has an `evidence`
section for exact canonical subjects. It reads explicit stored observations,
retains their original scopes and checks, and does not run Lean or refresh an
index. Manifest v1 remains unchanged.

The installed command read the existing `uniform-total` capture from the real
exposition. Its stored summary contains **2,685 nodes**, **64,824 dependency
edges**, and **2,045 external frontier nodes**. The assumption projection has
**2,050 rows**: one stored axiom observation, 2,045 frontier observations and four
unavailable extraction categories. These are capture observations, not a count
of unproved lemmas or a complete transitive assumption inventory.

The selection is explicitly **producer-selected**. The old lineage store cannot
establish canonical environment/source-digest binding; its `fresh` status only
means agreement with the supplied capture identity. Current-source freshness
remains unassessed. Hypotheses, declared external mathematical assumptions,
placeholders with no recorded observation, and obligations remain unknown where
extraction is missing. Unsafe facts remain separate lineage observations.

Four installed CLI pages passed outside the checkout: lineage summary, the first
two assumption pages, and the exact-subject dossier. The whole 2,050-row field
population was not traversed. A fixture verifies complete multi-page recovery,
JSON/text parity and changed-store cursor rejection. The 796,540,928-byte input
store has identical before/after SHA-256. Commands, output, input selection,
time and RSS are in `field/`.

Peak CLI RSS was **251.7 MiB**; pages took
**7.00–10.51 seconds**.
The largest page was **32,081 bytes**. These figures
measure offline inspection during concurrent qualification, not Lean capture.
The existing 32 GiB Lean defaults remain unchanged. Repeated artifact validation
and temporary dossier projection remain performance costs worth revisiting.

Verification: **2,821 clean quality tests**, **152 installed result tests on each
of Python 3.11 and 3.12**, 29 installed-package contracts, packaged schemas and independent audit (board #227).
OpenSpec passed all 54 items. The default installed package matches all 330 wheel
files, and its real lineage output matches the qualified isolated runtime.
Auditing fixed an omission-category mislabel, late acquisition limits and
malformed stored boolean handling. All regressions are retained. One earlier
clean gate rejected two test functions for excessive complexity; splitting the
scenario/helpers preserved their assertions and the final clean gate passed.

The dossier is now **9/9 tasks complete**, and the umbrella is **17/50**.
The [full exit](../../full-acceptance-r46.json) binds fresh correctness, authority,
integration and discovery receipts to this exact candidate on both supported
Python versions. All eleven prerequisite gates passed. The independent receipt
audit and baseline comparison are retained with that receipt. Eight frozen
command outcomes are unchanged; inspection is the intentional new capability.
The original 127 baseline files and its earlier outcomes remain unchanged.
`../../acceptance-r46.json` records the earlier reader qualification checkpoint.
Nothing here establishes informal/formal equivalence, whole-paper coverage or
human review. Proof reading guides are the next child.
