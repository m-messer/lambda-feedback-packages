# Phase 0: Repo scaffolding

Applies to all packages. No behaviour changes: the parity check shows 3221/3221 probes unchanged.

## Layout

- [x] Move each package to `src/` layout under the namespace: `slr_parsing/slr_parsing/*.py` → `slr_parsing/src/lambdafeedback/slr_parsing/*.py`, and likewise for `criteria`, `expression_parsing`, `units` and (until Phase 2) `evaluation_result`.
- [x] Add `py.typed` to each package. There is no `lambdafeedback/__init__.py`, since the PEP 420 namespace depends on its absence.
- [x] Update imports to `lambdafeedback.<pkg>`; all 468 carried-over tests pass.

## Packaging (Poetry)

- [x] Per-package `pyproject.toml`: PEP 621 `[project]`, build backend `poetry-core>=2`, `[tool.poetry] packages = [{ include = "lambdafeedback/<pkg>", from = "src" }]`, `requires-python = ">=3.11"`.
- [x] Sibling deps by name in `[project.dependencies]`, enriched in `[tool.poetry.dependencies]` with `{ path = "../<pkg>", develop = true }`.
- [x] `poetry build` each package: the wheel `METADATA` has only plain requirements, with no path references. All four wheels installed together in a fresh venv merge under one `lambdafeedback` namespace (smoke test: `2 kg m/s^2` → `2 | kilogram metre/second^2`).
- [x] Root `pyproject.toml` with `package-mode = false`. The dev group holds all packages as path/develop deps plus `pytest`, `pytest-cov`, `ruff` and `mypy`; `poetry.lock` is committed.
- [x] `lf_toolkit` pinned to `ae52fa6`, as a **dev-only** dependency (Phase 2 decision; see [upstream-lf-toolkit.md](upstream-lf-toolkit.md)).

**Deviation:** `expression_parsing`, `units` and the root dev env declare `requires-python = ">=3.11,<3.13"`. latex2sympy2 (both the PyPI release and the lambda-feedback fork) pins `antlr4-python3-runtime` 4.7.2, which imports `typing.io`, removed in Python 3.13. `slr_parsing` and `criteria` pass on 3.13. Lifting the cap needs latex2sympy regenerated with a newer ANTLR, which is upstream work.

## Tooling

- [x] ruff (root): `target-version = "py311"`, line length 120, rules `E,F,W,I,UP,B,SIM,RUF,N`, with `RUF001-003` ignored (ambiguous unicode is the input domain). Packages sit in `extend-exclude` until their phase lands.
- [x] mypy (root): `files` lists what is covered so far (`tools/parity`). Packages not yet refactored use `follow_imports = "silent"`. The per-package strictness settings and the `latex2sympy2` override are added in each package's phase.
- [x] pytest `filterwarnings = error::SyntaxWarning` (plus `error::DeprecationWarning` for our modules): added at the end of Phase 4, once every package's invalid-escape regexes were fixed.
- [x] `.github/workflows/ci.yml`: matrix Python 3.11/3.12 (3.13 excluded, see above). `pipx install poetry` → `poetry install` → `ruff check` → `ruff format --check` → `mypy` → `scripts/test.sh`.

**Deviation:** tests run **per package** (`scripts/test.sh`), not in one pytest session. Every package has a `tests` package, and one pytest process can't import two packages with the same name (`--import-mode=importlib` breaks the tests' relative `_fixtures` imports).

## Docs

- [x] Rewrite `README.md`: Poetry install, new import paths, dependency graph, parity check.
- [x] Add a "Refactor (stage 2)" section to `NOTES.md`.
- [x] Save the parity snapshot: `tools/parity/baseline.json` (3221 probes from `capture_v0_1.py` at commit `2d7db40`), with `check.py` and `expected_changes.json` to diff against it.
