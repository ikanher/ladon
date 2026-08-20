# Design

Edges point from importer to imported modules. For each known chosen root:

1. read `edges[root]`;
2. for each direct import, follow outgoing edges from that import;
3. count reachable modules including the direct import;
4. emit the top rows by descending closure size.

This answers "which direct import pulls the most known module context?" without
changing the module graph itself.

Rows above the standard hotspot threshold are also promoted into the findings
section so reviewers see closure causes before raw graph details.
