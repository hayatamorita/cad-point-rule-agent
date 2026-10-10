# Acceptance Tests / Quality Gates

## Synthetic M0 (currently implemented)
1. Three labeled feature-graph variants admit one common conjunction matching exactly one target per variant.
2. Minimal conjunction length is 4 in provided fixture, with deterministic ordering.
3. Applying saved rule to a held-out synthetic model uses no label and returns unique `holdout_target`.
4. Ambiguous/missing target labels fail explicitly.
5. No-rule-found with too-small program budget fails explicitly.
6. A zero-match or multi-match application fails, never selects first candidate.
7. Missing attributes are UNKNOWN; negative predicates cannot match missing fields.
8. Unknown predicates, invalid units and nonfinite coordinates are rejected.
9. Coordinate frame mismatches fail explicitly.
10. Rule serialization round trips.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
cad-rule synthesize --dataset examples/synthetic_three_variants.json --output results/rule.json
cad-rule apply --model examples/synthetic_unseen_variant.json --rule results/rule.json
```

## M1/M2 actual STEP integration (NOT YET IMPLEMENTED)
- Programmatically generate simple public CAD solids containing face loops and line edges, write STEP, import again.
- Preserve XCAF assembly occurrence hierarchy and relative/world transforms and mm units.
- Check known analytic vertex coordinates, curve/surface types, incidences, adjacency and closed/inner loops.
- Detect missing constructible points and ambiguously labeled vertices.
- Ensure geometry predicates are computed from shape, not labels.
- Re-export and reorder entity indices to prove rules do not depend on subshape numbering.
- A selected point in a differently located assembly occurrence is correctly transformed to vehicle frame.

## M3/M4 nested rules and generalization (NOT YET IMPLEMENTED)
- Synthesize part → face → inner loop → parallel edge → endpoint using a typed grammar.
- Discover the reference edge via its own independent subrule.
- Counterexample-driven synthesis addresses false positives; respect search budgets and explain failures.
- Report unique candidate count, label distance, rule complexity, tolerance margins.
- Apply rule without labels on a fourth variant; test length/position changes, rigid transforms and edge splits.

## Confidentiality
- .gitignore excludes production STEP, raw CAD data and local private label files.
- No real STEP files sent to remote LLMs or CI without express authorization.
