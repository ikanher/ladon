# Design

The helper remains parser-first. Instead of invoking the full Lean frontend, it
updates the `ParserModuleContext` after parsing `open` commands.

For `open scoped Ns`, the helper resolves each namespace using the current
environment, current namespace, and open declarations, then activates scoped
parser extensions through `Parser.parserExtension.activateScoped`.

For plain `open Ns`, it also adds the corresponding simple open declaration,
matching the parser extension behavior Lean uses for parser contexts.

This fixes imported scoped notation such as `𝓝[>]` after `open scoped Topology`
while avoiding the hazards of elaborating large theorem files inside a review
extractor.
