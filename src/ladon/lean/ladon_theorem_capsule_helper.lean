import Lean
import Lean.Elab.Frontend
import Lean.Meta

open Lean

structure CapsulePosition where
  line : Nat
  column : Nat
  deriving Inhabited, ToJson

structure CapsuleRange where
  start : CapsulePosition
  finish : CapsulePosition
  deriving Inhabited, ToJson

structure CapsuleDependency where
  name : String
  ownerModule : String
  kind : String
  declaredAxiom : Bool
  «unsafe» : Bool
  deriving Inhabited, ToJson

structure CapsuleNode where
  name : String
  kind : String
  ownerModule : String
  compilerGenerated : Bool
  typeFingerprint : String
  valueFingerprint? : Option String
  typeDependencies : Array CapsuleDependency
  valueDependencies : Array CapsuleDependency
  declaredAxiom : Bool
  «unsafe» : Bool
  deriving Inhabited, ToJson

structure CapsuleEndRecord where
  kind : String
  nodeCount : Nat
  checksum : String
  deriving Inhabited, ToJson

structure CapsuleOutput where
  version : String
  helperVersion : String
  protocolVersion : String
  leanVersion : String
  module : String
  file : String
  target : String
  status : String
  reason? : Option String := none
  complete : Bool
  targetRange? : Option CapsuleRange
  nodes : Array CapsuleNode
  endRecord : CapsuleEndRecord
  nonclaim : String
  deriving Inhabited, ToJson

private def helperVersion := "ladon-theorem-capsule-helper-v1"
private def protocolVersion := "ladon-theorem-capsule-stream-v1"

private def nonclaim :=
  "Lean environment dependency evidence for capsule replay; Ladon does not independently prove theorem truth, global minimality, offline availability, or system hermeticity."

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

private def declarationKind : ConstantInfo → String
  | .axiomInfo _ => "axiom"
  | .defnInfo value => if value.hints.isAbbrev then "abbrev" else "def"
  | .thmInfo _ => "theorem"
  | .opaqueInfo _ => "opaque"
  | .quotInfo _ => "quotient"
  | .inductInfo _ => "inductive"
  | .ctorInfo _ => "constructor"
  | .recInfo _ => "recursor"

private def isDeclaredAxiom : ConstantInfo → Bool
  | .axiomInfo _ => true
  | _ => false

private def isCompilerGenerated (name : Name) : ConstantInfo → Bool
  | .ctorInfo _ => true
  | .recInfo _ => true
  | .quotInfo _ => true
  | _ => name.isInternal

private def dependencyModule? (env : Environment) (name : Name) : Option String := do
  let moduleIndex ← env.getModuleIdxFor? name
  let moduleName ← env.header.moduleNames[moduleIndex.toNat]?
  some (toString moduleName)

private def ownerModule (env : Environment) (currentModule : String)
    (name : Name) : String :=
  dependencyModule? env name |>.getD currentModule

private def expressionFingerprint (expression : Expr) : String :=
  toString (hash expression)

private def dependencyRow (env : Environment) (currentModule : String)
    (name : Name) : CapsuleDependency :=
  match env.find? name with
  | none =>
      {
        name := toString name
        ownerModule := ownerModule env currentModule name
        kind := "unavailable"
        declaredAxiom := false
        «unsafe» := false
      }
  | some info =>
      {
        name := toString name
        ownerModule := ownerModule env currentModule name
        kind := declarationKind info
        declaredAxiom := isDeclaredAxiom info
        «unsafe» := info.isUnsafe
      }

private def nodeRow (env : Environment) (currentModule : String)
    (name : Name) (info : ConstantInfo) : CapsuleNode :=
  let value? := info.value? (allowOpaque := true)
  let typeNames := sortedConstantNames info.type
  let valueNames := value?.map sortedConstantNames |>.getD #[]
  {
    name := toString name
    kind := declarationKind info
    ownerModule := ownerModule env currentModule name
    compilerGenerated := isCompilerGenerated name info
    typeFingerprint := expressionFingerprint info.type
    valueFingerprint? := value?.map expressionFingerprint
    typeDependencies := typeNames.map (dependencyRow env currentModule)
    valueDependencies := valueNames.map (dependencyRow env currentModule)
    declaredAxiom := isDeclaredAxiom info
    «unsafe» := info.isUnsafe
  }

private partial def collectRepositoryClosure (env : Environment)
    (currentModule : String) (repositoryModules : Std.HashSet String)
    (pending : List Name) (seen : Std.HashSet Name := {})
    (rows : Array CapsuleNode := #[]) : Array CapsuleNode :=
  match pending with
  | [] => rows
  | name :: rest =>
      if seen.contains name then
        collectRepositoryClosure env currentModule repositoryModules rest seen rows
      else
        let seen := seen.insert name
        match env.find? name with
        | none =>
            collectRepositoryClosure env currentModule repositoryModules rest seen rows
        | some info =>
            let row := nodeRow env currentModule name info
            let localDependencies :=
              (row.typeDependencies ++ row.valueDependencies).filterMap fun dependency =>
                if repositoryModules.contains dependency.ownerModule then
                  some dependency.name.toName
                else
                  none
            collectRepositoryClosure env currentModule repositoryModules
              (localDependencies.toList ++ rest) seen (rows.push row)

private def runMeta {α : Type} (env : Environment) (file : String)
    (fileMap : FileMap) (action : MetaM α) : IO α := do
  let (value, _, _) ← action.toIO
    { fileName := file, fileMap, options := {} }
    { env }
  return value

private def mkRange (range : DeclarationRange) : CapsuleRange := {
  start := { line := range.pos.line, column := range.pos.column + 1 }
  finish := { line := range.endPos.line, column := range.endPos.column + 1 }
}

private def repositoryModuleSet (file : String) : IO (Std.HashSet String) := do
  let contents ← IO.FS.readFile file
  return contents.splitOn "\n" |>.foldl
    (init := ({} : Std.HashSet String))
    fun seen item =>
      let module := item.trimAscii.toString
      if module.isEmpty then seen else seen.insert module

private def closureChecksum (rows : Array CapsuleNode) : String :=
  let names := rows.map (·.name) |>.qsort (· < ·)
  let bytes := (String.intercalate "\n" names.toList).toUTF8
  let checksum := bytes.foldl
    (init := 2166136261)
    fun state byte =>
      (state * 16777619 + byte.toNat + 1) % 4294967291
  toString checksum

private def output (module file target status : String)
    (reason? : Option String) (complete : Bool)
    (range? : Option CapsuleRange) (rows : Array CapsuleNode) : CapsuleOutput :=
  let rows := rows.qsort fun left right => left.name < right.name
  let checksum := closureChecksum rows
  {
    version := "1"
    helperVersion
    protocolVersion
    leanVersion := Lean.versionString
    module
    file
    target
    status
    reason?
    complete
    targetRange? := range?
    nodes := rows
    endRecord := {
      kind := "end"
      nodeCount := rows.size
      checksum
    }
    nonclaim
  }

private def runHelper (module file target modulesFile : String) : IO UInt32 := do
  let contents ← IO.FS.readFile file
  let repositoryModules ← repositoryModuleSet modulesFile
  unsafe Lean.enableInitializersExecution
  let options := Elab.async.set ({} : Options) false
  let env? ← Elab.runFrontend contents options file module.toName
  match env? with
  | none =>
      IO.println <| Json.pretty <| toJson <|
        output module file target "elaboration_failed"
          (some "Lean frontend did not produce an environment") false none #[]
      return 0
  | some env =>
      let targetName := target.toName
      match env.find? targetName with
      | none =>
          IO.println <| Json.pretty <| toJson <|
            output module file target "not_found"
              (some "The exact declaration was not present in the elaborated environment")
              false none #[]
          return 0
      | some info =>
          if declarationKind info != "theorem" then
            IO.println <| Json.pretty <| toJson <|
              output module file target "wrong_kind"
                (some s!"Expected theorem, found {declarationKind info}") false none #[]
            return 0
          let ranges? ← runMeta env file contents.toFileMap
            (findDeclarationRanges? targetName)
          let rows := collectRepositoryClosure env module repositoryModules [targetName]
          IO.println <| Json.pretty <| toJson <|
            output module file target "complete" none true
              (ranges?.map (mkRange ·.range)) rows
          return 0

def main (args : List String) : IO UInt32 := do
  match args with
  | ["--", module, file, target, modulesFile] =>
      runHelper module file target modulesFile
  | [module, file, target, modulesFile] =>
      runHelper module file target modulesFile
  | _ =>
      IO.eprintln
        "usage: ladon_theorem_capsule_helper MODULE FILE TARGET REPOSITORY_MODULES_FILE"
      return 2
