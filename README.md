# Tabularium

> *Tabularium* — the Roman state archive, built 78 BC on the Forum.
> This is the personal equivalent: a pipeline for managing a lifetime of digital files.

## What this is

**Crispr-NiE** (Non-integer Edition) is a modular library cleanup pipeline for organizing
flat folders of files into indexed, grouped, certified libraries — one file type at a time.

The system processes `.json`, `.py`, `.txt`, `.md`, `.sh`, and other file extensions
through staged pipeline passes: snapshot → repair → rename → consolidate → certify.

## Certified Libraries

| Library | Files | Groups | Status |
|---------|-------|--------|--------|
| `.json` | 224   | 29     | Certified |
| `.py`   | 132   | 42     | Certified |
| `.txt`  | 210   | 30     | Certified |
| `.md`   | 2,604 | 26     | In Progress — 1,674 VETTING (554 rescued) |
| `.sh`   | 70    | —      | Consolidate done |

## Pipeline Scripts

| Script | Purpose |
|--------|---------|
| `crispr_run.py` | Orchestrator — runs all stages for any extension |
| `crispr_snapshot.py` | Stage 0/4: before/after snapshot + certification diff |
| `crispr_repair.py` | Stage 1: JSON repair |
| `crispr_repair_py.py` | Stage 1: Python syntax repair |
| `crispr_rename.py` | Stage 2: copies→copies/, versions→versions/, dedup |
| `crispr_consolidate.py` | Stage 3: JSON groups + master index |
| `crispr_consolidate_py.py` | Stage 3: Python groups + master index |
| `crispr_consolidate_txt.py` | Stage 3: .txt groups + master index |
| `crispr_consolidate_md.py` | Stage 3: .md groups + master index |
| `crispr_analyze_txt.py` | VETTING analyzer — prefix clusters |
| `crispr_titlemancer.py` | Title extractor + group-prefix rename proposer |
| `crispr_ai_title.py` | AI title extraction cache layer (agy/Gemini) |
| `crispr_salvage_txt.py` | Detects .txt files that belong in other libraries |

## Usage

```bash
python3 pipeline/crispr_run.py .txt
python3 pipeline/crispr_run.py .md --dry-run
python3 pipeline/crispr_run.py .md --stage 3
```

## Missions Wing

The `missions/` folder is the meta-layer — directives, commissions, and save points
that guide the pipeline itself.

- **SENESCHAL_Protocol.md** — recurring steward duties + active log
- **FIRST_LIBRARY.md** — save point narrative for the .txt library certification
- **INDEX.md** — current library status and active missions

## Environment

Designed for Termux on Android (Pixel 8a). Python 3.13, no external dependencies.
Library path: `~/pixel8/library/`

---

*Named after the Tabularium (78 BC), the Roman state archive on the Forum.*
