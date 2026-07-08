#!/usr/bin/env python3
"""Sample CREATIVE and REFERENCE clusters to classify them."""
from pathlib import Path

lib = Path.home() / 'pixel8/library/.md'

targets = ['creative', 'reference', 'the', 'how', 'what', 'agent', 'autonomous', 'hermes']

for prefix in targets:
    files = sorted(f.name for f in lib.iterdir()
                   if f.is_file() and f.name.lower().startswith(prefix))[:10]
    if files:
        print(f"\n{prefix.upper()} ({len(files)} shown):")
        for name in files:
            print(f"  {name[:80]}")
