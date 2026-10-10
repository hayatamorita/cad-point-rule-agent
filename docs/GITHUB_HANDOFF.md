# GitHub & Coding Agent Handoff

Repository: https://github.com/hayatamorita/cad-point-rule-agent (main)

## Checkout
```bash
git clone https://github.com/hayatamorita/cad-point-rule-agent.git
cd cad-point-rule-agent
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Recommended Codex task
Read AGENTS.md and docs/PRD.md, ARCHITECTURE.md, ACCEPTANCE_TESTS.md and ROADMAP.md. Confirm M0 synthetic tests. Implement M1 with a real OCCT STEP/XCAF import, including generated nonproprietary sample STEP, preserved part/occurrence transforms, vertex/edge/face adjacency, and vertex label snapping. Add integration tests proving import→feature extraction. Do not describe synthetic JSON baseline as completed STEP functionality.

## Data handling
This repository is public. Keep actual/proprietary STEP, local private labels and generated geometry out of GitHub and remote AI services unless specifically authorized. Follow AGENTS.md and .gitignore.

## Training data: entity-ID labels (schema v2)
Place `type_a.step`, `type_b.step`, `type_c.step` locally under `data/training/`; copy `labels.example.json` to ignored `labels.json` and set `target_point.entity_id` in each case, for example `118` to identify STEP entity `#118`. Run `cad-rule check-inputs` to check DATA entity/type and simple VERTEX_POINT geometry reference. This does not yet map the entity to TopoDS_Vertex or implement real STEP rule synthesis.
