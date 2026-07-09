#!/usr/bin/env python3
"""
Crispr-NiE Salvage (.txt) v1
Finds .txt files whose content belongs in another library (.json, .sh, .py).
Proposes moves to the correct library subfolder.

Usage:
  python3 ~/crispr_salvage_txt.py           # dry run — show plan
  python3 ~/crispr_salvage_txt.py --apply   # execute moves
"""
import json
import re
import sys
from pathlib import Path

LIBRARY_BASE = Path.home() / "pixel8/library"
TXT_LIB      = LIBRARY_BASE / ".txt"
MASTER       = TXT_LIB / "library_master_txt.json"

APPLY = "--apply" in sys.argv

# Files to skip (these belong in .txt even though they look like other types)
SKIP_NAMES = {
    "pandora-sacred-beyond-seed.txt",   # content doc, JSON is incidental
    "sargasso-sea-chronicles.txt",      # content doc, keep in SARGASSO
    "termux1.txt", "Termux3.txt", "Terminal3.txt", "termux4.txt",  # SESSION convos
    "Pushing Forward: Concept Development & Inception Contribut.txt",  # DATA doc
}

# ── salvage targets: (destination_library, detector, clean_name_fn) ──────────

def _ext_stem(path: Path) -> str:
    """Strip wrapper extensions from stem (e.g. foo.json.txt → foo.json → foo)."""
    s = path.stem
    for ext in (".json", ".sh", ".py", ".tsx", ".js", ".md"):
        if s.endswith(ext):
            return s[: -len(ext)], ext
    return s, path.suffix

def _clean(stem: str) -> str:
    stem = re.sub(r'[^\w\s\-]', ' ', stem)
    stem = re.sub(r'\s+', '_', stem.strip())
    return re.sub(r'_+', '_', stem).strip('_').lower()[:60]

SALVAGE_RULES = [
    # (target_ext, group_hint, detector)
    (".json",
     "DATA",
     lambda name, desc, head: (
         name.endswith(".json.txt") or
         (desc and desc.strip().startswith("{") and '"' in (head or "")[:50])
     )),
    (".sh",
     "CODE",
     lambda name, desc, head: (
         name.endswith(".sh.txt") or
         (head or "").lstrip().startswith("#!/") and "bash" in (head or "")[:80]
     )),
    (".py",
     "CODE",
     lambda name, desc, head: (
         name.endswith(".py.txt") or
         (head or "").lstrip().startswith("#!/usr/bin/env python") or
         re.match(r'^(import |from \w+ import|def |class )', (head or "").lstrip())
     )),
]

def head(path: Path, n: int = 200) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:n]
    except Exception:
        return ""


def main():
    if not MASTER.exists():
        print(f"Master not found: {MASTER}\nRun stage 3 first.")
        sys.exit(1)

    data   = json.loads(MASTER.read_text(encoding="utf-8"))
    index  = data.get("index", [])

    print(f"\n=== CRISPR SALVAGE (.txt) ===")
    print(f"Library : {TXT_LIB}")
    print(f"Mode    : {'APPLY moves' if APPLY else 'DRY RUN — pass --apply to move'}\n")

    plan = []  # (src_path, dst_path, target_ext, reason)

    for entry in index:
        fname = entry["file"]
        fpath = TXT_LIB / fname
        if not fpath.exists():
            continue

        if fname in SKIP_NAMES:
            continue

        desc  = entry.get("description") or ""
        h     = head(fpath)

        for target_ext, group_hint, detector in SALVAGE_RULES:
            if not detector(fname, desc, h):
                continue

            dst_lib = LIBRARY_BASE / f".{target_ext.lstrip('.')}"
            if not dst_lib.is_dir():
                print(f"  [skip] target library not found: {dst_lib}")
                break

            # Build destination filename
            stem_raw = fpath.stem
            # Strip wrapper extension if present (foo.json.txt → foo)
            for ext in (".json", ".sh", ".py", ".tsx", ".js", ".md"):
                if stem_raw.lower().endswith(ext):
                    stem_raw = stem_raw[:-len(ext)]
                    break
            base = _clean(stem_raw) or "salvaged"  # guard empty stem (e.g. {.txt)
            # TSX/React → keep in .txt CODE, no .tsx library
            if fpath.suffix == ".txt" and ".tsx" in fpath.stem:
                print(f"  [note] {fpath.name}: TSX/React — no .tsx library, keeping in CODE/.txt")
                break
            dst_name = base + target_ext
            dst_path = dst_lib / dst_name

            # Avoid collision
            if dst_path.exists():
                dst_name = base + "_salvaged" + target_ext
                dst_path = dst_lib / dst_name

            plan.append((fpath, dst_path, target_ext, group_hint))
            break

    if not plan:
        print("  No salvage candidates found.")
        return

    print(f"  {'FILE':<55} {'→ DESTINATION'}")
    print(f"  {'─'*55}   {'─'*40}")
    for src, dst, ext, grp in plan:
        print(f"  {src.name[:55]:<55}   {dst.parent.name}/{dst.name[:40]}")

    print(f"\n  {len(plan)} files proposed for salvage to other libraries")

    if APPLY:
        print("\nMoving files...")
        moved = 0
        for src, dst, ext, grp in plan:
            if dst.exists():
                print(f"  ✗ skip (exists): {dst.name}")
                continue
            src.rename(dst)
            print(f"  ✓ {src.name[:45]} → .{ext.lstrip('.')}/{dst.name}")
            moved += 1
        print(f"\n✓ {moved} files salvaged — re-run stage 3 to update master index")
    else:
        print("\nPass --apply to execute moves.")


if __name__ == "__main__":
    main()
