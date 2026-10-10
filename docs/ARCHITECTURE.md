# Technical Architecture

## Pipeline
```text
STEP models + supervised point labels + vehicle frame
  → STEPCAFControl_Reader / XCAF assembly occurrences (planned)
  → B-rep geometry/topology graph (planned)
  → unlabeled candidate enumeration / feature computation (planned)
  → predicate mining and negative-candidate elimination
  → exact set-cover / ILP seed search
  → typed DSL enumeration + beam search / CEGIS
  → deterministic rule executor
  → 3-model verification / ambiguity diagnostics / robustness
  → JSON/Python rule export and holdout evaluation
```

The LLM proposes/refines hypotheses, but OCCT and a deterministic rule evaluator own the ground truth. Never execute arbitrary AI-generated Python inside the CAD core; evaluate a restricted typed AST/DSL and optionally export audited code.

## CAD geometry graph
Nodes: AssemblyOccurrence, Part, Solid, Shell, Face, Wire, Edge, Vertex, ConstructedPoint when supported.
Relations: owns, incident_to, bounds, connects, adjacent_to, on_closed_loop, parallel_to, orthogonal_to, nearest_to, same_plane_as and coordinate-frame transforms.
Attributes: point coordinates, face normals/areas/surface types, edge curve types/tangents/lengths, connectedness, relative directions and normalized dimensions.
Preserve separate assembly occurrences of a reusable part and their location transforms; topological ordinals are run-local implementation handles, **not persistent semantic IDs**.

Use OCCT TopExp/TopTools to enumerate B-rep subshapes and STEPCAFControl_Reader + XCAF to retain assemblies. Define relative 'front'/'left'/'up' in supplied vehicle frame, not guessed world coordinates.

## Label protocol
Each training point has XYZ, coordinate_frame and positive tolerance_mm. Convert units and apply occurrence transforms. Reject if zero or more than one Vertex lies within tolerance. During rule inference labels are never accessible.

If the selected point is not encoded as a STEP Vertex, support optional geometric construction DSL (midpoint, intersection, projection, center) only when the point is well defined by included geometry. Otherwise report unsupported.

## DSL
Use typed and pure operators such as:
```text
Parts(Model) -> Set[Part]
Faces(Part) -> Set[Face]
Wires(Face) -> Set[Wire]
Edges(Wire) -> Set[Edge]
Vertices(Edge) -> Set[Vertex]
Closed(Wire) -> Bool
Inner(Wire, Face) -> Bool
Parallel(Edge, ReferenceEdge, angleTolerance) -> Bool
LeftEndpoint(Edge, Frame) -> Vertex
Unique(Set[Vertex]) -> Vertex | Ambiguous
```
Reference edge itself must be selected with a model-independent subprogram. Do not use hidden target-derived reference geometry.

Example:
```text
Unique(LeftEndpoint(SelectEdge(
  ParallelTo(SelectReferenceEdge(SelectFace(...))),
  Edges(SelectInnerClosedWire(SelectFrontFace(SelectPart(...))))
)))
```

M0 implements only conjunctions of precomputed whitelisted Boolean Vertex features. It does not compute these features from STEP.

## Optimization formulation
Let target p_i belong to candidate set V_i for each model i. Consider label-consistent Boolean predicates q_j, and negative candidates v. Let a[j,v]=1 when q_j **eliminates** v. Find:
```text
min sum_j c_j*z_j
subject to sum_j a[j,v]*z_j >= 1  for every v != p_i
z_j in {0,1}
```
This is a set-cover / binary-integer program. For the current small whitelist, enumerating conjunctions by increasing length yields the exact minimum count. For hierarchical, parameterized CAD predicates, use typed enumerative program synthesis, branch-and-bound/ILP, beam search and counterexample-guided inductive synthesis (CEGIS).

Acceptance: `forall i: |R(G_i)|=1 AND dist(R(G_i),p_i)<=eps_i`.
Rank accepted rules by cost, angular/distance margin, behavior under perturbed dimensions and transforms, holdout performance. The objective cannot guarantee generalization from three examples.

## Robustness & security
- Missing feature is UNKNOWN, not equivalent to False.
- Test consistent rotation/translation of vehicle axes and solids, re-export and split edges.
- Include false positive/distractor vertices; matching a property shared by all positives is insufficient without rejecting negatives.
- Tolerances are explicit, numeric margins reported and model constraints validated.
- Restrict LLM outputs to DSL AST; do not exfiltrate raw CAD or company geometry to cloud services.
- Keep headless Python CLI independent of optional GUI and MCP adapters.
