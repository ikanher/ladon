# Premise-provenance case 03 capability-probe review

**Registration:** `pitfall-common-registration-v3`  
**Registration SHA-256:** `52f5acda607d5a56230db7617796211ab74a9ecbf15ff6af0eec75195dda78f0`  
**Disposition:** Accepted as evidence of one narrow unsupported capability.

The independent read-only review checked `command.json`, `host-receipt.json`,
`workspace-receipt.json`, and `slot-904a21/proof-slice.json`. The command uses
the registered custody bootstrap, source/module/declaration, selector `h`,
node limit, scoped mode, and external output location. The receipts bind the
accepted baseline runtime identity and v3 registration hash. All five files
in the sparse case workspace match their recorded hashes; the other 23 corpus
cases are excluded.

The host command returned exit code 2 with empty stdout and stderr and wrote
the expected JSON. It reports `status: unavailable`, `complete: false`, and
selection `h`. The selected theorem compiled. The helper then returned 1 with
the registered selector-name diagnostic on stdout and empty stderr. Neither
helper process timed out, hit memory limits, or hit output limits. The result
matches the v3 terminal contract.

This qualifies only the preserved runtime's inability to select this local
binder using the registered proof-slice API. It does not establish that a
provider route is absent. The case remains in the denominator and receives no
detection or control credit. The earlier v2 probe remains post hoc and
unscored. This probe does not accept the four-case premise-provenance family
batch; cases 01, 02, and 04 have not been measured, and no family batch has
been independently accepted.
