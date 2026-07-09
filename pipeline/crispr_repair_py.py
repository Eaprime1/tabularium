#!/usr/bin/env python3
"""
Crispr-NiE Repair (.py) — diagnose and fix invalid Python files.
Backs up originals before any write.
"""
import ast
import shutil
import sys
from datetime import datetime
from pathlib import Path

LIBRARY_PY = Path.home() / "pixel8/library/.py"
BACKUP_DIR  = LIBRARY_PY / "repair_backups"


def backup(path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    dest = BACKUP_DIR / f"{path.stem}_{ts}.bak"
    shutil.copy2(path, dest)
    return dest


def syntax_error(path: Path):
    try:
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return None
    except SyntaxError as e:
        return e


# ── fix functions ─────────────────────────────────────────────────────────────

def fix_fleet_op3s(text: str) -> str:
    """Two fixes: add 'pass' to empty __main__ block; change orphan elif to if."""
    lines = text.splitlines(keepends=True)
    # Fix 1: empty if __name__ == "__main__" block
    for i, line in enumerate(lines):
        if line.strip().startswith("if __name__") and "__main__" in line:
            j = i + 1
            while j < len(lines) and (lines[j].strip() == "" or lines[j].strip().startswith("#")):
                j += 1
            if j >= len(lines) or not lines[j].startswith("    "):
                lines.insert(i + 1, "    pass\n")
            break
    # Fix 2: orphan elif with no preceding if (placeholder comment gap)
    result = []
    prev_real = None
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("elif ") and prev_real in (None, "comment", "blank"):
            line = line.replace("elif ", "if ", 1)
        if stripped == "" or stripped.startswith("#"):
            prev_real = "blank" if stripped == "" else "comment"
        else:
            prev_real = "code"
        result.append(line)
    return "".join(result)


def fix_myrootkeys(text: str) -> str:
    """Remove bare shell 'cd' command — not valid Python."""
    return "".join(
        line for line in text.splitlines(keepends=True)
        if not line.strip().startswith("cd ")
    )


def fix_split_root(text: str) -> str:
    """Line 28: two merged statements — keep only the library='np' version."""
    fixed = []
    for line in text.splitlines(keepends=True):
        if 'tree.arrays(entry_stop=SAMPLE_SIZE, library="np")' in line \
                and 'tree.arrays(entry_stop=SAMPLE_SIZE)' in line:
            # Keep only the library="np" half
            fixed.append('    sample = tree.arrays(entry_stop=SAMPLE_SIZE, library="np")\n')
        else:
            fixed.append(line)
    return "".join(fixed)


def fix_terminus2(text: str) -> str:
    """Replace U+00A0 non-breaking spaces with regular spaces throughout."""
    return text.replace("\u00a0", " ")


REPAIRS = {
    "fleet_op3s.py":           fix_fleet_op3s,
    "myrootkeys.py":           fix_myrootkeys,
    "split_root_by_sizev1.py": fix_split_root,
    "terminus2.py":            fix_terminus2,
}


def repair(path: Path, fix_fn, dry_run: bool) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    fixed = fix_fn(text)
    result = {"file": path.name, "status": "unknown", "note": ""}
    try:
        ast.parse(fixed)
        result["status"] = "fixed"
    except SyntaxError as e:
        result["status"] = "still_invalid"
        result["note"] = f"line {e.lineno}: {e.msg}"
        return result
    if not dry_run:
        bak = backup(path)
        path.write_text(fixed, encoding="utf-8")
        result["note"] = f"backup → {bak.name}"
    return result


def main():
    dry_run = "--dry-run" in sys.argv
    target_arg = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
    target = Path(target_arg).expanduser().resolve() if target_arg else LIBRARY_PY

    print(f"\n=== CRISPR REPAIR (.py) {'[DRY RUN] ' if dry_run else ''}===")
    print(f"Target: {target}\n")

    # Diagnose all invalid .py files first
    print("--- DIAGNOSIS ---")
    for f in sorted(target.glob("*.py")):
        err = syntax_error(f)
        if err:
            print(f"  ✗ {f.name}")
            print(f"    line {err.lineno}: {err.msg}")
            if err.text:
                print(f"    >>> {err.text.rstrip()}")

    print()

    # Apply known repairs
    print("--- REPAIRS ---")
    fixed = invalid = missing = 0
    for name, fix_fn in REPAIRS.items():
        path = target / name
        if not path.exists():
            print(f"  · {name:<45} [not found]")
            missing += 1
            continue
        r = repair(path, fix_fn, dry_run)
        icon = "✓" if r["status"] == "fixed" else "✗"
        print(f"  {icon} {name}")
        if r["note"]:
            print(f"    └─ {r['status']}: {r['note']}")
        else:
            print(f"    └─ {r['status']}")
        if r["status"] == "fixed":
            fixed += 1
        else:
            invalid += 1

    print(f"\n  fixed={fixed}  still_invalid={invalid}  not_found={missing}")
    if not dry_run and fixed:
        print(f"  backups → {BACKUP_DIR}")


if __name__ == "__main__":
    main()
