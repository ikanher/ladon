import hashlib,json,os,shutil,sys,time
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process
p=Path('openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/source-pair-20261018');repo=Path('/home/codex/projects/lean/matrix-factorization');start=json.loads((p/'PRE-MATCH-FREEZE.json').read_text())['monotonicFreeze'];deadline=start+90
source=repo/'Mf/DP/PoissonFixedEpochEpochUniformDomain.lean';before=source.read_bytes();shutil.copyfile(source,p/'formal-source.lean')
manifest={str(f.relative_to(repo)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [source,repo/'lean-toolchain',repo/'lake-manifest.json',repo/'lakefile.toml'] if f.is_file()}
command=[sys.executable,'-m','ladon.entrypoint','investigation','contract','produce','--channel','formal','--root',str(repo),'--file','Mf/DP/PoissonFixedEpochEpochUniformDomain.lean','--module','Mf.DP.PoissonFixedEpochEpochUniformDomain','--declaration','Mf.DP.poissonFixedEpochCalibratedPrivacyVariance_gt_fullBatch_of_epochUniformSignal','--timeout-seconds','30','--max-rss-mib','12288','--output',str(p/'formal-snapshot.json')]
remaining=min(30,max(0,deadline-time.monotonic()));assert remaining>0
process=run_bounded_target_process(command,cwd=Path.cwd(),env={**os.environ,'PYTHONPATH':'src:tests'},timeout_seconds=remaining,max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
(p/'formal-stdout.txt').write_text(process.stdout);(p/'formal-stderr.txt').write_text(process.stderr)
receipt={'command':command,'cwd':str(Path.cwd()),'returnCode':process.returncode,'elapsedSeconds':process.elapsed_seconds,'timedOut':process.timed_out,'memoryLimited':process.memory_limited,'outputLimited':process.output_limited,'peakRssBytes':process.peak_rss_bytes,'limits':{'timeoutSeconds':remaining,'maxRssBytes':12*1024**3,'maxOutputBytes':8*1024**2},'experimentDeadlineMonotonic':deadline,'sourceMetadataBefore':manifest,'sourceBytesUnchanged':source.read_bytes()==before}
assert receipt['sourceBytesUnchanged'];(p/'formal-process.json').write_text(json.dumps(receipt,indent=2))
summary={'status':'incomplete','sourcePairGate':'not-established','productionChanged':False,'proseFreezeBeforeFormal':True,'frontierAttempted':False,'reason':'A source-extracted supported contract is required; no replacement authored contract or unsupported-to-Nat conversion is allowed.','cumulativeWallSeconds':time.monotonic()-start,'budgetSeconds':90,'wholeMethodAuthority':'none','mathematicalFalsity':'not-established','heldOutCAdmittedCases':0,'detectionBenefit':'unmeasured'}
if (p/'formal-snapshot.json').exists():
 snapshot=json.loads((p/'formal-snapshot.json').read_text());summary.update(formalStatus=snapshot['status'],formalResiduals=snapshot['residuals'],formalContractAvailable=snapshot['contract'] is not None,actualStatementObserved=snapshot['observation'] is not None)
 if snapshot['contract'] is not None:summary['status']='supported-candidate-awaiting-propagation'
else:summary.update(formalStatus='resource-stop-or-worker-failure',formalContractAvailable=False,actualStatementObserved=False)
(p/'RESULT.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
