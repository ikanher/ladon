# Conditional route comparison frontier

Task 2.1 is implemented and independently reviewed. The Python planner retains
ordered AND occurrences and native witness alternatives, compares providers to
their local backward sufficient requirements, and checks each method's final
contract separately from support supplied by another method. Pruned final
witnesses replay the registered transfer over their exact parent witnesses.
Intermediate pruning that leaves no described-method witness stays pending.

Route identities bind witness alternatives independently of priority metadata.
Declared source location, route identity and heuristic priority determine order.
Each route explains its earliest retained unresolved comparison in dependency
order, with explicit local scope and no global minimality claim. Unknown
comparisons stay unresolved. Regularity, constant-permission and
witness-permission gaps have separate dimensions.

[Validation](FRONTIER.json) binds the seven production modules and check scope.
All 56 graph cases pass; the combined planner/backward/propagation suite passes
[235 checks](FRONTIER-FOCUSED.xml). The exact previous 658-check owner set plus
14 new planner files passes [714 checks](FRONTIER-INTEGRATION.xml) in 79.18 seconds.
No-cache Ruff and strict Python quality pass. An independently reviewed helper
extraction preserved the explanation test's name and all six assertion ASTs;
original frozen bytes and explicit revision history remain preserved.

The fixed arithmetic/dependency oracle has five supporting methods and seventeen
methods without profile support. The first frozen draft classified 19/22
correctly: four true support results, one missed support result, two false support
results and fifteen correctly unresolved results. The integrated planner scores
22/22, with both false support results and the missed support removed. See the
[before](FRONTIER-ORACLE-before.json) and [after](FRONTIER-ORACLE-after.json)
case records. These are constructed development controls for conditional profile
analysis, not measurements of manuscript fault discovery or mathematical falsity.

[Resource receipts](FRONTIER-RESOURCES.json) preserve two bounded regressions.
The original shared depth-22 DAG timed out at five seconds; the integrated
planner finishes the same case in 0.187 process seconds, with 22 forward and 22
backward work units. The 2.27 MB-input, 60-step large-record case originally hit
its 128 MiB test cap. The integrated run returns a 6.25 MB partial result retaining
a completed requirement, at 48.1 MB sampled RSS and 0.644 process seconds under
the same cap. These single runs establish regression gates, not general speedup
estimates. No resource cap was raised.

Two bounded Luna proposals were rejected before integration. The Astra repair
prepays route metadata and both serialized appearances of each retained
requirement/comparison. Completed records survive later stops. A separate bounded
replay cache admits material before transfer copying; all actual transfer and
backward units share the forward work ledger and deadline. The
[distinct final review](FRONTIER-INDEPENDENT-REVIEW.md) checked the integrated
hashes and all 56 graph cases. The earlier merged-witness lookup finding was a
synthetic helper-level reproduction, not a new public native-case measurement.

Results remain conditional-profile analysis with checker authority `none` and
mathematical falsity `not-established`. Source, evidence and clock bindings are
unchecked. Route reconstruction conservatively caps distinct witnesses at
`maxDepth`, so a wide shallow route can remain pending. Source-context obligation
construction, actual bridge completion, targeted provider requests and the
native/public CLI workflow remain open. This does not accept the whole child,
umbrella, or detection-benefit gate.
