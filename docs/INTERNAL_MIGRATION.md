# Moving CAD Point Rule Agent to the company-internal GitHub

## Agreed workflow

- **Personal/public GitHub** (`hayatamorita/cad-point-rule-agent`): develop and test the generic CAD point-rule agent using public/synthetic material. Historical production pyocc source remains local and Git-ignored.
- **Company-internal GitHub** (future repository): host the permitted historical `.py` files and allow an authorized coding agent to discover, review and migrate reusable geometric logic into the common DSL.
- **Do not copy historical pyocc files or real automotive STEP data to the public repository.** Internal GitHub permission does not imply permission for public hosting or external cloud model processing.

## Safe migration procedure

Use a **separate local working directory** so internal branches and files never accidentally get pushed to the public repository.

```bash
# 1. Clone the public generic engine into a NEW directory.
git clone https://github.com/hayatamorita/cad-point-rule-agent.git cad-point-rule-agent-internal
cd cad-point-rule-agent-internal

# 2. Replace the push destination. This intentionally removes the public origin.
git remote remove origin
git remote add origin <APPROVED_COMPANY_INTERNAL_GITHUB_REPO_URL>

# 3. Verify the remote is the company-internal repository BEFORE any push.
git remote -v
git ls-remote origin

# 4. Edit .gitignore as shown below ONLY in this internal working copy.
# 5. Copy authorized historical scripts into data/legacy_pyocc/project_name/*.py.
# 6. Review tracked files; never indiscriminately add large/secret CAD or credentials.
git status --short
git add .gitignore data/legacy_pyocc
git diff --cached --stat
git diff --cached --check
git commit -m "chore: register approved historical pythonOCC source"
git push -u origin main
```

`<APPROVED_COMPANY_INTERNAL_GITHUB_REPO_URL>` is a placeholder to replace after the approved company repository exists. Do not execute the `git remote add` line with the placeholder unchanged.

### Internal-only `.gitignore` change

The public template deliberately includes:

```gitignore
/data/legacy_pyocc/**
!/data/legacy_pyocc/README.md
/data/legacy_catalog/
```

**In the internal repository only**, delete the first two lines and keep `/data/legacy_catalog/` ignored unless company policy explicitly calls for tracking review metadata.

Then `data/legacy_pyocc/**/*.py` becomes trackable (the normal `*.py[cod]` ignore rule excludes bytecode but **does not** exclude `.py` source).

Keep `*.step`, `*.stp`, `/data/training/labels.json`, secrets, logs and generated results ignored unless separately authorized under internal company policy. Prior to the first commit, inspect the diff for passwords, tokens, internal addresses and confidential inputs.

`git check-ignore -v data/legacy_pyocc/project_name/example.py` helps diagnose any remaining ignore rule.

## Agentic coding inside the company environment

Run the coding agent in an authorized environment with access to the internal repository and pyocc dependencies, then:

```bash
python -m pip install -e .
cad-rule legacy-index
cad-rule legacy-search --query "閉ループ 平行 エッジ"
python -m unittest discover -s tests -v
```

Proposed agent instruction:

> Read AGENTS.md, docs/LEGACY_REUSE.md and docs/ROADMAP.md. Before creating new CAD geometric predicates, inventory and search the historical pythonOCC source under data/legacy_pyocc. Identify reusable topology traversals, geometry predicates and reference-feature selectors. Create review-only migration proposals; port and test approved functions as typed, deterministic OCCT geometry primitives. Remove source-specific STEP entity numbers, type switches, fixed XYZ and hidden global state. Register verified primitives into the DSL only after actual STEP integration tests. Do not execute unreviewed legacy modules or send their source to external cloud services.

## What is already implemented and what remains

**Implemented:** local AST inventory; queryable function/API/geometry-tag catalog; review proposal generation; synthetic feature-graph rule synthesis; STEP `#entity` label verification.

**Not yet implemented:** automatic translation of historical source into tested geometry primitives, actual OCCT STEP-to-Vertex mapping, automatic use of promoted historical primitives during real STEP rule synthesis, real CAD rule discovery. These are subsequent coding-agent milestones (M1–M3).

## Important branching rule

Do not merge an internal branch containing old pyocc source back to this public GitHub repository. To share generic improvements publicly, create **new public-safe commits containing only reviewed, non-sensitive code** and verify the full pushed Git history does not include historical internal source.
