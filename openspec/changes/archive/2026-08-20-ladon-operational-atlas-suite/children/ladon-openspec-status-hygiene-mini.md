# Child 1: `ladon-openspec-status-hygiene-mini`

Close the immediate metadata drift where completed OpenSpec changes still say
`status: active`, and add a deterministic check/report so future drift is
visible.

Expected output:

- normalized status metadata for completed packets where appropriate
- a small checker or analysis helper for active-vs-complete drift
- tests/fixtures for complete, active, and partially complete packets
