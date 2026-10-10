# Legacy pythonOCC Logic Reuse

## Goal
Use earlier successful pyocc point/vertex selection code to discover reusable geometric/topological predicates, reference-selection techniques and traversal patterns for new STEP variants. Do not copy exact point coordinates, STEP entity IDs, filenames or occurrence-specific branches into the final rule.

## Storage
- Original scripts: `data/legacy_pyocc/<old-project>/*.py` (ignored locally; recursively indexed).
- Static catalog: `data/legacy_catalog/index.json` (ignored output).
- Migration proposals: `data/legacy_catalog/proposals/*.json` (ignored output).
- Reviewed, tested implementations: `src/cad_rule_agent/geometry_primitives/` (tracked; canonical and reusable).

The repo is public. Never publish confidential legacy source or share it with remote LLM/Cloud tools without user/organization approval.

## Implemented commands (M0.6)
```bash
cad-rule legacy-index
cad-rule legacy-search --query "front closed wire parallel edge"
cad-rule legacy-search --query "前方 閉ループ 平行 エッジ"
cad-rule legacy-promote --function-id 'project_01/old_find_point.py::find_parallel_edge'
```

- `legacy-index` recursively reads only user-supplied `.py` files, uses `ast.parse`, extracts functions/methods, call symbols, source hash, function line range, possible tags and DSL feature hints, and writes a JSON catalog.
- `legacy-search` rescans before ranking matches by query keywords. It returns file path, line range, tags and hints; nothing is executed.
- `legacy-promote` generates a **review-required** migration proposal with provenance and candidate feature mappings; it is *not* an executable plugin, and explicitly marks `approved: false`, `executed: false`.
- Corrupt, oversized (>2MB), or non-UTF8 scripts are reported as skipped. Notebooks/other languages currently unsupported.
- Catalog tags are heuristic; discoverability is not correctness. Code may depend on outdated bindings, mutable global state, external project modules or proprietary data.

## Mandatory future agent workflow
Before creating a brand-new geometry primitive:
1. Confirm permission to access local legacy scripts; do not send scripts/source excerpts to a remote LLM without permission.
2. Run `cad-rule legacy-index`. For target point's geometry/topology context, call `cad-rule legacy-search --query "..." `; inspect top matching functions *locally* using their source file + line numbers.
3. Determine whether useful pieces are: graph traversal (Part→Face→Wire→Edge→Vertex), predicate (parallel/closed/left), reference-geometry selector, candidate filter or final disambiguation.
4. Generate a review proposal via `legacy-promote` if useful; track original source SHA and name, but treat original source as untrusted.
5. **Port** the reusable algorithm into typed, side-effect-free OCCT primitives in `src/cad_rule_agent/geometry_primitives/`. Remove hard-coded STEP IDs, absolute XYZ, variant switches and application/UI effects. Normalize shapes, frames and tolerances.
6. Add unit/integration tests, including 3 training cases and unseen variant if available. Record provenance in primitive docstring/spec.
7. Only after review/tests: register the new primitive in the rule synthesis grammar, so the next run can actually discover/use it. Reject ambiguous targets.
8. Document why each old function was accepted/rejected, including limitations.

## Design distinction
Static index/search/proposal = **implemented now**.
Automated code interpretation, semantic equivalence checking, real STEP/OCCT feature extraction and hands-free reuse by a rule-synthesis agent = **planned**, NOT already implemented.

Even after porting, source ID numbers are supervision-only; the inferred rule must remain shared and independent of the training STEP entities.
