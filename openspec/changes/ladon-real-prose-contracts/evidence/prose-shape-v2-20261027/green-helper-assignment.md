Green implementer: isolated Lean helper proposal only. Contract1902, rootkernel
probe1908/1911 (actualfiles under .codex/state/prose-shape-v2) and frozen11shape
acceptance tests/tests_real_prose_shape_v2.py (actualpath tests/test_real_prose_shape_v2.py)
are authority. Create green/ladon_prose_alias.lean in .codex/state/prose-shape-v2.
No production/test edits, no Lean execution/build. Rootownscompilerintegration.

Helper args [module,file,snapshot,target,requestFile,destination]. Copy bounded
Expr JSON renderer from src/ladon/lean/ladon_prose_observation.lean; unchanged
legacyhelper. Frontendelaborate trusted source snapshot (contains exact generated
def target:Prop); require localdefnInfo, declaredtypeProp/valueProp andownrange.
RequestJSON schema ladon-prose-alias-request-v1, keys schema,targets; max2targets.
Each target keys kind(input-order|output-bound),originPath(/propositionExpr/...),
roles object order/constant/bound integer source-prefixindices. Generic pathwalk
matchesExpr JSONconstructorpath app/0|1,forallE/body|type,lam/body|type etc; strips
mdata like renderer; enteringforall/lam BODY mustwithLocalDecl+instantiate1,
accumulateexact fvarprefix(inclunusedproof/instancevars). Selectedexpr hasallfvars
inprefix; rejectotherwise. Pathlength<=256tokens; prefix<=64binders.

Orderdiscovery bounded<=32headsteps. Return0ifexpressionisbaseorderfvar; stopat
HAdd.hAdd or Nat.add andinfer rightNatliteral(OfNat.ofNat Nat literal supported).
Unknown/symbolic/tooBig(>2^53-1) staysunresolved. Eachstep canheadBeta,zeta leading
letE,unfoldDefinition? once; no wholeProp unfold. Build canonicalbuiltinNat.add
base d, and prove exactEq viaEq.refloriginal. Kernel acceptanceforces source
additioninstance to builtin semantics; originalinstance remainsinoriginal/closure.
Outputbounddiscovery boundedheadstepsuntilHMul.hMul with6args,3carrierargs exactReal.
Build canonical product by REUSING observed first4args(type+instance) plus exact
sourceK,C fvars; do not synthesizeinstance. Wrongproduct operands mustfailkernel.

Certificate: equation←mkEq original canonical; closegoal with mkForallFVars scope
usedOnlyfalse; proof←mkLambdaFVars scope (mkEqRefl original) usedOnlyfalse. Serialize
original/canonical as closedLambda wrappers over EXACTSAME prefix, proof andgoal.
Verify noforeignfvars beforeclosure; closedexpressions nofvars/metavarsafterwards.
Use generateddefinition info.levelParams. Synchronous gate MUST be
(←getEnv).toKernelEnv.addDecl (debug.skipKernelTC.set {} false) (.thmDecl {...}).
Core.addDecl alone is asynchronouslyfakegreen(probe2). No needaddtheorem toCoreenv.

Output ALWAYSclosedkeys schema(ladon-prose-alias-worker-v1),helperVersion
(ladon-prose-alias-helper-v1),module,file,target,leanVersion,status(checked|partial|
unavailable),propositionExpr(nullwhenunavailable),results[],importedModules[],
compiledModulePaths[],reason(nullunlessunavailable). Same fulloriginalvalueJSON
forPythonexactcomparison; paths/imports sourcedfromsourceenv.header as oldhelper.
Successcert exactkeys kind,originPath,state(checked),lossLiteral(nat|null),original,
canonical,goal,proof,kernelCheck(synchronous),scopeCount,levelParams(arraystrings).
Unresolvedcert exactkeys kind,originPath,state(unresolved),code,message. Kernel
reject/unfoldbudget/nonnumeric/rendererlimit staysper-targetunresolved. statuschecked
onlyifall2targetschecked; partialotherwise. Output8MiB cap beforewrite.

Use source references/localLean4.32.1APIs. Rootprototypevalidatedrealproduct/scoped
instance/unusedproofclosure in ScopedKernelProbe. Mainreturnedfilesproposal only;
neverclaimcompiledgreen. Canonicalboard .codex/state/ultra-proof-contract.sqlite3
legacyhelper scripts/ultra_code_bb.py mutationsenvcanonicalfullpath. Author
/root/prose_alias_green_57 roleimplementer Luna medium. Poststarted/findings/final
onboard cursor1911. Soft8min hard12min. No online. Return exact risks, file,
noexecutionclaim. Rootimplementation of Pythonrecognition/history proceedsparallel.
