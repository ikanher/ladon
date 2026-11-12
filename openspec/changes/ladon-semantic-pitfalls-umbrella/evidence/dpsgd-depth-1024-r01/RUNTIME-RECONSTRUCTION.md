# Experimental runtime reconstruction

Base production commit: `dec5fdec910320599a6541689b3990883f5350c4`. `runtime.patch` records the exact final experimental package differences against that commit. In a separate checkout of the base, apply the patch with `git apply runtime.patch` and use that checkout's `src` as PYTHONPATH. The local copied `runtime/` directory is excluded from Git. This does not reconstruct earlier attempts; their receipts and settings are historical evidence.
