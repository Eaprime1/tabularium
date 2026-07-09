#!/usr/bin/env python3
"""
Crispr-NiE Run v1 — unified pipeline orchestrator.

Each stage is an independent module with one mission.
The runner chains them in order without knowing their internals.

Stages:
  0  snapshot --before   capture baseline
  1  repair              fix broken files (skipped if no adapter exists)
  2  rename              normalize names, move versions/copies/dupes
  3  consolidate         group, index, build master document
  4  snapshot --compare  certification diff

Usage:
  python3 ~/crispr_run.py .json
  python3 ~/crispr_run.py .py  --dry-run
  python3 ~/crispr_run.py .md  --stage 3
  python3 ~/crispr_run.py .sh  --from 2
  python3 ~/crispr_run.py .json --stage 3 --remove-noise
"""
import subprocess
import sys
from pathlib import Path

HOME         = Path.home()
LIBRARY_BASE = HOME / "pixel8/library"

STAGE_NAMES = {
    0: "SNAPSHOT (before)",
    1: "REPAIR",
    2: "RENAME",
    3: "CONSOLIDATE",
    4: "CERTIFY (after snapshot)",
}

# Extension → stage script map.  Add entries as new adapters are built.
ADAPTERS = {
    ".json": {
        "repair":      "crispr_repair.py",
        "consolidate": "crispr_consolidate.py",
    },
    ".py": {
        "repair":      "crispr_repair_py.py",
        "consolidate": "crispr_consolidate_py.py",
    },
    ".md": {
        "consolidate": "crispr_consolidate_md.py",
    },

    ".sh": {
        "consolidate": "crispr_consolidate_sh.py",
    },
    ".txt": {
        "consolidate": "crispr_consolidate_txt.py",
    },
}

DIVIDER = "─" * 52


def run_cmd(cmd: list[str]) -> bool:
    result = subprocess.run(cmd, text=True)
    return result.returncode == 0


def run_stage(num: int, ext: str, target: Path, dry_run: bool, extra: list[str]) -> bool:
    adapters = ADAPTERS.get(ext, {})

    if num == 0:
        cmd = ["python3", str(HOME / "crispr_snapshot.py"), str(target)]

    elif num == 1:
        script = adapters.get("repair")
        if not script or not (HOME / script).exists():
            print(f"  (no repair adapter for {ext} — stage skipped)")
            return True
        cmd = ["python3", str(HOME / script), str(target)]
        if dry_run:
            cmd.append("--dry-run")

    elif num == 2:
        cmd = ["python3", str(HOME / "crispr_rename.py"), str(target)]
        if dry_run:
            cmd.append("--dry-run")

    elif num == 3:
        script = adapters.get("consolidate")
        if not script or not (HOME / script).exists():
            print(f"  (no consolidate adapter for {ext} — stage skipped)")
            return True
        cmd = ["python3", str(HOME / script)]
        if dry_run:
            cmd.append("--dry-run")
        cmd += extra

    elif num == 4:
        cmd = ["python3", str(HOME / "crispr_snapshot.py"), str(target), "--compare"]

    else:
        print(f"  Unknown stage {num}")
        return False

    return run_cmd(cmd)


def main():
    raw = sys.argv[1:]

    dry_run      = "--dry-run"      in raw
    remove_noise = "--remove-noise" in raw
    raw = [a for a in raw if a not in ("--dry-run", "--remove-noise")]

    # --stage N  (single stage)
    stage_only = None
    if "--stage" in raw:
        i = raw.index("--stage")
        stage_only = int(raw[i + 1])
        raw = raw[:i] + raw[i + 2:]

    # --from N  (stages N..4)
    from_stage = 0
    if "--from" in raw:
        i = raw.index("--from")
        from_stage = int(raw[i + 1])
        raw = raw[:i] + raw[i + 2:]

    ext = next((a for a in raw if a.startswith(".")), None)
    if not ext:
        print(__doc__)
        sys.exit(1)

    target = LIBRARY_BASE / ext.lstrip(".")
    if not target.is_dir():
        # try with dot prefix  e.g. .json
        target = LIBRARY_BASE / f".{ext.lstrip('.')}"
    if not target.is_dir():
        print(f"Library not found: {target}")
        sys.exit(1)

    extra = ["--remove-noise"] if remove_noise else []
    stages = [stage_only] if stage_only is not None else list(range(from_stage, 5))

    print(f"\n{'#' * 52}")
    print(f"  CRISPR-NiE RUN  {'[DRY RUN] ' if dry_run else ''}")
    print(f"  Extension : {ext}")
    print(f"  Library   : {target}")
    print(f"  Stages    : {stages}")
    print(f"{'#' * 52}")

    for s in stages:
        print(f"\n{DIVIDER}")
        print(f"  STAGE {s} — {STAGE_NAMES[s]}")
        print(DIVIDER)
        ok = run_stage(s, ext, target, dry_run, extra)
        if not ok:
            print(f"\n✗ Stage {s} failed — pipeline stopped.")
            sys.exit(1)

    print(f"\n{'#' * 52}")
    print(f"  ✓ Pipeline complete")
    print(f"{'#' * 52}\n")


if __name__ == "__main__":
    main()
