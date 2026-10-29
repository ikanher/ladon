Root response to RSS finding: product spec says configured RSS caps, and the
frozen API explicitly exposes max_rss_bytes plus --max-rss-mib. Existing shared
validator supports an explicit cap up to64GiB; the user's persistent request was
to set all DEFAULTS to12GiB and stop/report exhaustion, not to remove explicit
configuration. docs/REAL_PROSE_OBSERVATION.md already calls12GiB the default.
The contract's 'one deadline and12GiB RSS' is the Task1.2 verification resource
contract, not an additional product maximum. No operation here was or will be
run above12GiB. Please recheck this distinction against actual child requirement
'configured RSS/output caps' and existing resource_limits.py. Proposed resolution:
retain explicit caller-selected cap using ordinary validator, test that it is
honored and never automatically increased, record measured12GiB verification.
No silent contract weakening or increased execution budget proposed.
The helper-only test refactor preservation review is accepted. Root will apply
in a renamed frozen replacement preserving all25assertion ASTs and all12cases.
Final production checkpoint will follow source/receipt consistency fixes and
focused public qualification. Only then finalaudit needed.
