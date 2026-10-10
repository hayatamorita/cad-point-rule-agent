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
4. Map human-supplied STEP entity IDs (CARTESIAN_POINT/VERTEX_POINT) through STEP reader model entities into TopoDS_Vertex or explicit geometry; reject missing/ambiguous mapping.
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

## Standard supervised STEP input location
When authorized real STEP datasets are available, read `data/training/README.md` and `data/training/labels.example.json`. A user puts `type_a.step`, `type_b.step`, `type_c.step`, and a locally copied `labels.json` with the target `entity_id` for each case together under `data/training/`. The label schema is version 2; the entity ID can be an integer such as `118` or text `"#118"`. `cad-rule check-inputs` currently reads STEP DATA entities and verifies that labeled IDs are `CARTESIAN_POINT` or `VERTEX_POINT`; it does not build OCCT B-rep geometry, distinguish assembly occurrences, or synthesize STEP rules. A geometry-point entity may not correspond to exactly one B-rep vertex. Never infer semantic identity from numbers across different STEP files. Do not alter this convention without updating the docs, tests and validator. Files with real CAD and labels must stay out of source control.

## STEP label principle
The STEP #entity number identifies the supervised target **only within its source file**. Labels MUST be mapped to geometric/topological nodes through the STEP transfer process, not converted to a hard-coded cross-variant ID rule. For `CARTESIAN_POINT`, handle zero/multiple matching topological vertices explicitly; `VERTEX_POINT` is the preferred unambiguous label for topological vertices, subject to assembly instance mapping.

## Reuse historical pythonOCC code before inventing geometry primitives
- User places historical Python scripts recursively under `data/legacy_pyocc/`, never commit or upload these scripts without separate authorization (repository is public).
- **Mandatory at M1/M2/M3 feature planning:** run `cad-rule legacy-index`, then `cad-rule legacy-search --query '<target geometry semantics>'`; use indexed function name, file, line range, tags and call evidence to identify reusable logic.
- For each promising match, use `cad-rule legacy-promote --function-id '<relative.py::qualified.function>'` to generate a review-required proposal and provenance. Never automatically import/execute old code.
- Adapt/reimplement the useful geometric predicates/reference selectors into tested, deterministic functions under `src/cad_rule_agent/geometry_primitives/`, and register into the typed rule-synthesis DSL. Check data assumptions, OCCT version, transformations, tolerances, and behavior across three STEP variants. Do not propagate hardcoded file/STEP IDs/XYZ into learned rule.
- The current catalog is a static AST keyword index, **not** production semantic extraction or an automatic adapter. Consult `docs/LEGACY_REUSE.md` and report that limitation accurately.

## Public development vs. internal source-code migration

This repo is a PUBLIC generic-engine development repository. Historical user scripts under `data/legacy_pyocc/` remain Git-ignored **here**. The confirmed destination for version-controlled historical pyocc source is a separate company-internal GitHub repository, not the current public origin. Follow `docs/INTERNAL_MIGRATION.md` when the approved internal remote exists; change the legacy ignore rules **only in the separate internal working copy**. Never merge private-source commits back into this public history.

Agent access to legacy source is local or through an organization-approved internal runtime. The presence of historical `.py` code in a company GitHub repository is not authorization to send its content to outside cloud models.
