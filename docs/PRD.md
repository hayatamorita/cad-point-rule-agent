# Product Requirements Document — CAD Point Rule Synthesis

## Problem
Three STEP assemblies are variants of the same automotive component. A human labels the homologous point in each. Shapes may differ in dimensions, placement and topology. Find **one reusable executable geometric/topological selection procedure** such as: frontmost suitable part → inner closed loop → edge parallel to a selected reference edge → left endpoint.

**The task is program synthesis, not direct XYZ regression, template-specific branching, or retrieval of stored labels.**

## Inputs
- Three STEP files (extendable to N >= 3).
- One label per variant, initially a B-rep Vertex: 3D point, tolerance in mm, coordinate-frame identifier and occurrence context.
- Vehicle front/left/up reference basis or trusted metadata; don't assume global +X means forward.
- Explicit units (convert consistently to mm), model transforms and kernel precision.
- Optional negative selections and unlabeled fourth STEP for out-of-sample validation.

## Outputs
- One versioned, human-readable and machine-executable deterministic DSL rule.
- Exactly one selected target per training case, with its coordinates, distance to supervised label, candidate count, path/traversal trace and ambiguity diagnostics.
- Alternative valid programs ranked for complexity, margins and perturbation robustness.
- Explicit no-rule-found, no-match, ambiguous-point and unsupported-geometry errors.

## User stories
1. Select one desired point on each of three STEP files.
2. Run discovery and inspect the shared geometric rule and why it identifies each point.
3. Apply the stored rule to an unseen STEP, without providing a label.
4. Adjust coordinate frames and tolerances when source exports differ.
5. Export reproducible logs and engineering validation metrics.

## Hard acceptance
For models G_i, target p_i, tolerance epsilon_i, candidate set C_i(R):
`for every i: |C_i(R)| == 1 and distance(only(C_i(R)),p_i) <= epsilon_i`.
All 3 models must use the same code/R. Never use file names, IDs, raw coordinates of targets, unstable face/edge/vertex numbers or label-specific branching to select points.

## Current M0 implementation
A fully deterministic pure-Python prototype over **precomputed whitelisted Boolean features**, not a STEP parser. It performs exact minimum-conjunction enumeration and verification, exports a JSON rule, handles non-unique selections explicitly and tests three variants plus a holdout.

## Production scope
- Import via OCCT, retaining XCAF product occurrence hierarchy, units and transforms.
- B-rep geometry/topology graph: Part/Solid/Face/Wire/Edge/Vertex and relations.
- Point labels collected via GUI or JSON; match in correct frames without ambiguity.
- Geometric predicates: front/left/up, inner/outer closed wires, line/circle, endpoint, parallel/perpendicular, adjacency, normalized length, near/relative spatial properties.
- Typed compositional DSL; nested reference-edge/face selection.
- Rule mining via set cover/ILP, enumerative or beam search, counterexample-guided inductive synthesis.
- Robustness evaluation: rigid transforms, tolerance, export/reimport and edge splits; holdout models.
- CLI first, optional FreeCAD plugin and MCP wrapper later.

## Non-goals
- Recovering missing design intent or arbitrary sketch-only points omitted from STEP.
- General mathematical proof of universal correctness based on three examples.
- Whole-CAD parametric reconstruction.
- Cloud upload of proprietary files without authorization.

## Success criteria
Verified unique match across three training STEP variants with real geometry-derived predicates; a repeatable saved rule; explicit failure handling; and experimental generalization reports on never-labeled variants. M0 alone does **not** satisfy the production STEP criteria.
