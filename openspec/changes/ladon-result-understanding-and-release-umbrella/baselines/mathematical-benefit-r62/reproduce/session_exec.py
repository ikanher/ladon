"""Outside recorder: preserve the native event stream without reader diary work."""
from pathlib import Path
import json,subprocess,sys,time
out=Path(sys.argv[1]);argv=json.loads(Path(sys.argv[2]).read_text())
with (out/'events.jsonl').open('xb') as raw,(out/'event-arrivals.jsonl').open('x') as arrivals,(out/'stderr.txt').open('xb') as stderr:
 process=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=stderr)
 for number,line in enumerate(process.stdout,1):
  raw.write(line);raw.flush();arrivals.write(json.dumps({'line':number,'observedUnixNanoseconds':time.time_ns(),'bytes':len(line)})+'\n');arrivals.flush()
 code=process.wait()
print(json.dumps({'readerProcessExitCode':code,'eventsBytes':(out/'events.jsonl').stat().st_size}))
raise SystemExit(code)
