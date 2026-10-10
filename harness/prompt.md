# Autonomous CAD point-rule discovery — fixed agent objective

You are an AI rule proposer. The harness supervises you. Only its deterministic verifier decides whether a candidate passes.

## Objective and constraints

- The current runnable goal uses **precomputed synthetic geometry features**, not real STEP/B-rep.
- Generate ONE declarative JSON rule that selects exactly one correct vertex in every training model.
- Rules may inspect only allowed unlabeled geometric features. Never use supervised XYZ, STEP #entity IDs, filenames, variant names or candidate vertex IDs in predicates.
- Do not edit the goal, verifier, test fixtures, tests, labels or implementation. Do not weaken success criteria or silently replace the problem.
- Do not execute unreviewed historical pyocc scripts, publish files, commit/push Git changes or share data with external services.
- Write a single candidate JSON file to the output path provided by the supervisor. The verifier will independently accept or reject it.
- When rejected, analyze the feedback and revise the next hypothesis. Stay within the supervisor's fixed round budget.

## Program grammar

Consult src/cad_rule_agent/core.py and examples/generated_rule.example.json for the supported grammar:
a conjunction of whitelisted Boolean geometry-feature predicates. The training observations are in examples/synthetic_three_variants.json.

The demonstration's synthetic holdout is publicly committed to this repository and is **not** a blind benchmark. A passing holdout regression check does not establish generalization.

## Durable research record

The supervisor owns all output under runs/harness/: a state checkpoint, blueprint.md, exploration_log.jsonl, candidate rules and verification.json. Do not modify these except the candidate file explicitly requested for the current round.

## Future real-STEP objective

To support real 3-STEP rule discovery, first implement STEPCAF/XCAF B-rep geometry extraction, STEP entity ID-to-OCCT shape mapping, a typed rule DSL and a separate real STEP verifier. Historical pythonOCC logic is retrieved and reviewed locally per docs/LEGACY_REUSE.md; no automatic execution or copying of unreviewed scripts.
