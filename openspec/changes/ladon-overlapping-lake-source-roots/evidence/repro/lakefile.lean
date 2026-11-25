import Lake
open Lake DSL

package overlapRepro

lean_lib HodgeHelpers where
  srcDir := "Challenges/Preserved"
  globs := #[.submodules `HodgeHelpers]

lean_lib Challenges where
  globs := #[`Challenges.+]
