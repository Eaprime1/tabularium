#!/usr/bin/env python3
"""
Crispr-NiE Snapshot — capture before/after state of a library folder.
Usage:
  python3 crispr_snapshot.py <target>            # take snapshot
  python3 crispr_snapshot.py <target> --compare  # take snapshot + diff vs latest prior
  python3 crispr_snapshot.py <target> --list     # list existing snapshots
"""
import ast
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

SKIP = {"library_master.json", "removed.json", "library_report.txt"}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def check_validity(path: Path) -> str:
    ext = path.suffix.lower()
    try:
        if ext == ".json":
            json.loads(path.read_text(encoding="utf-8", errors="replace"))
            return "valid"
        elif ext == ".py":
            ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            return "valid"
        else:
            return "unchecked"
    except Exception as e:
        return f"invalid: {e}"


def fmt_size(n: int) -> str:
    return f"{n/1024:.1f}KB" if n < 1_048_576 else f"{n/1_048_576:.1f}MB"


def take_snapshot(target: Path) -> dict:
    files = sorted(
        f for f in target.iterdir()
        if f.is_file() and f.name not in SKIP and not f.name.startswith("snapshot_")
    )
    entries = []
    total_sz = 0
    invalid = []
    for f in files:
        sz = f.stat().st_size
        total_sz += sz
        validity = check_validity(f)
        entry = {
            "name":     f.name,
            "size":     sz,
            "hash":     file_hash(f),
            "valid":    validity,
            "mtime":    f.stat().st_mtime,
        }
        entries.append(entry)
        if not validity.startswith("valid") and validity != "unchecked":
            invalid.append(f.name)

    snap = {
        "taken_at":    datetime.now().isoformat(timespec="seconds"),
        "target":      str(target),
        "file_count":  len(files),
        "total_size":  total_sz,
        "total_size_fmt": fmt_size(total_sz),
        "invalid_count": len(invalid),
        "invalid":     invalid,
        "files":       entries,
    }
    return snap


def find_snapshots(target: Path) -> list[Path]:
    return sorted(target.glob("snapshot_*.json"))


def diff_snapshots(before: dict, after: dict):
    b_files = {e["name"]: e for e in before["files"]}
    a_files = {e["name"]: e for e in after["files"]}

    added   = [n for n in a_files if n not in b_files]
    removed = [n for n in b_files if n not in a_files]
    changed = [
        n for n in b_files if n in a_files
        and b_files[n]["hash"] != a_files[n]["hash"]
    ]
    unchanged = len(b_files) - len(removed) - len(changed)

    print(f"\n{'─'*50}")
    print(f"  BEFORE  {before['taken_at']}  {before['file_count']} files  {before['total_size_fmt']}")
    print(f"  AFTER   {after['taken_at']}  {after['file_count']} files  {after['total_size_fmt']}")
    print(f"{'─'*50}")

    sz_delta = after["total_size"] - before["total_size"]
    sign = "+" if sz_delta >= 0 else ""
    print(f"  Size delta   : {sign}{fmt_size(abs(sz_delta))} ({'grew' if sz_delta > 0 else 'shrank'})")
    print(f"  Files added  : {len(added)}")
    print(f"  Files removed: {len(removed)}")
    print(f"  Modified     : {len(changed)}")
    print(f"  Unchanged    : {unchanged}")
    print(f"  Invalid (before): {before['invalid_count']}  →  (after): {after['invalid_count']}")

    if added:
        print(f"\n  + Added ({len(added)}):")
        for n in sorted(added)[:20]:
            print(f"      {n}")
        if len(added) > 20:
            print(f"      ... and {len(added)-20} more")

    if removed:
        print(f"\n  - Removed ({len(removed)}):")
        for n in sorted(removed)[:20]:
            print(f"      {n}")
        if len(removed) > 20:
            print(f"      ... and {len(removed)-20} more")

    if changed:
        print(f"\n  ~ Modified ({len(changed)}):")
        for n in sorted(changed):
            print(f"      {n}")

    if after["invalid_count"] == 0:
        print(f"\n  ✓ All files valid")
    else:
        print(f"\n  ✗ Invalid files remain: {after['invalid']}")


def main():
    args = sys.argv[1:]
    compare = "--compare" in args
    list_only = "--list" in args
    target_arg = next((a for a in args if not a.startswith("--")), None)

    if not target_arg:
        print("Usage: crispr_snapshot.py <target_dir> [--compare] [--list]")
        sys.exit(1)

    target = Path(target_arg).expanduser().resolve()
    if not target.is_dir():
        print(f"Not a directory: {target}")
        sys.exit(1)

    existing = find_snapshots(target)

    if list_only:
        print(f"Snapshots in {target}:")
        for s in existing:
            d = json.loads(s.read_text(encoding="utf-8"))
            print(f"  {s.name}  —  {d['file_count']} files  {d['total_size_fmt']}")
        return

    # Take new snapshot
    snap = take_snapshot(target)
    label = "after" if compare else "before"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    snap_path = target / f"snapshot_{ts}_{label}.json"
    snap_path.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n=== CRISPR SNAPSHOT ===")
    print(f"Target  : {target}")
    print(f"Label   : {label}")
    print(f"Files   : {snap['file_count']}")
    print(f"Size    : {snap['total_size_fmt']}")
    print(f"Invalid : {snap['invalid_count']}")
    if snap["invalid"]:
        for f in snap["invalid"]:
            print(f"  ✗ {f}")
    else:
        print(f"  ✓ All files valid")
    print(f"Saved   : {snap_path.name}")

    if compare and existing:
        before_path = existing[-1]  # most recent prior snapshot
        before = json.loads(before_path.read_text(encoding="utf-8"))
        print(f"\nComparing vs: {before_path.name}")
        diff_snapshots(before, snap)


if __name__ == "__main__":
    main()
