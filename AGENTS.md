# Instructions for coding agents

## Mission
Build a robust geometric/topological program-synthesis system. Given three STEP variants of the same automotive component and one supervised target point per variant, output **one interpretable deterministic rule** selecting the homologous point in all three. Preserve assemblies and coordinate frames.

## Mandatory reading
Read README.md, docs/PRD.md, docs/ARCHITECTURE.md, docs/ACCEPTANCE_TESTS.md, docs/ROADMAP.md before editing. Report any discrepancies between design docs and implemented behavior.

## Hard constraints
- Never use labels during inference, and apply exactly one shared rule to every variant.
- Do not branch by filename, variant/model ID, arbitrary part name, persistent TopoDS subshape index, or memorized absolute coordinates.
- Labels are supervision-only, not geometric rule features. Do not leak labels into feature extraction.
- Explicitly specify vehicle/world frame, axis definitions, unit conversions, shape transforms and metric/angular tolerances.
- Return errors for zero/ambiguous/unsupported selections; never silently choose the first.
- Start with a typed, deterministic, side-effect-free geometric DSL. An LLM may propose programs, but shall not be the authority for geometric results.
- Separate exact topological predicates from approximate numeric tests and report margins.
- Three training examples do NOT prove generalization to arbitrary unseen variants.
- Proprietary/real STEP files remain locally in an approved ignored directory; do not upload to GitHub, CI, logs or LLM endpoints without explicit approval.
- Keep tests, reproducible fixtures and headless CLI with every implementation milestone.

## Implementation sequence
1. Run M0 pure-Python synthetic tests.
2. Implement OCCT STEP reader (prefer XCAF/STEPCAFControl for assemblies), local/world transforms, run-local handles and structured errors.
3. Build Solid/Face/Wire/Edge/Vertex graph with ownership, incidence, adjacency, curve/surface types and geometric measures.
4. Enable robust human label matching in specified frames (unambiguous Vertex snapping).
5. Compute features on unlabeled geometry: relative directions, closed/inner loops, parallelism, orthogonality, distance ratios and reference-edge relations.
6. Mine predicates that hold for all positive examples and reject all other candidate vertices. Improve simple exact set-cover search with ILP or branch-and-bound.
7. Add a compositional typed traversal DSL and a CEGIS/beam-search synthesizer. Reference geometry must be selected by its own model-independent rule.
8. Verify unique selection for each training variant, rank by simplicity, margin, robustness; test unseen fourth type without labels.
9. Produce human-readable explanations, serialized rules and reproducible diagnostics.
10. Add FreeCAD click-label UX; add MCP adapter only after a stable Python library/CLI exists.

## Quality gates
- `python -m unittest discover -s tests -v` succeeds.
- No silent success on missing, multiple or unsupported target candidates.
- Tests distinguish synthetic feature-JSON support from **actual STEP import**.
- New code must include fixtures/tests and explicit limitations.
- If real STEP samples are unavailable, use generated public B-rep/STEP test fixtures; never invent real CAD accuracy.

## Delegation
Commit small reviewable milestones, explain architectural choices and exact test commands. Preserve this specification for future coding agents.
