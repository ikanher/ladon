# Results

## Report Paths

- Project JSON: `temp/preregistered-ladon-runs/quux/project-quux.json`
- Project text: `temp/preregistered-ladon-runs/quux/project-quux.txt`
- Owner JSON: `temp/preregistered-ladon-runs/quux/owner-propagation-lean.json`
- Owner text: `temp/preregistered-ladon-runs/quux/owner-propagation-lean.txt`

## Prediction Comparison

### Project-Level Quux

Status: matched.

- Predicted acyclic module graph: observed `acyclic: True`.
- Predicted approximately `370` modules: observed `370`.
- Predicted `Quux.Basic` as dominant fan-in: observed rank `1/370`,
  fan-in `101`.
- Predicted broad fan-out at `Quux.Problems`, `Quux.Semantics`,
  `Quux.Bridge.Example.Core`: observed top fan-outs `90`, `72`, `57`.
- Predicted umbrella/facade pressure: observed `root_import_closure_hotspot`,
  `composite_import_pressure`, and `facade_fanout_pressure`.
- Predicted quality-baseline calibration: observed `Quux.Basic` at
  percentile `100.0`, rank `1/370`.

Additional useful signal:

- Direct root import closure ranked `Quux -> Quux.Problems` first with `178`
  reachable known modules.

### Propagation Owner

Status: matched.

- Predicted small declaration graph: observed `11` declarations and `16`
  declaration edges.
- Predicted `PropagationAlgebra` fan-in hotspot: observed
  `Quux.Semantics.PropagationAlgebra` rank `1/11`, fan-in `8`.
- Predicted unresolved names around `Edge` and local fields: observed
  `Edge`, `combine`, `extend`, and related classes.
- Predicted narrow-owner root-scope pressure: observed `root_scope_pressure`.
- Predicted no proof-family surface: observed no proof-family similarity
  candidates.

## Conclusion

The Quux run supports the pre-registration. Ladon correctly separates broad
project umbrella pressure from the small Propagation owner’s declaration-level
signals.
