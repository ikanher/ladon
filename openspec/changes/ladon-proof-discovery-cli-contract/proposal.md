## Why

The installed CLI and maintained examples currently disagree about removed flags,
output options, and report-version behavior. Proof discovery cannot become a
reliable human or agent workflow while its entrypoint contract is stale.

## What Changes

- Add one ordinary `proof-search` command family using the existing canonical
  `--format`, `--output`, exit, and report-version rules.
- Synchronize `README.md`, `docs/CLI.md`, proof-discovery documentation, and the
  Codex Ladon skill with installed help and no-build defaults.
- Remove or explicitly version legacy `--skip-build`, `--output-json`, and
  `--output-text` examples.
- Add a maintained proof-discovery example and installed-wheel contract gates.

## Capabilities

### New Capabilities

- `ladon-proof-discovery-cli-contract`: Caller-neutral proof-search commands and
  synchronized maintained examples built on the existing CLI execution authority.

### Modified Capabilities

None.

## Impact

- Affects CLI parser/help, docs, the installed Codex skill, compatibility notices,
  installed-wheel tests, and command examples consumed by later child packets.
