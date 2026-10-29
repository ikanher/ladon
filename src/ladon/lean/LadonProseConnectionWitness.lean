import LadonProseExactGoal

open Lean Elab Command

/-- Parse an isolated term category, never splice proof text into source commands. -/
elab "#ladon_connection_witness " request:str proof:str : command => do
  let termSyntax ← match Parser.runParserCategory (← getEnv) `term proof.getString with
    | .ok parsed => pure (⟨parsed⟩ : TSyntax `term)
    | .error message => throwError "connection proof is not an isolated Lean term: {message}"
  let witnessName := mkIdent `_root_.LadonCheckedConnectionWitness
  let command ← `(theorem $witnessName:ident :
    ladon_prose_exact_goal% $request := $termSyntax)
  elabCommand command
