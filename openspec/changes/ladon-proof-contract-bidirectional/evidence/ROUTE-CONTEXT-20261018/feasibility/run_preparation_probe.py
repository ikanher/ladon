import json,os,sys,time
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process
p=Path('.codex/state/proof-contract-analysis/route-context');r=json.loads((p/'request.json').read_text());m=json.loads((p/'measurement.json').read_text());r['deadlineMonotonic']=time.monotonic()+min(30,90-m['totalMeasuredSeconds']);r['limits']['timeout_seconds']=30
result=run_bounded_target_process([sys.executable,str(p/'preparation_probe.py')],cwd=Path.cwd(),env=os.environ,input_bytes=json.dumps(r).encode(),timeout_seconds=min(30,90-m['totalMeasuredSeconds']),max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
v={'returnCode':result.returncode,'elapsedSeconds':result.elapsed_seconds,'peakRssBytes':result.peak_rss_bytes,'timedOut':result.timed_out,'outputLimited':result.output_limited,'memoryLimited':result.memory_limited,'stdout':result.stdout,'stderr':result.stderr,'cumulativeMeasuredSeconds':m['totalMeasuredSeconds']+result.elapsed_seconds};(p/'preparation-measurement.json').write_text(json.dumps(v,indent=2));print(json.dumps(v));assert result.returncode==0 and not any((result.timed_out,result.memory_limited,result.output_limited)),v
