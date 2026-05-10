# Proposal

The text report currently renders only a terse module-DAG summary and a generic
`Top Fan-In` footer. After preserving full text inventory in Lean-backed runs,
module-DAG details are important enough to group explicitly.

Add clearer module-DAG detail sections for fan-in, fan-out, facade modules, and
unreachable modules.

# Scope

- Rename text report module fan-in details to `Top Module Fan-In`.
- Add `Top Module Fan-Out`.
- Add facade and unreachable module count/detail sections when present.
- Keep JSON shape unchanged.
