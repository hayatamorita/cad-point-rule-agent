---
name: cad-rule-discovery
description: Discover a shared deterministic geometric rule that selects homologous labeled points in three CAD STEP variants using topology, program synthesis and verification.
---

# CAD Rule Discovery Skill

Read `AGENTS.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_TESTS.md`. Never pretend M0 synthetic feature graphs are genuine STEP imports.

## Procedure
1. Confirm approved CAD data access. Validate three STEP paths, each corresponding target STEP `#entity_id` (CARTESIAN_POINT or VERTEX_POINT), assembly occurrence ambiguity, vehicle axes, unit conversions and tolerances.
2. Read assembly-aware geometry using supported STEP/XCAF importer, preserving part instances, frame transforms and topology. If importer is not implemented, build it first.
3. Before defining new geometry predicates, consult local historical pyocc code using `cad-rule legacy-index` and `cad-rule legacy-search --query "<desired point's geometry relations>"`. Review relevant source functions locally and use `cad-rule legacy-promote --function-id '<file.py::function>'` to create a migration proposal. Do not execute historical scripts; port reviewed algorithms into tested primitives and then register them in the typed DSL (registration not yet implemented).
4. Enumerate candidate vertices and compute geometry/topology features without access to target labels.
5. Resolve each training STEP entity ID to CAD geometry/topology and an unambiguous model node for supervision only (M1, not implemented); reject zero/multiple matches. Never use STEP entity IDs as rule predicates.
6. Generate predicates true for all target vertices. Include **all non-target vertices as negatives** so that useless shared predicates do not count as success.
7. Search shortest consistent predicate combinations, then richer typed hierarchical traversals and reference selections.
8. Execute the EXACT SAME rule on every variant, requiring one candidate matching each training label within the stated tolerance.
9. On a counterexample, refine the grammar, reference selection and search. Do not insert per-type branching or memorize coordinates.
10. Rank by rule simplicity, decision margin and geometric perturbation robustness. Test fourth type without a label when provided.
11. Export serializable DSL, human explanation, traces, test data provenance and failure diagnostics. Never claim universal proof based on three samples.

## Current prototype
```bash
python -m unittest discover -s tests -v
cad-rule synthesize --dataset examples/synthetic_three_variants.json --output results/rule.json
cad-rule apply --model examples/synthetic_unseen_variant.json --rule results/rule.json
```
This only verifies precomputed synthetic Boolean features. It does NOT process STEP until M1/M2 are implemented and tested.

MCP is optional and must use the tested Python core rather than replacing it.

For implementation details and confidentiality constraints, read `docs/LEGACY_REUSE.md`. Historical source is excluded from the public GitHub repository. A catalog match does not imply successful semantic reuse: only reviewed, migrated, tested geometry primitives may participate in the future synthesizer.

## Iterative research harness

Read `harness/README.md` and `harness/prompt.md`. Before attempting real CAD rules, confirm the synthetic harness works with `bash harness/run.sh demo`. Use `bash harness/verify.sh PATH` to independently inspect candidates and `runs/harness/*/exploration_log.jsonl` to understand rejected hypotheses. An opt-in Codex CLI loop is available on trusted machines using `bash harness/run.sh codex`. Never bypass verification, weaken tests or pretend the current synthetic-only harness validates STEP.
