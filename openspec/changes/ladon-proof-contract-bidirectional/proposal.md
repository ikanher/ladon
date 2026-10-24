# Proposal

## Why

Forward summaries alone may indicate a difference without locating the premise or bridge needed by the exposition. Comparing backward requirements with forward guarantees can turn a broad concern into a small, exact obligation.

## What Changes

- Generate backward sufficient obligations using admitted rule preimages, without reversing arbitrary implications.
- Meet requirements with forward route contracts in exact local contexts and retain every required premise.
- Rank and explain local comparison frontiers; check bridge terms with existing correspondence/source-goal workflows.
- Keep route failure, unsupported analysis and theorem falsity separate.

The bounded acceptance contract is in [specs/ladon-contract-obligations/spec.md](specs/ladon-contract-obligations/spec.md). This is a child of [ladon-proof-contract-analysis-umbrella](../ladon-proof-contract-analysis-umbrella/design.md); dependency order and interface ownership are defined there.

## Capabilities

### New Capabilities

- `ladon-contract-obligations`: Backward requirement generation and localization against forward contract guarantees.

### Modified Capabilities

None. Existing native identity, authority, bounded validation and AND/OR requirements remain in force; this adds a distinct capability without changing their meaning.

## Impact

New obligation planner consumes domain, producers and propagation; reuses correspondence_check.py and source_goal_completion.py. Generated goals are distinguished from observed source goals, with strict context hygiene.

