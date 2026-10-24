# Finite calibration qualification

The user-authorized 30-minute qualification **passed in 166.789 seconds
(2 minutes 47 seconds)**. All ten controls behaved as required. This evidence
completes probes task 1.3 for the registered `Fin 5 → Bool` coordinate-evaluation
class. It does not qualify the five application-probe families or the umbrella.

## Results

| Control | Result |
| --- | --- |
| Equal objects with exact full-family certificate | Checked finite-object equality; all three proofs accepted |
| Unequal objects with exact full-family certificate | Checked finite-object distinction; all three proofs accepted |
| Unequal objects agreeing on the first four coordinates, without a certificate | Scoped agreement; no equality or distinction claim |
| Full-family agreement without a certificate | Scoped agreement; no equality claim |
| Incomplete family offered the full certificate | Rejected before proof work |
| Wrong object-class identity | Rejected before proof work |
| Wrong source digest | Rejected before proof work |
| Wrong template version | Rejected before proof work |
| Intentionally expired deadline | Incomplete; no proof work or equivalence claim |
| Deliberate 1-MiB worker memory limit, run last | Required memory stop/report instruction; no later goal or retry |

Each certified query checked the generic separating-family theorem, the actual
incomplete-family agreement-with-inequality counterexample, and the concrete
query application. All **six fresh Lean proofs** have completed proof execution,
accepted independent replay and accepted trust checks. Their full raw evidence
files and content-bound references are retained. See [the run result](SOURCE-VERIFICATION.json),
[measurements](MEASUREMENTS.json), [log](qualification.log) and exact request,
result and process files for every control.

The equal query finished 81.988 seconds after the shared start; the unequal
query finished at 164.866 seconds. All controls finished at 166.789 seconds,
well within the single 1,800-second deadline. Individual proof stages retained
their 30-second, 12-GiB and 8-MiB ceilings. The expired control intentionally
used an earlier deadline. The last control used the stricter 1-MiB worker cap,
retained the actual memory-limit receipt, stopped at its first unresolved goal,
and was not retried. Peak proof-stage RSS was 3,805,622,272 bytes (3.54 GiB).

## Custody and verification

The [runtime manifest](RUNTIME.json) and [archive](runtime.tar.gz) are identical
to the previously qualified corrected implementation: **505 live/archive files
match**, and all **107 frozen test paths match** before and after this run.
No production code, tests or configuration changed. The new harness differs
from the preserved harness only in the authorized 240-to-1,800-second budget
constants and clock-description text; its assertions are unchanged.

The previous **1,054-case/162-owner regression**, strict quality, Ruff and
compilation results remain applicable. They were reused after confirming the
unchanged runtime and frozen tests; see [the reuse record](VERIFICATION-REUSE.json).
The six proof checks and all ten public-CLI controls above were executed anew.

[Independent review](AUDIT.json) verified the six exact proof goals, terms and
query bindings, raw hashes/projections, actual completion/replay/trust, process
and worker-input digests, clocks, limits, all ten outcomes, memory-stop ordering,
runtime/archive identity and regression reuse. Its original report is retained
as [the first review](AUDIT-FIRST-656.json); the final revision clarifies the
completed control count and the deliberately earlier expired deadline.

The [earlier 240-second qualification](../FINITE-CALIBRATION-20261018/REPORT.md)
remains incomplete as originally recorded. All 87 files in that bundle still
match its frozen manifest. The new user authorization and [run contract](CONTRACT.json)
permit this separate longer envelope; no deadline was reset within either run.

Only task **1.3** closes: the probe child is **1/8**, and the umbrella remains
**2/12**. The five application-probe families, their separate 30-minute
five-fault/five-control gate, native probe reporting, result reuse and broader
integration remain unfinished. Mathematical source fidelity, general/PDE
equivalence, whole-method correspondence and detection benefit are not
established by this finite calibration.
