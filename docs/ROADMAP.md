# Agentic Coding Implementation Roadmap

## M0: Synthetic core (implemented)
- [x] Synthetic JSON point-feature model and label schema.
- [x] Whitelist-only deterministic Boolean DSL.
- [x] Exhaustive minimal conjunction/set-cover search using positive targets and all negative vertices.
- [x] Versioned rule JSON, synthesize/apply CLI, unique-match checking.
- [x] Synthetic holdout and unit tests.
- [ ] Better error explanations, diagnostics, property-based tests and schema tooling.

## M1: STEP ingestion + labeling — START HERE
- [ ] Choose pinned OCCT Python binding (pythonocc-core, OCP or FreeCAD Python) on the actual Mac/Linux environment; write installation/compatibility instructions.
- [ ] Implement STEPCAFControl_Reader and XCAF assembly occurrence traversal, with local/world/vehicle transforms.
- [ ] Enumerate Solid/Face/Wire/Edge/Vertex with B-rep containment/adjacency.
- [ ] Preserve units and precision; supply kernel-derived geometric measures and shape types.
- [ ] Create synthetic STEP fixtures and import/re-export integration tests.
- [ ] Register labels: coordinate-frame aware Vertex clicking/snapping; reject ambiguous or missing matches.

## M2: Real geometric features
- [ ] Vehicle-frame relative front/left/up, inner and outer closed loops, line/circle edge types.
- [ ] Pairwise parallel/orthogonal within explicit angular tolerance, adjacency, relative length/distance.
- [ ] Build unlabeled per-Vertex relational features from graph, connect to M0 synthesize/apply.
- [ ] Demonstrate one shared rule on 3 REAL STEP variants (user supplies authorized data) or generated STEP benchmarks.

## M3: Compositional rule synthesis
- [ ] Typed part/face/wire/edge/vertex traversals and model-independent reference-feature selectors.
- [ ] SAT/ILP / branch-and-bound feature cover and typed program enumeration with beam search / CEGIS.
- [ ] Complexity, selection margin and robustness ranking; serialize executable rule plus trace and diagnostics.

## M4: Human interaction + stronger validation
- [ ] FreeCAD click-label bridge / simple CAD GUI with 3 target points.
- [ ] Apply saved rule to an unseen fourth STEP without training labels.
- [ ] Geometric perturbation, edge split, export/reimport and rigid-transform benchmarks.

## M5: Optional integration
- [ ] Expand Skill with real stable CLI procedures.
- [ ] Expose tested CLI through an MCP adapter only if useful for external AI clients.
- [ ] Reproducible container environment, CI stages and release packaging.

## Immediate next Codex instruction
Read AGENTS.md and docs. Run M0 tests and synthetic CLI. Implement M1 in a focused pull request with an OCCT-generated public STEP fixture and import/transform tests, without breaking M0. Be explicit about unavailable actual production STEP cases.
