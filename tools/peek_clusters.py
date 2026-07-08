#!/usr/bin/env python3
"""Peek at mystery large files and small clusters."""
from pathlib import Path

lib = Path.home() / 'pixel8/library/.md'

SPECIFIC = [
    'dataset-formats.md',
    'anthropic-best-practices.md',
    'discord.md',
    'pinn_workflow.md',
    'GUARDIAN_CHARACTERS_CATALOG.md',
    'DEEP_DIVE_COMPREHENSIVE_REVIEW.md',
    'InputFormatReference.md',
    'extending-the-dashboard.md',
    'component-creation.md',
    'docs.md',
]

print("SPECIFIC FILE PEEK")
for name in SPECIFIC:
    p = lib / name
    if not p.exists():
        print(f"\n  [NOT FOUND] {name}")
        continue
    print(f"\n{'='*62}")
    print(f"  {name}  ({p.stat().st_size//1024}KB)")
    print('='*62)
    lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
    shown = 0
    for line in lines[:30]:
        if line.strip():
            print(f"  {line.strip()[:72]}")
            shown += 1
            if shown >= 6:
                break

# Sample the 4-count clusters that sound original
PREFIXES = ['memory', 'perspective', 'guardian', 'visual', 'windows', 'ai']
print(f"\n\nCLUSTER SAMPLES (4-count groups)")
for prefix in PREFIXES:
    files = sorted(f for f in lib.iterdir()
                   if f.is_file() and f.name.lower().startswith(prefix))[:4]
    if not files:
        continue
    print(f"\n{'─'*52}  {prefix.upper()}")
    for f in files:
        print(f"\n  ── {f.name[:58]}")
        try:
            lines = f.read_text(encoding='utf-8', errors='replace').splitlines()
            shown = 0
            for line in lines[:15]:
                if line.strip():
                    print(f"     {line.strip()[:68]}")
                    shown += 1
                    if shown >= 3:
                        break
        except Exception as e:
            print(f"     [error: {e}]")
