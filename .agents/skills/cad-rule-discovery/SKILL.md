---
name: cad-rule-discovery
description: Discover a shared deterministic geometric rule that selects homologous labeled points in three CAD STEP variants using topology, program synthesis and verification.
---

# CAD Rule Discovery Skill

Read `AGENTS.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_TESTS.md`. Never pretend M0 synthetic feature graphs are genuine STEP imports.

## Procedure
1. Confirm approved CAD data access. Validate three STEP paths, each corresponding target point, coordinate frames, vehicles axes, unit conversions and tolerances.
2. Read assembly-aware geometry using supported STEP/XCAF importer, preserving part instances, frame transforms and topology. If importer is not implemented, build it first.
3. Enumerate candidate vertices and compute geometry/topology features without access to target labels.
4. Resolve human target labels uniquely to candidates for supervision only; reject ambiguous/missing labels.
5. Generate predicates true for all target vertices. Include **all non-target vertices as negatives** so that useless shared predicates do not count as success.
6. Search shortest consistent predicate combinations, then richer typed hierarchical traversals and reference selections.
7. Execute the EXACT SAME rule on every variant, requiring one candidate matching each training label within the stated tolerance.
8. On a counterexample, refine the grammar, reference selection and search. Do not insert per-type branching or memorize coordinates.
9. Rank by rule simplicity, decision margin and geometric perturbation robustness. Test fourth type without a label when provided.
10. Export serializable DSL, human explanation, traces, test data provenance and failure diagnostics. Never claim universal proof based on three samples.

## Current prototype
```bash
python -m unittest discover -s tests -v
cad-rule synthesize --dataset examples/synthetic_three_variants.json --output results/rule.json
cad-rule apply --model examples/synthetic_unseen_variant.json --rule results/rule.json
```
This only verifies precomputed synthetic Boolean features. It does NOT process STEP until M1/M2 are implemented and tested.

MCP is optional and must use the tested Python core rather than replacing it.
