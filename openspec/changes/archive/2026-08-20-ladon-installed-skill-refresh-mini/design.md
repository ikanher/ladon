# Design

This is documentation only. The skill should remain short and operational:

- text backend for fast module-DAG inventory
- Lean backend for root declaration graph
- cache directory for repeated Lean-backed runs
- interpretation rules that avoid overclaiming

The skill is intentionally installed globally, but this repo owns the packet so
the change is traceable in the Ladon development loop.
