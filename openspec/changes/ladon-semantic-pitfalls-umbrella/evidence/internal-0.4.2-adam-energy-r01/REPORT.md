# Internal 0.4.2 consumer exercise: initialized Adam energy

The bounded consumer exercise reached a useful native result: Ladon captured the
actual formal energy goal and accepted a supporting application with separate compiler
replay and trust checks. The root inspected the retained receipts: accepted application,
empty residual list, accepted replay, complete trust, and only the three allowed standard
axioms. This checks one formal route to the `2.9` energy ceiling. It does not certify the
whole paper or establish incremental detection benefit.

## Scope and evidence

The selected source is the “Actual update energy” lemma in
`finite_initialized_clipped_adam_rate.tex`. The root selected the passage, and one fresh
Luna worker at medium reasoning used the internal 0.4.2 handoff and shared Ladon skill.
It froze its source reading before inspecting candidate Lean owners. It used the current
checkout interpreter; discovery used `rg` and owner inspection, followed by native
source-goal capture/completion. No target build or source/index update was requested.
This is a consumer exercise with root interventions, not a blind or comparative study.

The worker’s unchanged [findings](FINDINGS.md), [commands](COMMANDS.json),
[first interpretation](FIRST-INTERPRETATION.md), and
[attributed correction](INTERPRETATION-CORRECTION.md) retain the interpretation and route.
The root independently recalculated the numerical suffix: the displayed RHS at
`T=16384` is `1539261691/545587200`, approximately `2.821294`, and decreases for larger T.
That arithmetic check is separate from the Lean evidence.

The checked native target is `expectedUpdateEnergy ... ≤ 29/10` in the actual context
of `physical_window_expected_energy_le`. Its term uses the existing actual-model energy
producer and numerical bound; it does not assume the desired energy ceiling. The prose
assumptions-to-formal-record mapping remains an explicit inspected interpretation, rather
than a kernel-certified translation of TeX. The intermediate displayed inequality has
an inspected route through `model_expected_update_energy_le` and
`logEnergyBound_envelope`; it was not separately completed by Ladon in this exercise.
No mathematical error was established.

## Field feedback

- Capture completed in 30.86 seconds, with sampled peak process-tree RSS
  9,002,942,464 bytes (~8.39 GiB).
- Completion completed in 54.31 seconds, with sampled peak process-tree RSS
  9,136,914,432 bytes (~8.51 GiB).
- Both used 180-second checking limits, an 8 MiB output limit and a 12 GiB RSS cap.
  No timeout or memory stop occurred. These are existing supervised-process receipts,
  not Memray measurements or exact kernel high-water marks.
- The first reading confused epsilon with its square. Root flagged this and asked for
  an attributed correction while preserving the original reading. Later root feedback
  required distinguishing the full displayed chain from its checked terminal consequence.
  Those interventions limit any claim of independent audit performance.
- An initial optional source-digest argument was malformed and rejected before Lean ran.
  The consumer removed it and succeeded. This is invocation feedback; no need for a new
  product operation was established.

## Custody and next action

[CHECKED-RECEIPT.json](CHECKED-RECEIPT.json) contains selected native statuses and exact
hashes/paths of raw local evidence under `temp/internal-0.4.2-adam-energy-r01/`. The large
capture/completion JSON files stay there; they are not bundled with this compact report.
The selected source copy is retained; its original hash matched at the end. The target
checkout had existing concurrent work. No full compiled dependency closure or independent
replication environment is bundled, and unchanged whole-repository state is not claimed.

The checked path is usable for internal 0.4.2 work. Continue ordinary theorem-application
work in matrix-factorization, collecting concrete errors and unresolved mappings. Do not
infer a memory-performance issue solely from this successful large-context check. Direct
checking of the intermediate RHS remains optional follow-up evidence; broad diagnostic
integration and historical detection gates remain open/deferred.
