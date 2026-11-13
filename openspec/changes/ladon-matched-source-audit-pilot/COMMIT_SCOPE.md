# Evidence commit scope

The pilot's source snapshots, registrations, reports, receipts and manifests are
preserved as recorded. Local `.lake` directories are excluded: they contain
regenerable Lake configuration binaries and dependency links to the donor
checkout. Their exclusion does not provide independent dependency replay or a
portable dependency closure. The recorded dependency metadata retains its
original scope and limitations. Existing frozen files have not been reformatted.
