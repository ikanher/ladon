# Source digest transcription correction

During r03 packet preparation, the `subsample.tex` digest printed in
INTERPRETATION.md was found to contain a transcription error:

- Printed: `11223a25e22c97b4c57dd08fd231d53da8c1664430c40cecb97a8e0c6eb561bb`
- Actual retained and donor bytes: `11223a25e22c97b4c57dd08fd231d53da8c1664430c40cecb97a8c0e6eb561bb`

The countermodel's INPUTS.json, INPUT-VERIFICATION.json and MANIFEST.json already
record the actual digest, matching its retained `inputs/paper/theory/mu-dp/subsample.tex`
and the read-only donor at this check. The other two source digests match.
The original interpretation note and manifest are preserved. This is a digest-text
correction, not a source change, mathematical revision or new replay.
