import Lean
import ObligationsRedOriginal

namespace AliasHost

theorem parentAlias (s x : Nat) :
    ObligationsRed.N3 s (ObligationsRed.H x) ≤
      ObligationsRed.C * ObligationsRed.N0 (s + 0) x :=
  ObligationsRed.threeStep s x

run_cmd do
  let env ← Lean.getEnv
  unless (env.find? `AliasHost.parentAlias).isSome do
    throwError "compiled parent alias unexpectedly absent"

end AliasHost
