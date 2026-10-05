# Green presentation proposal

`proposal.patch` is a root-integration proposal against the maintained source hashes in `source-hashes.json`. It changes only the completion text renderer, focused exposition row compaction, and the exposition query projection version. Source copies are under `source/ladon/`.

The completion renderer now labels every captured local before its declaration and appends a nonempty `valueDisplay` verbatim, preserving captured order and leaving payload objects untouched. Exposition rows remove repeated formal context only with exact field omission references, retain the selected component and bounded sibling identity/status preview, prioritize short explanation/rationale text, and try smaller compaction levels against the combined JSON/text page bound. Clipped types carry an excerpt label and the ordinary `ladon result inspect <manifest> --section targets --target <targetId> --format json` retrieval route. The exposition query changes to projection version 3 so old cursors are rejected.

Verification on the isolated source copies:

- `python -m py_compile ...` passed for all three files.
- `uv run --locked ruff check ...` passed.
- `uv run --locked radon cc ... -s` reported maximum CC B (10); `radon mi` reported A for all three modules.
- Fixture smoke retained the exact short paragraph, rationale, selected component, and both sibling identities/statuses; JSON/text output measured 18,935/18,916 bytes.
- A bounded synthetic stress smoke with 64 KiB prose, a 64 KiB type, and 1,000 siblings stayed at 23,822/23,803 JSON/text bytes, kept a 20-row sibling preview, and emitted omission references and the type excerpt route.
- `uv run --locked vulture src/ladon <proposal copies>` completed with repository-wide 60%-confidence findings; these are existing entrypoint/attribute-style warnings, so this is not a clean Vulture result.
- Canonical board `verify-tests` reports 97 active frozen tests matching and 6 preserved superseded entries; status `verified`.

These checks cover proposal syntax and focused fixture behavior only. Root integration and maintained consumer tests remain outstanding.
