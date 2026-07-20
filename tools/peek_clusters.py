#!/usr/bin/env python3
"""Peek at borderline clusters to classify before bulk-routing."""
from pathlib import Path

lib = Path.home() / 'pixel8/library/.md'

TARGETS = {
    'user':        5,
    'apple':       5,
    'spec':        4,
    'feature':     4,
    'search':      4,
    'local':       4,
    'app':         4,
    'interactive': 4,
    'google':      4,
    'design':      4,
    'technical':   4,
    'stream':      4,
    'perspective': 4,
    'content':     4,
    'custom':      4,
}

for prefix, limit in TARGETS.items():
    files = sorted(f for f in lib.iterdir()
                   if f.is_file() and f.name.lower().startswith(prefix))[:limit]
    if not files:
        continue
    print(f"\n{'='*60}  {prefix.upper()}")
    for f in files:
        print(f"\n  ── {f.name[:58]}")
        try:
        try:
            with f.open(encoding='utf-8', errors='replace') as file:
                lines = []
                for i, line in enumerate(file):
                    lines.append(line)
                    if i >= 19:
                        break
            shown = 0
            for line in lines[:20]:
                if line.strip():
                    print(f"     {line.strip()[:68]}")
                    shown += 1
                    if shown >= 3:
                        break
        except Exception as e:
            print(f"     [error: {e}]")
