#!/usr/bin/env python3
"""One-shot: fix double-prefix filenames left by titlemancer pass."""
from pathlib import Path
import re

L = Path.home() / "pixel8/library/.txt"

_PREFIXES = r"(vetting|reference|utility|data|code|sacred|prime|codex|ka|moav|missions|pixel8|termux)"
_DOUBLE = re.compile(rf'^{_PREFIXES}_{_PREFIXES}_', re.IGNORECASE)

fixed = 0
for f in sorted(L.iterdir()):
    if not f.is_file() or f.suffix != ".txt":
        continue
    m = _DOUBLE.match(f.stem)
    if not m:
        continue
    # Strip the first (outer) prefix — keep the inner one
    outer = m.group(1)
    new_name = f.name[len(outer) + 1:]  # drop "outer_"
    dst = L / new_name
    if dst.exists():
        print(f"✗  skip (exists): {new_name}")
        continue
    f.rename(dst)
    print(f"✓  {f.name[:60]}  →  {new_name}")
    fixed += 1

print(f"\n{fixed} files fixed")
