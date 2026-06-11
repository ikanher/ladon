import Lean
import Lean.Parser.Module
import Lean.Elab.DeclModifiers
import Lean.Elab.DeclarationRange
import Lean.Elab.Import
import Lean.ImportingFlag

open Lean Parser Elab

structure HelperPosition where
  line : Nat
  column : Nat
  deriving Inhabited, ToJson

structure HelperRange where
  start : HelperPosition
  finish : HelperPosition
  deriving Inhabited, ToJson

structure HelperImport where
  module : String
  isPublic : Bool
  isMeta : Bool
  isAll : Bool
  deriving Inhabited, ToJson

structure HelperHeader where
  hasModuleDeclaration : Bool
  hasPrelude : Bool
  imports : Array HelperImport
  deriving Inhabited, ToJson

structure HelperBodyNode where
  kind : String
  category : String
  children : Array HelperBodyNode
  deriving Inhabited, ToJson

structure HelperCommand where
  index : Nat
  syntaxKind : String
  range? : Option HelperRange
  isDeclarationLike : Bool
  declarationKind? : Option String
  declarationName? : Option String
  declarationFullName? : Option String
  selectionRange? : Option HelperRange
  bodyTree? : Option HelperBodyNode
  referenceCandidates : Array String
  deriving Inhabited, ToJson

structure HelperOutput where
  version : String
  file : String
  header : HelperHeader
  commands : Array HelperCommand
  deriving Inhabited, ToJson

inductive ScopeFrame where
  | section
  | namespace (name : String)

private def mkPos (fileMap : FileMap) (pos : String.Pos.Raw) : HelperPosition :=
  let p := fileMap.toPosition pos
  { line := p.line, column := p.column + 1 }

private def mkRange? (fileMap : FileMap) (stx : Syntax) : Option HelperRange := do
  let range ← stx.getRange?
  some {
    start := mkPos fileMap range.start
    finish := mkPos fileMap range.stop
  }

private def declarationKind? (cmd : Syntax) : Option String :=
  if !cmd.isOfKind ``Lean.Parser.Command.declaration then
    none
  else
    let decl := cmd[1]
    let kind := decl.getKind
    if kind == ``Lean.Parser.Command.abbrev then some "abbrev"
    else if kind == ``Lean.Parser.Command.definition then some "def"
    else if kind == ``Lean.Parser.Command.theorem then some "theorem"
    else if kind == ``Lean.Parser.Command.opaque then some "opaque"
    else if kind == ``Lean.Parser.Command.axiom then some "axiom"
    else if kind == ``Lean.Parser.Command.inductive then some "inductive"
    else if kind == ``Lean.Parser.Command.classInductive then some "class"
    else if kind == ``Lean.Parser.Command.structure then some "structure"
    else if kind == ``Lean.Parser.Command.instance then some "instance"
    else none

private def declarationName? (cmd : Syntax) : Option String := do
  let kind ← declarationKind? cmd
  let decl := cmd[1]
  if kind == "instance" then
    let optDeclId := decl[3]
    if optDeclId.isNone then
      none
    else
      some (toString (Lean.Elab.expandDeclIdCore optDeclId[0]).fst)
  else
    some (toString (Lean.Elab.expandDeclIdCore decl[1]).fst)

private def selectionRange? (fileMap : FileMap) (cmd : Syntax) : Option HelperRange := do
  let _kind ← declarationKind? cmd
  let decl := cmd[1]
  mkRange? fileMap (Lean.Elab.getDeclarationSelectionRef decl)

private def isEmptyOptionalNode (stx : Syntax) : Bool :=
  stx.getKind == `null && stx.getNumArgs == 0

private partial def mkBodyNode (stx : Syntax) : HelperBodyNode :=
  let category :=
    if stx.isIdent then "ident"
    else if stx.isAtom then "atom"
    else if stx.isMissing then "missing"
    else "node"
  let children :=
    if stx.isAtom || stx.isIdent || stx.isMissing then
      #[]
    else
      Id.run <| do
        let mut out := #[]
        for i in [:stx.getNumArgs] do
          let child := stx[i]
          if child.isMissing || isEmptyOptionalNode child then
            continue
          out := out.push (mkBodyNode child)
        pure out
  {
    kind := toString stx.getKind
    category := category
    children := children
  }

private partial def declarationBodySyntax? (stx : Syntax) : Option Syntax :=
  if stx.isOfKind ``Lean.Parser.Command.declValSimple then
    some stx[1]
  else if stx.isOfKind ``Lean.Parser.Command.declValEqns then
    some stx[0]
  else if stx.isOfKind ``Lean.Parser.Command.whereStructInst then
    some stx
  else
    Id.run <| do
      for i in [:stx.getNumArgs] do
        if let some body := declarationBodySyntax? stx[i] then
          return some body
      return none

private def bodyTree? (cmd : Syntax) : Option HelperBodyNode := do
  let _kind ← declarationKind? cmd
  let body ← declarationBodySyntax? cmd[1]
  pure (mkBodyNode body)

private partial def collectReferenceCandidates (stx : Syntax) : Array String :=
  if stx.isMissing || isEmptyOptionalNode stx then
    #[]
  else if stx.isIdent then
    #[toString stx.getId]
  else if stx.isAtom then
    #[]
  else
    Id.run <| do
      let mut out := #[]
      for i in [:stx.getNumArgs] do
        out := out ++ collectReferenceCandidates stx[i]
      pure out

private def referenceCandidates (cmd : Syntax) : Array String :=
  match declarationName? cmd with
  | none => #[]
  | some declName =>
      Id.run <| do
      let ownName := declName.splitOn "." |>.getLastD declName
      let all := collectReferenceCandidates cmd[1]
      let mut seen : Std.HashSet String := {}
      let mut out := #[]
      for candidate in all do
        if candidate == declName || candidate == ownName then
          continue
        if seen.contains candidate then
          continue
        seen := seen.insert candidate
        out := out.push candidate
      pure out

private def currentNamespace (stack : List ScopeFrame) : String :=
  String.intercalate "." <| stack.foldl (init := ([] : List String)) fun acc frame =>
    match frame with
    | .section => acc
    | .namespace name => acc ++ [name]

private def qualifyName (stack : List ScopeFrame) (rawName : String) : String :=
  if rawName.startsWith "_root_." then
    String.intercalate "." <| (rawName.splitOn ".").drop 1
  else if rawName.contains '.' then
    rawName
  else
    let ns := currentNamespace stack
    if ns.isEmpty then rawName else s!"{ns}.{rawName}"

private def namespaceStart? (cmd : Syntax) : Option String :=
  if cmd.isOfKind ``Lean.Parser.Command.namespace then
    some (toString cmd[1].getId)
  else
    none

private def isSectionStart (cmd : Syntax) : Bool :=
  cmd.isOfKind ``Lean.Parser.Command.section

private def isEnd (cmd : Syntax) : Bool :=
  cmd.isOfKind ``Lean.Parser.Command.end

private def popScope (stack : List ScopeFrame) : List ScopeFrame :=
  match stack.reverse with
  | [] => []
  | _ :: rest => rest.reverse

private def applyScopeTransition (stack : List ScopeFrame) (cmd : Syntax) : List ScopeFrame :=
  match namespaceStart? cmd with
  | some name => stack ++ [.namespace name]
  | none =>
    if isSectionStart cmd then
      stack ++ [.section]
    else if isEnd cmd then
      popScope stack
    else
      stack

private def activateOpenNamespaces (pmctx : ParserModuleContext) (ids : Array Name)
    (addOpenSimple : Bool) : ParserModuleContext :=
  ids.foldl
    (init := pmctx)
    fun c id =>
      let nss := ResolveName.resolveNamespace c.env c.currNamespace c.openDecls id
      nss.foldl
        (init := c)
        fun c ns =>
          let openDecls := if addOpenSimple then OpenDecl.simple ns [] :: c.openDecls else c.openDecls
          let env := Parser.parserExtension.activateScoped c.env ns
          { c with env, openDecls }

private def applyParserContextTransition (pmctx : ParserModuleContext) (cmd : Syntax) :
    ParserModuleContext :=
  if cmd.isOfKind ``Lean.Parser.Command.open then
    let openDeclStx := cmd[1]
    if openDeclStx.getKind == `Lean.Parser.Command.openSimple then
      activateOpenNamespaces pmctx (openDeclStx[0].getArgs.map fun stx => stx.getId)
        (addOpenSimple := true)
    else if openDeclStx.getKind == `Lean.Parser.Command.openScoped then
      activateOpenNamespaces pmctx (openDeclStx[1].getArgs.map fun stx => stx.getId)
        (addOpenSimple := false)
    else
      pmctx
  else
    pmctx

private def parseImports (header : TSyntax ``Lean.Parser.Module.header) : Except String HelperHeader := do
  match header with
  | `(Module.header| $[module%$moduleTk?]? $[prelude]? $importsStx:import*) =>
      let imports := importsStx.map fun stx =>
        match stx with
        | `(Module.import| $[public%$pubTk?]? $[meta%$metaTk?]? import $[all%$allTk?]? $mod) =>
            {
              module := toString mod.getId
              isPublic := pubTk?.isSome
              isMeta := metaTk?.isSome
              isAll := allTk?.isSome
            }
        | _ => panic! s!"unexpected import syntax: {stx}"
      return {
        hasModuleDeclaration := moduleTk?.isSome
        hasPrelude := header.raw[1].getOptional?.isSome
        imports
      }
  | _ => throw "unexpected header syntax"

private def helperCommandOfSyntax (fileMap : FileMap) (stack : List ScopeFrame)
    (index : Nat) (cmd : Syntax) : HelperCommand :=
  let rawName? := declarationName? cmd
  {
    index := index
    syntaxKind := toString cmd.getKind
    range? := mkRange? fileMap cmd
    isDeclarationLike := (declarationKind? cmd).isSome
    declarationKind? := declarationKind? cmd
    declarationName? := rawName?
    declarationFullName? := rawName?.map (qualifyName stack)
    selectionRange? := selectionRange? fileMap cmd
    bodyTree? := bodyTree? cmd
    referenceCandidates := referenceCandidates cmd
  }

private partial def helperCommandsFromSyntax (fileMap : FileMap)
    (cmds : Array Syntax) (cursor : Nat := 0) (stack : List ScopeFrame := [])
    (index : Nat := 0) (acc : Array HelperCommand := #[]) : Array HelperCommand :=
  if h : cursor < cmds.size then
    let cmd := cmds[cursor]
    if Parser.isTerminalCommand cmd then
      acc
    else
      helperCommandsFromSyntax fileMap cmds (cursor + 1)
        (applyScopeTransition stack cmd) (index + 1)
        (acc.push (helperCommandOfSyntax fileMap stack index cmd))
  else
    acc

private partial def collectCommands (inputCtx : InputContext) (pmctx : ParserModuleContext)
    (state : ModuleParserState) (messages : MessageLog) (fileMap : FileMap)
    (stack : List ScopeFrame := []) (index : Nat := 0) (acc : Array HelperCommand := #[]) :
    ExceptT String IO (Array HelperCommand) := do
  let (cmd, nextState, nextMessages) := Parser.parseCommand inputCtx pmctx state messages
  if nextMessages.hasErrors then
    let msg ← nextMessages.toList.mapM fun m => m.toString
    let details := String.intercalate "\n" msg
    throw s!"parse errors:\n{details}"
  if Parser.isTerminalCommand cmd then
    return acc
  collectCommands inputCtx (applyParserContextTransition pmctx cmd) nextState nextMessages fileMap
    (applyScopeTransition stack cmd) (index + 1)
    (acc.push (helperCommandOfSyntax fileMap stack index cmd))

private def runHelper (file : String) : IO UInt32 := do
  let contents ← IO.FS.readFile file
  let inputCtx := Parser.mkInputContext contents file
  let fileMap := inputCtx.fileMap
  let (header, state, messages) ← Parser.parseHeader inputCtx
  if messages.hasErrors then
    let details := String.intercalate "\n" (← messages.toList.mapM fun m => m.toString)
    IO.eprintln s!"PARSE_FAILURE {file}\n{details}"
    return 1
  unsafe Lean.enableInitializersExecution
  let (env, headerMessages) ← Lean.Elab.processHeader header {} messages inputCtx (leakEnv := true)
  if headerMessages.hasErrors then
    let details := String.intercalate "\n" (← headerMessages.toList.mapM fun m => m.toString)
    IO.eprintln s!"PARSE_FAILURE {file}\n{details}"
    return 1
  match parseImports header with
  | .error err =>
      IO.eprintln s!"PARSE_FAILURE {file}\n{err}"
      return 1
  | .ok headerInfo =>
      let commands ← (collectCommands inputCtx { env := env, options := {} } state headerMessages fileMap).run
      match commands with
      | Except.error err =>
          IO.eprintln s!"PARSE_FAILURE {file}\n{err}"
          return 1
      | Except.ok commands =>
          let output : HelperOutput := {
            version := "1"
            file := file
            header := headerInfo
            commands := commands
          }
          IO.println <| Json.pretty <| toJson output
          return 0

def main (args : List String) : IO UInt32 := do
  match args with
  | ["--", file] => runHelper file
  | [file] => runHelper file
  | _ =>
      IO.eprintln "usage: ladon_parser_helper.lean <file>"
      return 1
