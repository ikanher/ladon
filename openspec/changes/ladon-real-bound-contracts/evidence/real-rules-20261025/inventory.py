"""Observe and verify the exact compiled import closure used by the final examples."""
import json
from dataclasses import asdict
from pathlib import Path
from ladon._source_goal_inventory import capture_inventory,verify_inventory
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
base=Path('.codex/state/real-bound-rules')
root=(base/'qualification-green-2/project').resolve()
(root/'Inventory.lean').write_text("""import PositiveRules
import NegativeRules
run_cmd do
  let env ← Lean.getEnv
  let paths ← env.header.moduleNames.mapM fun name => do
    let path ← Lean.findOLean name
    pure (Lean.Json.mkObj [("module", Lean.toJson name.toString), ("path", Lean.toJson path.toString)])
  let frame := Lean.Json.mkObj [
    ("importedModules", Lean.toJson (env.header.moduleNames.map toString)),
    ("compiledModulePaths", Lean.Json.arr paths)]
  Lean.Elab.Command.liftIO <| IO.println ("LADON_RULE_INVENTORY " ++ frame.compress)
""")
context=pinned_toolchain(root)
execution=prepare_direct_lean_execution(root,None,context,require_compiled_module=False)
result=run_bounded_target_process([*execution.command,'Inventory.lean'],cwd=root,env=execution.environment,
 timeout_seconds=60,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
(base/'inventory-command.json').write_text(json.dumps(asdict(result),indent=2))
assert result.succeeded,result.stdout
frames=[json.loads(line.removeprefix('LADON_RULE_INVENTORY ')) for line in result.stdout.splitlines()
        if line.startswith('LADON_RULE_INVENTORY ')]
assert len(frames)==1
files,environment,inventory=capture_inventory(context,frames[0])
verify_inventory(files,environment,inventory)
(base/'COMPILED-INVENTORY.json').write_text(json.dumps(inventory,indent=2))
(base/'TOOLCHAIN.json').write_text(json.dumps(context.to_dict(),indent=2))
print('Observed and verified compiled modules:',len(inventory['modules']))
