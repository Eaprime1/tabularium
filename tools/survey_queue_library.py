#!/usr/bin/env python3
"""Survey the downloads/queue/library folder structure."""
import os
from pathlib import Path

root = Path.home() / 'downloads/queue/library'

if not root.exists():
    print(f"NOT FOUND: {root}")
    exit(1)

print(f"ROOT: {root}\n")

# Walk all subdirectories
for dirpath, dirnames, filenames in os.walk(root):
    dirnames.sort()
    dp = Path(dirpath)
    rel = dp.relative_to(root)
    depth = len(rel.parts)
    indent = "  " * depth
    folder_name = dp.name if depth > 0 else "."

    # Count by extension
    from collections import Counter
    ext_counts = Counter(Path(f).suffix.lower() for f in filenames)

    print(f"{indent}📁 {folder_name}/  ({len(filenames)} files: {dict(ext_counts)})")

    # Show .md files and dot folders
    md_files = [f for f in sorted(filenames) if f.endswith('.md')]
    dot_files = [f for f in sorted(filenames) if f.startswith('.')]

    if md_files:
        for f in md_files[:8]:
            sz = (dp / f).stat().st_size
            print(f"{indent}  📄 {f}  ({sz//1024}KB)")
        if len(md_files) > 8:
            print(f"{indent}  ... and {len(md_files)-8} more .md files")

    if dot_files:
        for f in dot_files[:5]:
            print(f"{indent}  · {f}")

print(f"\n--- SUMMARY ---")
all_files = list(root.rglob('*'))
all_files = [f for f in all_files if f.is_file()]
from collections import Counter
ext_summary = Counter(f.suffix.lower() for f in all_files)
for ext, count in sorted(ext_summary.items(), key=lambda x: -x[1]):
    print(f"  {ext or '(no ext)':15} {count:5} files")
print(f"\n  TOTAL: {len(all_files)} files")
