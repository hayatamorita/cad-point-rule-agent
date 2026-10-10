# CAD autonomous rule-discovery harness

This is a **CAD adaptation** of the objective → hypothesis → test → independent verification → feedback → journal → retry pattern discussed by Chen Yang. It is not a copy of his Julia/Lean code. Reference: https://chenyang.co/blog/math-research.html

## Supported today

- Fixed goal JSON and dataset fingerprints (prevent silent changes on resume)
- Repeated deterministic rule hypotheses with increasing search complexity
- Independent deterministic verification of all 3 *synthetic* labeled training models and one synthetic holdout
- Explicit rejection of wrong/ambiguous rules, bounded retries
- Persistent state and logs, resume with verification
- Optional Codex CLI proposer with verification-driven revisions (requires local Codex installation and authorization)

**Actual STEP parsing, OCCT feature generation, STEP entity-to-TopoDS mapping, and real-STEP rule verification are not yet implemented.** The synthetic holdout is public, not a blind benchmark.

## Try the working deterministic feedback loop

From the repository root, on Python 3.11 or newer:

~~~bash
bash harness/run.sh demo --max-rounds 8
bash harness/verify.sh runs/harness/demo/candidates/round_04.json
~~~

The demonstration tries 1-, 2-, 3- and 4-predicate hypotheses. The first three should fail to isolate all targets; the fourth should match the labeled targets in all three synthetic variants and the synthetic holdout.

The run writes:

~~~text
runs/harness/demo/
  blueprint.md
  exploration_log.jsonl
  state.json
  verification.json
  candidates/round_04.json
~~~

Repeating the command re-verifies the stored result. Use --run-dir with a different folder for a fresh run.

## Optional Codex-driven refinement

On a trusted Mac/Linux development environment with Codex CLI installed and authenticated:

~~~bash
bash harness/run.sh codex --max-rounds 4 --timeout-seconds 900
~~~

The supervisor invokes codex exec with workspace-write sandbox and the fixed harness/prompt.md. The agent proposes a candidate JSON; the supervisor independently checks it. A failed candidate's diagnostic is passed into the next round. Attempts stop after the user-specified finite budget. **This does not run in the background from ChatGPT; the command runs in the user's terminal.**

**Security limitation:** The Codex workspace-write sandbox can allow writes to repository files. Text instructions against goal/verifier modification are not a security guarantee against malicious behavior. Run on a trusted, isolated checkout, inspect diffs, and do not give this public project access to sensitive internal CAD code or data. Neither launcher automatically commits nor pushes.

## Verify any proposed rule

~~~bash
bash harness/verify.sh /path/to/rule.json
~~~

A passing report explicitly says verification_scope = synthetic_feature_graph_only and real_step_verified = false. A clean result does not prove correctness on STEP, or broad generalization.

## Next milestone: real CAD verifier

1. Import the STEP files and their XCAF assembly occurrences.
2. Resolve user-specified STEP #entity labels to unambiguous B-rep vertices/geometric points.
3. Compute relational features from CAD data, not the target labels.
4. Build and independently test a real STEP rule evaluator with zero/one/multiple-match reports.
5. Adapt the generator/verifier loop to a new, explicit real STEP goal profile. Only then can production CAD runs pass.
6. Search previous reviewed pyocc implementations under data/legacy_pyocc and port reusable primitives into the typed grammar (see docs/LEGACY_REUSE.md).

Run outputs remain ignored by Git.
