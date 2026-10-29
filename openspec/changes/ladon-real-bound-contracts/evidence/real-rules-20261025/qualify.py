"""Root-owned compile and axiom evidence for the fixed reusable rule module."""
import argparse
import hashlib
import json
import shutil
import time
from dataclasses import asdict
from pathlib import Path

from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.semantic_lean_execution import prepare_direct_lean_execution

parser=argparse.ArgumentParser()
parser.add_argument("mode", choices=["red","green"])
parser.add_argument("--root",type=Path,required=True)
parser.add_argument("--attempt",default="1")
args=parser.parse_args()
base=Path(".codex/state/real-bound-rules")
out=base/("qualification-"+args.mode+("-"+args.attempt if args.attempt!="1" else ""));out.mkdir(exist_ok=False)
workspace=(out/"project").resolve();workspace.mkdir()
context=pinned_toolchain(args.root)
(workspace/"lean-toolchain").write_bytes((args.root/"lean-toolchain").read_bytes())
(workspace/".lake/build/lib/lean").mkdir(parents=True)
for index,library in enumerate(context.library_roots):
    target=workspace/f".lake/packages/import{index}/.lake/build/lib/lean"
    target.parent.mkdir(parents=True);target.symlink_to(library,target_is_directory=True)
deadline=time.monotonic()+600
results=[]
def compile_module(module,source):
    (workspace/(module+".lean")).write_bytes(source)
    execution=prepare_direct_lean_execution(workspace,None,pinned_toolchain(workspace),require_compiled_module=False)
    remaining=deadline-time.monotonic();assert remaining>0
    result=run_bounded_target_process([*execution.command,"-o",f".lake/build/lib/lean/{module}.olean",module+".lean"],
        cwd=workspace,env=execution.environment,timeout_seconds=min(60,remaining),
        max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
    (out/(module+".json")).write_text(json.dumps(asdict(result),indent=2))
    results.append({"module":module,"succeeded":result.succeeded,"seconds":result.elapsed_seconds,
                    "peakRssBytes":result.peak_rss_bytes,"sourceDigest":hashlib.sha256(source).hexdigest()})
    print(module,result.returncode,round(result.elapsed_seconds,2),flush=True)
    return result
family=Path("src/ladon/lean/LadonRealBound.lean").read_bytes()
assert compile_module("LadonRealBound",family).succeeded
rules=(b"import LadonRealBound\n" if args.mode=="red" else
       Path("src/ladon/lean/LadonRealBoundComposition.lean").read_bytes())
assert compile_module("LadonRealBoundComposition",rules).succeeded
import sys
sys.path.insert(0,str(Path("tests").resolve()))
from test_real_bound_rules_lean import CASES,RULES,observer
for module,cases in CASES.items():
    namespace="RuleExamples" if module=="PositiveRules" else "RuleControls"
    names=[f"{namespace}.{name}" for name in cases]+[f"Ladon.RealBound.{name}" for name in RULES]
    source=Path(f"tests/fixtures/real_bound_rules/{module}.lean").read_bytes()+observer(names).encode()
    result=compile_module(module,source)
    if args.mode=="red":
        assert not result.succeeded and ("TransferAt" in result.stdout or "scaled_bound_mono" in result.stdout)
    else:
        assert result.succeeded,result.stdout
        frames=[json.loads(line.removeprefix("LADON_REAL_RULES ")) for line in result.stdout.splitlines()
                if line.startswith("LADON_REAL_RULES ")]
        assert len(frames)==1 and [row["declaration"] for row in frames[0]]==names
        assert all(set(row["axioms"])<={"propext","Classical.choice","Quot.sound"} for row in frames[0])
        (out/(module+"-axioms.json")).write_text(json.dumps(frames[0],indent=2))
(out/"RESULTS.json").write_text(json.dumps(results,indent=2))
