/- Complete structural expression serialization with explicit subtree sharing.
   ExprStructEq is essential: Expr's ordinary BEq ignores binder annotations. -/
private structure ExprGraphState where
  seen : ExprStructMap Nat := {}
  nodes : Array Json := #[]

private partial def encodeExprNode (expr : Expr) : StateM ExprGraphState Nat := do
  let before : ExprGraphState ← get
  if let some id := before.seen[ExprStructEq.mk expr]? then return id
  let node ← match expr with
    | .bvar index => pure (Json.arr #[toJson "bvar", toJson index])
    | .fvar id => pure (Json.arr #[toJson "fvar", toJson (repr id.name).pretty])
    | .mvar id => pure (Json.arr #[toJson "mvar", toJson (repr id.name).pretty])
    | .sort level => pure (Json.arr #[toJson "sort", toJson (repr level).pretty])
    | .const name levels => pure (Json.arr #[toJson "const", toJson (repr name).pretty, toJson (repr levels).pretty])
    | .app fn arg => do
        let f ← encodeExprNode fn
        let a ← encodeExprNode arg
        pure (Json.arr #[toJson "app", toJson f, toJson a])
    | .lam name type body info | .forallE name type body info => do
        let t ← encodeExprNode type
        let b ← encodeExprNode body
        let tag := if expr.isLambda then "lam" else "forallE"
        pure (Json.arr #[toJson tag, toJson (repr name).pretty, toJson (repr info).pretty, toJson t, toJson b])
    | .letE name type value body nondep => do
        let t ← encodeExprNode type
        let v ← encodeExprNode value
        let b ← encodeExprNode body
        pure (Json.arr #[toJson "letE", toJson (repr name).pretty, toJson nondep, toJson t, toJson v, toJson b])
    | .lit value => pure (Json.arr #[toJson "lit", toJson (repr value).pretty])
    | .mdata data body => do
        let b ← encodeExprNode body
        pure (Json.arr #[toJson "mdata", toJson (repr data).pretty, toJson b])
    | .proj name index body => do
        let b ← encodeExprNode body
        pure (Json.arr #[toJson "proj", toJson (repr name).pretty, toJson index, toJson b])
  let state : ExprGraphState ← get
  let id := state.nodes.size
  set ({ seen := state.seen.insert (ExprStructEq.mk expr) id, nodes := state.nodes.push node } : ExprGraphState)
  return id

private def structuralText (expr : Expr) : String := Id.run do
  let (root, state) := (encodeExprNode expr).run {}
  return "ladon-expr-dag-v1:" ++ Json.compress (Json.mkObj [
    ("root", toJson root), ("nodes", toJson state.nodes)])
