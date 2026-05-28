# Formula Gold Fixtures

- `421-pr.gold.json` and `812-pr.gold.json` are anchor gold snapshots generated from accepted canonical packages and used by the formula benchmark harness.
- `sp-control-absence.gold.json` is a shared control gold fixture for SP documents that are expected to contain no formula units.
- Gold files use `formula-gold.v1` and compare document-level counts plus per-formula fields by `formula_index`.
- Update anchor gold only after a deliberate visual/semantic review of the new canonical package, not after every parser tweak.