# tabularium Development Patterns

> Auto-generated skill from repository analysis — corrected 2026-07-17 against the actual `pipeline/` and `tools/` code (the original auto-generated draft assumed a Python package that does not exist here).

## Overview
This skill documents the real development patterns used in the `tabularium` repository: a collection of standalone Crispr-NiE pipeline scripts (`pipeline/crispr_*.py`) plus launcher shell scripts (`tools/*.sh`), not a Python package.

## Coding Conventions

### File Naming
- Use **snake_case** for all file names.
  - Example: `crispr_snapshot.py`, `crispr_analyze_txt.py`

### Import Style
- Every script uses **absolute, standard-library-only imports**. There is no package structure, no `__init__.py`, and no relative (`from .x import y`) imports anywhere in `pipeline/` or `tools/`.
  - Example:
    ```python
    import json
    from pathlib import Path
    ```

### Function Naming
- Functions are **snake_case** throughout (`do_copies`, `do_dedup`, `unique_path`, `extract_title`).

### Export Style
- There are **no module-level exports**. Each script is a standalone CLI entry point:
  ```python
  if __name__ == "__main__":
      main()
  ```
  Nothing defines or relies on `__all__`.

### Commit Patterns
- Commit messages are freeform, full sentences describing the change and its motivation — not short fragments.

## Workflows

The real workflow is the 5-stage Crispr-NiE pipeline documented in `pipeline/CRISPR_PROCEDURE.md`:

    python3 pipeline/crispr_run.py .json              # run all 5 stages
    python3 pipeline/crispr_run.py .py --dry-run      # preview only
    python3 pipeline/crispr_run.py .md --stage 3      # single stage
    python3 pipeline/crispr_run.py .sh --from 2       # resume from a stage

Stages: `0 snapshot (before)` → `1 repair` → `2 rename` → `3 consolidate` → `4 snapshot (compare/certify)`. Each library extension (`.json`, `.py`, `.md`, `.sh`, `.txt`) has its own adapter registered in `pipeline/crispr_run.py`'s `ADAPTERS` map.

`tools/navigo1.sh` is the interactive/non-interactive menu launcher for the `.md` library specifically (`bash tools/navigo1.sh <choice>`).

## Testing Patterns

- **There is no test suite in this repository** — no `tests/`, no `*.test.*`, no `pytest`/`unittest` usage. Correctness is verified with `python3 -m py_compile <file>` (syntax) and the pipeline's own before/after snapshot diff (behavioral), not a test framework.

## Commands

There are no custom slash commands defined for this repo. The real commands are the pipeline stages above, invoked directly via `python3 pipeline/crispr_run.py <ext>`.
