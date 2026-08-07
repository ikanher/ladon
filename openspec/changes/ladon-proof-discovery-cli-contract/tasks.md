## 1. Public CLI Contract

- [ ] 1.1 Add the proof-discovery command family to the ordinary Ladon parser and installed entry point without caller-specific behavior.
- [ ] 1.2 Define shared request validation, exit classes, report-version metadata, and text/JSON output contracts for every proof-discovery command.
- [ ] 1.3 Add compact terminal renderers whose limits are explicit and whose JSON counterparts preserve machine-actionable evidence.

## 2. Documentation And Compatibility

- [ ] 2.1 Update command help, user documentation, and the maintained Ladon skill to use only supported flags and canonical output selectors.
- [ ] 2.2 Add an automated stale-flag scan covering `--skip-build`, legacy `--output-json`/`--output-text`, and report-version examples.
- [ ] 2.3 Preserve existing analyzer commands and document migrations for any superseded proof-discovery preview syntax.

## 3. Verification

- [ ] 3.1 Test source-checkout and freshly installed-wheel help, parsing, text/JSON parity, clean streams, and stable exit behavior.
- [ ] 3.2 Strictly validate this change and run the focused CLI and documentation contract gates.
