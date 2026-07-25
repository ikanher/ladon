# Large-Inventory Acceptance Evidence

## Authority

This is an installed-wheel preflight on the local host, not the normative
reference-cell result. The harness compared the host with the preregistered
Ubuntu 24.04, x86-64, four-core cell and recorded
`matchesReferenceJob: false`; it did not relabel local measurements as
reference evidence.

The selected candidate was the materialized Ladon directory, including
untracked implementation files, with source fingerprint
`sha256:be85b8119ade847782b5e167cb4a8f01740bce5e1e9b2e56c64aba72f8cc765d`.
The isolated wheel SHA-256 was
`2a20a59823561af54ada0a2f98b4636ab04bceae833c7717a154024edfa839a4`.
This evidence document and terminal run-state updates were written after that
measured snapshot and are not recursively part of its source fingerprint.

## Command

```bash
uv run --locked python scripts/large_inventory_gate.py \
  --candidate /home/codex/projects/ladon \
  --samples 3 \
  --output /tmp/ladon-large-inventory-final-r5.json
```

The gate built and installed the wheel in disposable storage, generated the
fixture through that installed wheel, and invoked only the ordinary `ladon`
CLI. JSON and text used independent per-sample caches.

## Fixture And Limits

- Fixture fingerprint:
  `sha256:c34835c339d553837c634befaaf4ac44c36b43c7cd5c400388c2fc33f0ea712a`
- 2,600 modules, 1,500,000 source lines, 100,000 declarations
- Cold wall: 20.0 seconds
- Warm wall: 5.0 seconds
- Peak RSS: 512.0 MiB
- Canonical JSON: 32,000,000 bytes
- Compact text: 500,000 bytes

## Per-Sample Results

| Temperature | Sample | Format | Wall (s) | Peak RSS (MiB) | Bytes | Discover (s) | Module DAG (s) | Serialize (s) | Cache |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| cold | 1 | JSON | 12.963872 | 121.672 | 429,506 | 11.043385 | 0.582359 | 0.914445 | 2,600 rebuilt |
| cold | 1 | text | 12.857586 | 121.125 | 10,366 | 11.889748 | 0.552419 | 0.000986 | 2,600 rebuilt |
| cold | 2 | JSON | 12.888691 | 122.480 | 429,508 | 11.051527 | 0.567621 | 0.864605 | 2,600 rebuilt |
| cold | 2 | text | 11.896047 | 123.145 | 10,366 | 10.899775 | 0.569285 | 0.001013 | 2,600 rebuilt |
| cold | 3 | JSON | 12.854858 | 121.305 | 429,508 | 10.962928 | 0.565666 | 0.888998 | 2,600 rebuilt |
| cold | 3 | text | 12.997498 | 122.656 | 10,366 | 11.922935 | 0.628237 | 0.001103 | 2,600 rebuilt |
| warm | 1 | JSON | 3.004949 | 123.043 | 429,521 | 0.917288 | 0.652809 | 0.982510 | 2,600 hits |
| warm | 1 | text | 2.098673 | 120.344 | 10,365 | 0.794102 | 0.720416 | 0.001019 | 2,600 hits |
| warm | 2 | JSON | 3.059816 | 122.902 | 429,532 | 0.762149 | 0.636238 | 1.184893 | 2,600 hits |
| warm | 2 | text | 1.790136 | 122.535 | 10,365 | 0.793499 | 0.552913 | 0.001034 | 2,600 hits |
| warm | 3 | JSON | 2.770428 | 123.062 | 429,530 | 0.712605 | 0.608287 | 0.959660 | 2,600 hits |
| warm | 3 | text | 1.945382 | 123.078 | 10,365 | 0.857333 | 0.627822 | 0.001018 | 2,600 hits |

All 36 supported local per-sample contracts passed. All six JSON runs shared
analysis fingerprint
`sha256:aaf408b33d318dcaa8ffa79e393711c3150e1fc2bae546e662043e59cf501f78`
and normalized report SHA-256
`sha256:57b45aa5863bf8521e690e58e7aecdd508d7d14fb00390ae5038b23d35a3d1fd`
over 428,349 normalized bytes. Every warm run reported 2,600 source-index
hits and zero rebuilds. The result artifact is 91,694 bytes with SHA-256
`addeee9bba957ef5f2fc427c407239d3ab923cc7a223f0296eeb5bfb9ac68415`.

## Contention Control

An immediately preceding `r4` sample overlapped an unrelated active
`codex`-owned Matrix-Factorization Lean build consuming about ten CPU cores.
Its cold discovery phases rose to about 20–21 seconds and all six cold wall
checks failed. That active work was not terminated. After it completed, the
same gate and candidate wheel produced the passing `r5` measurements above,
with cold discovery back in the 10.90–11.92 second band. The failed `r4`
artifact remains host-contention evidence and is not counted as a pass.

## Host Identity And Remaining Reference Work

- Ubuntu 24.10, x86-64
- CPython 3.11.15
- 12 available CPUs
- Linux process-tree RSS and descendant sampling supported

The expected reference identity remains Ubuntu 24.04, x86-64, four available
CPUs, on both supported Python minors 3.11 and 3.12. Required publication
evidence remains pending until that exact CI matrix records its own samples.
