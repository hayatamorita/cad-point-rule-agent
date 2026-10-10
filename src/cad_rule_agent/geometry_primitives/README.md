# Reviewed geometry primitive shelf

This directory is the **destination** for primitives ported from historical pyocc snippets. Only reviewed, deterministic, typed OCCT geometry functions with tests should be included here.

Upstream source examples are indexed in `data/legacy_pyocc/` (local only). Run `cad-rule legacy-index`, `cad-rule legacy-search`, then `cad-rule legacy-promote` to identify candidates and produce a review-required migration proposal. Do NOT import or execute old modules directly.

For each migrated primitive, document the source file and SHA-256, version/binding requirements, function signature, units, coordinate-frame assumptions, geometric tolerances, ambiguity handling, related DSL operators and tests.

**No legacy geometry primitive has been approved/ported yet.** Real OCCT integration is a future milestone.
