# Crispr-NiE Library Procedure
Version 1.0 — 2026-07-07

The Crispr-NiE system treats each library folder as a single unified document — the
`__init__.py` concept. Each pass is reversible (audit trail) and non-destructive until
explicitly confirmed.

---

## Phases

### Phase 0 — Before Snapshot
Capture baseline: file count, sizes, hashes, validity.

    python3 ~/crispr_snapshot.py ~/pixel8/library/.py

Output: `snapshot_YYYYMMDD_HHMMSS_before.json` in the target folder.

---

### Phase 1 — Repair  *(JSON only — Phase skipped for .py)*
Fix structurally broken files before touching names or content.

    python3 ~/crispr_repair.py --dry-run   # preview
    python3 ~/crispr_repair.py             # apply (backs up originals → repair_backups/)

**Certification gate:** `fixed=N  still_invalid=0  not_found=N`

For `.py` files: use `python3 -m py_compile <file>` to identify syntax errors.
Auto-repair is not attempted — flag broken files in the report for manual review.

---

### Phase 2 — Rename
Normalize filenames, segregate copies/versions/duplicates.

    python3 ~/crispr_rename.py <target> --dry-run   # preview all operations
    python3 ~/crispr_rename.py <target>             # apply

Order of operations (matters — do not reorder):
1. `--copies`   — move `filename (1).ext` → `copies/`
2. `--spaces`   — fix spaces, quotes, shell-unsafe chars in filenames
3. `--rename`   — fix broken/fragment filenames (bad name detection)
4. `--versions` — `_vN` (numbered) → `versions/`; `_v` (latest) keeps its spot, un-suffixed → `versions/`
5. `--dedup`    — content-hash duplicates → `duplicates/`

**Certification gate:** renamed=N, moved=N, `✓ No conflicts`

---

### Phase 3 — Consolidate
Build the master index, classify groups, flag noise and credentials.

    python3 ~/crispr_consolidate.py --dry-run   # preview
    python3 ~/crispr_consolidate.py             # write library_master.json + report
    python3 ~/crispr_consolidate.py --remove-noise   # archive noise → removed.json

**Certification gates:**
- `✓ All files valid`
- `✓ No noise files detected`
- Credential suspects reviewed and resolved
- OTHER group < 30% of total files (target)
- `library_master.json` and `library_report.txt` written

---

### Phase 4 — After Snapshot + Certification Report
Capture post-clean state and produce the diff.

    python3 ~/crispr_snapshot.py ~/pixel8/library/.py --compare

Output: `snapshot_YYYYMMDD_HHMMSS_after.json` + printed before/after diff.

**Final certification:**
- Files removed: N (noise) + N (duplicates) + N (versions)
- Files renamed: N
- Invalid/broken: 0
- Credential suspects: 0 unresolved
- Library size delta: XMB → YMB
- Master index: ✓ written
- Audit trail: removed.json ✓

---

## Conventions

| Convention | Meaning |
|---|---|
| `_v` suffix (no number) | Latest version — keep in main folder |
| `_vN` suffix (numbered) | Specific older snapshot — move to `versions/` |
| `(1)` `(2)` in name | OS copy — move to `copies/` |
| Identical content hash | Duplicate — move to `duplicates/` |
| `removed.json` | Append-only audit log — never delete |
| `library_master.json` | The `__init__.py` — unified index entry point |

## Subfolders
```
<library>/
  copies/         ← OS-generated copies
  versions/       ← superseded versions
  duplicates/     ← content-identical files
  repair_backups/ ← originals before any repair write
  removed.json    ← audit trail for archived noise
  library_master.json  ← unified index (re-generated each run)
  library_report.txt   ← last report
```

## Extension-Specific Notes

| Type | Validity check | Repair strategy |
|---|---|---|
| `.json` | `json.loads()` | strip_trailing, fix_annotations, close_truncated |
| `.py` | `ast.parse()` / `py_compile` | Flag only — no auto-repair |
| `.md` | Always valid | Flag only |
| `.sh` | `bash -n` syntax check | Flag only |
| `.txt` | Always valid | N/A |
