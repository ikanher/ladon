import Lean
import Lean.Elab.Frontend
import Lean.Meta
import Lean.Util.CollectAxioms
import Lean.Util.ForEachExpr

open Lean

structure HelperPosition where
  line : Nat
  column : Nat
  deriving Inhabited, ToJson

structure HelperRange where
  start : HelperPosition
  finish : HelperPosition
  deriving Inhabited, ToJson

structure HelperBoundedStrings where
  items : Array String
  total : Nat
  truncated : Bool
  status : String
  reason? : Option String := none
  deriving Inhabited, ToJson

structure HelperBinder where
  name : String
  binderInfo : String
  typeText : String
  isPremise : Bool
  deriving Inhabited, ToJson

structure HelperBoundedBinders where
  items : Array HelperBinder
  total : Nat
  truncated : Bool
  status : String
  reason? : Option String := none
  deriving Inhabited, ToJson

structure HelperBoundedText where
  text : String
  totalBytes : Nat
  truncated : Bool
  status : String
  reason? : Option String := none
  deriving Inhabited, ToJson

structure HelperTrustFact where
  kind : String
  scope : String
  target? : Option String := none
  deriving Inhabited, ToJson

structure HelperDependencyModule where
  name : String
  module : String
  deriving Inhabited, ToJson

structure HelperPrinterOptions where
  prettyPrinter : String
  ppUniverses : Bool
  ppAll : Bool
  deriving Inhabited, ToJson

structure HelperDeclaration where
  fullyQualifiedName : String
  kind : String
  compilerGenerated : Bool
  ownerModule? : Option String
  sourceRange? : Option HelperRange
  selectionRange? : Option HelperRange
  status : String
  reason? : Option String := none
  renderedType : String
  renderedTypeBytes : Nat
  renderedTypeTruncated : Bool
  printerOptions : HelperPrinterOptions
  binders : HelperBoundedBinders
  premises : HelperBoundedStrings
  conclusion : String
  conclusionTruncated : Bool
  typeConstants : HelperBoundedStrings
  valueConstants : HelperBoundedStrings
  axioms : HelperBoundedStrings
  statementExcerpt : HelperBoundedText
  statementRange? : Option HelperRange
  proofRange? : Option HelperRange
  hasValue : Bool
  proofForm? : Option String
  bodyTotalBytes : Nat
  bodyTruncated : Bool
  declaredAxiom : Bool
  «unsafe» : Bool
  trustFacts : Array HelperTrustFact
  dependencyModules : Array HelperDependencyModule
  nonclaim : String
  deriving Inhabited, ToJson

structure HelperOutput where
  version : String
  helperVersion : String
  leanVersion : String
  module : String
  file : String
  declarations : Array HelperDeclaration
  deriving Inhabited, ToJson

private def dependencyCap : Nat := 64
private def binderCap : Nat := 32
private def premiseCap : Nat := 32
private def textCap : Nat := 1024
private def typeCap : Nat := 4096

private def nonclaim : String :=
  "Navigation and direct Lean artifact evidence only; Ladon does not independently verify proof correctness or theorem truth."

private def directTrustNonclaim : String :=
  "Direct expression evidence only; not a transitive axiom closure, proof-correctness result, or theorem-truth verdict."

private def mkRange (range : DeclarationRange) : HelperRange := {
  start := { line := range.pos.line, column := range.pos.column + 1 }
  finish := { line := range.endPos.line, column := range.endPos.column + 1 }
}

private def binderInfoString : BinderInfo → String
  | .default => "explicit"
  | .implicit => "implicit"
  | .strictImplicit => "strict_implicit"
  | .instImplicit => "instance_implicit"

private def declarationKind : ConstantInfo → String
  | .axiomInfo _ => "axiom"
  | .defnInfo value => if value.hints.isAbbrev then "abbrev" else "def"
  | .thmInfo _ => "theorem"
  | .opaqueInfo _ => "opaque"
  | .quotInfo _ => "quotient"
  | .inductInfo _ => "inductive"
  | .ctorInfo _ => "constructor"
  | .recInfo _ => "recursor"

private partial def collectConstants (expression : Expr)
    (seen : Std.HashSet Name := {}) : Std.HashSet Name :=
  let seen :=
    match expression with
    | .const name _ => seen.insert name
    | _ => seen
  match expression with
  | .forallE _ domain body _ =>
      collectConstants body (collectConstants domain seen)
  | .lam _ domain body _ =>
      collectConstants body (collectConstants domain seen)
  | .letE _ type value body _ =>
      collectConstants body (collectConstants value (collectConstants type seen))
  | .app function argument =>
      collectConstants argument (collectConstants function seen)
  | .mdata _ body => collectConstants body seen
  | .proj _ _ body => collectConstants body seen
  | _ => seen

private def sortedConstantNames (expression : Expr) : Array Name :=
  (collectConstants expression).toArray.qsort Name.quickLt

private def boundedStrings (names : Array Name) (cap : Nat) : HelperBoundedStrings :=
  let items := (names.take cap).map toString
  {
    items
    total := names.size
    truncated := names.size > items.size
    status := "complete"
  }

private def unavailableStrings (reason : String) : HelperBoundedStrings := {
  items := #[]
  total := 0
  truncated := false
  status := "unavailable"
  reason? := some reason
}

private def boundedStringValues (items : Array String) (total cap : Nat) :
    HelperBoundedStrings :=
  let visible := items.take cap
  {
    items := visible
    total
    truncated := total > visible.size
    status := "complete"
  }

private def boundedUtf8 (text : String) (cap : Nat) : String × Nat × Bool :=
  let bytes := text.toUTF8
  if bytes.size ≤ cap then
    (text, bytes.size, false)
  else
    let bytePrefix := bytes.extract 0 cap
    (String.fromUTF8? bytePrefix |>.getD (String.fromUTF8! (bytes.extract 0 (cap - 1))),
      bytes.size, true)

private partial def statementParts (type : Expr)
    (binders : Array HelperBinder := #[]) :
    MetaM (Array HelperBinder × Array String × String) := do
  match type with
  | .forallE binderName domain body binderInfo =>
      let typeText := (← Meta.ppExpr domain).pretty
      let isPremise ← Meta.isProp domain
      let row : HelperBinder := {
        name := if binderName.isAnonymous then "_" else toString binderName
        binderInfo := binderInfoString binderInfo
        typeText
        isPremise
      }
      Meta.withLocalDecl binderName binderInfo domain fun freeVariable =>
        statementParts (body.instantiate1 freeVariable) (binders.push row)
  | conclusion =>
      let conclusionText := (← Meta.ppExpr conclusion).pretty
      let premises := binders.filterMap fun binder =>
        if binder.isPremise then some binder.typeText else none
      return (binders, premises, conclusionText)

private def runMeta {α : Type} (env : Environment) (file : String)
    (fileMap : FileMap) (action : MetaM α) : IO α := do
  let (value, _, _) ← action.toIO
    { fileName := file, fileMap, options := {} }
    { env }
  return value

private def sourceExcerpt (fileMap : FileMap) (ranges? : Option DeclarationRanges) :
    HelperBoundedText :=
  match ranges? with
  | none =>
      {
        text := ""
        totalBytes := 0
        truncated := false
        status := "unavailable"
        reason? := some "Lean declaration range unavailable"
      }
  | some ranges =>
      let start := fileMap.ofPosition ranges.range.pos
      let finish := fileMap.ofPosition ranges.range.endPos
      let full := String.Pos.Raw.extract fileMap.source start finish
      let statement := full.splitOn ":=" |>.headD full
      let (text, _, textWasTruncated) := boundedUtf8 statement textCap
      {
        text
        totalBytes := full.utf8ByteSize
        truncated := textWasTruncated || full.utf8ByteSize > text.utf8ByteSize
        status := "complete"
      }

private def dependencyModule? (env : Environment) (name : Name) : Option String := do
  let moduleIndex ← env.getModuleIdxFor? name
  let moduleName ← env.header.moduleNames[moduleIndex.toNat]?
  some (toString moduleName)

private def dependencyModules (env : Environment) (typeNames valueNames : Array Name) :
    Array HelperDependencyModule :=
  let names := (typeNames ++ valueNames).foldl
    (init := ({} : Std.HashSet Name))
    fun seen name => seen.insert name
  names.toArray.qsort Name.quickLt |>.filterMap fun name => do
    let moduleName ← dependencyModule? env name
    some { name := toString name, module := moduleName }

private def directTrustFacts (env : Environment) (scope : String)
    (names : Array Name) : Array HelperTrustFact :=
  names.filterMap fun name => do
    let some (.axiomInfo _) := env.find? name | none
    let kind := if name.toString.endsWith "sorryAx" then "direct_sorryAx"
      else "direct_axiom_reference"
    some { kind, scope, target? := some (toString name) }

private def isDeclaredAxiom : ConstantInfo → Bool
  | .axiomInfo _ => true
  | _ => false

private def declarationTrustFacts (info : ConstantInfo)
    (typeFacts valueFacts : Array HelperTrustFact) : Array HelperTrustFact :=
  let declared :=
    if isDeclaredAxiom info then
      #[{ kind := "declared_axiom", scope := "declaration" }]
    else #[]
  let unsafeFact :=
    if info.isUnsafe then #[{ kind := "unsafe", scope := "declaration" }]
    else #[]
  declared ++ unsafeFact ++ typeFacts ++ valueFacts

private def declarationSurface (env : Environment) (file : String)
    (fileMap : FileMap) (name : Name) (info : ConstantInfo) :
    IO HelperDeclaration := do
  let type := info.type
  let value? := info.value? (allowOpaque := true)
  let renderedType ← runMeta env file fileMap (Meta.ppExpr type)
  let (binderRows, premises, conclusion) ←
    runMeta env file fileMap (statementParts type)
  let ranges? ← runMeta env file fileMap (findDeclarationRanges? name)
  let axioms ←
    if ranges?.isSome then
      try
        pure <| boundedStrings
          (← runMeta env file fileMap (collectAxioms name))
          dependencyCap
      catch error =>
        pure <| unavailableStrings s!"Lean axiom query failed: {error}"
    else
      pure <| unavailableStrings
        "Axiom query was not requested for an imported declaration"
  let typeNames := sortedConstantNames type
  let valueNames := value?.map sortedConstantNames |>.getD #[]
  let (typeText, typeBytes, typeWasTruncated) :=
    boundedUtf8 renderedType.pretty typeCap
  let (conclusionText, _, conclusionWasTruncated) :=
    boundedUtf8 conclusion typeCap
  let binderItems := binderRows.take binderCap
  let excerpt := sourceExcerpt fileMap ranges?
  let typeFacts := directTrustFacts env "type" typeNames
  let valueFacts := directTrustFacts env "value" valueNames
  return {
    fullyQualifiedName := toString name
    kind := declarationKind info
    compilerGenerated := name.isInternal
    ownerModule? := dependencyModule? env name
    sourceRange? := ranges?.map (mkRange ·.range)
    selectionRange? := ranges?.map (mkRange ·.selectionRange)
    status := "complete"
    renderedType := typeText
    renderedTypeBytes := typeBytes
    renderedTypeTruncated := typeWasTruncated
    printerOptions := {
      prettyPrinter := "Lean.Meta.ppExpr"
      ppUniverses := false
      ppAll := false
    }
    binders := {
      items := binderItems
      total := binderRows.size
      truncated := binderRows.size > binderItems.size
      status := "complete"
    }
    premises := boundedStringValues premises premises.size premiseCap
    conclusion := conclusionText
    conclusionTruncated := conclusionWasTruncated
    typeConstants := boundedStrings typeNames dependencyCap
    valueConstants := boundedStrings valueNames dependencyCap
    axioms
    statementExcerpt := excerpt
    statementRange? := ranges?.map (mkRange ·.range)
    proofRange? := if value?.isSome then ranges?.map (mkRange ·.range) else none
    hasValue := value?.isSome
    proofForm? := if value?.isSome then some "environment_value" else none
    bodyTotalBytes := excerpt.totalBytes
    bodyTruncated := excerpt.truncated
    declaredAxiom := isDeclaredAxiom info
    «unsafe» := info.isUnsafe
    trustFacts := declarationTrustFacts info typeFacts valueFacts
    dependencyModules := dependencyModules env typeNames valueNames
    nonclaim := nonclaim ++ " " ++ directTrustNonclaim
  }

private def localDeclarations (env : Environment) (file : String)
    (fileMap : FileMap) : IO (Array HelperDeclaration) := do
  let rows := env.constants.map₂.toArray.qsort fun left right =>
    Name.quickLt left.1 right.1
  rows.mapM fun (name, info) => declarationSurface env file fileMap name info

private def runHelper (module file : String) : IO UInt32 := do
  let contents ← IO.FS.readFile file
  unsafe Lean.enableInitializersExecution
  let options := Elab.async.set ({} : Options) false
  let env? ← Elab.runFrontend contents options file module.toName
  match env? with
  | none =>
      IO.eprintln s!"ELABORATION_FAILURE {file}"
      return 1
  | some env =>
      let declarations ← localDeclarations env file contents.toFileMap
      let output : HelperOutput := {
        version := "3"
        helperVersion := "ladon-elaborated-helper-v2"
        leanVersion := Lean.versionString
        module
        file
        declarations
      }
      IO.println <| Json.pretty <| toJson output
      return 0

def main (args : List String) : IO UInt32 := do
  match args with
  | ["--", module, file] => runHelper module file
  | [module, file] => runHelper module file
  | _ =>
      IO.eprintln "usage: ladon_elaborated_helper MODULE FILE"
      return 2
