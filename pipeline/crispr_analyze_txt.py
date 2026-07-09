#!/usr/bin/env python3
"""
Analyze VETTING group in .txt library — prefix clusters, first-line patterns, size.
Helps identify new groups to add to crispr_consolidate_txt.py.
NOTE: Keep GROUPS here in sync with crispr_consolidate_txt.py.
"""
import re
from collections import Counter, defaultdict
from pathlib import Path

LIBRARY = Path.home() / "pixel8/library/.txt"
SKIP = {"library_master_txt.json", "removed_txt.json", "library_report_txt.txt"}

GROUPS = [
    ("CODE",       r"^(#|code_)"),
    ("DIRLIST",    r"^(directory_\d|pixeltree)"),
    ("PRIME",      r"^(PRIME_|ALPHA_PRIME|PINNACLE_PRIME|prime_)"),
    ("UNEXUS",     r"^(UNEXUS|UNEXUSI)"),
    ("DIAMOND",    r"^(\(diamond_of_aces\)|diamond_of_aces)"),
    ("CODEX",      r"^(CODEX|codex_|upgrade_|legacy_|front_matter_)"),
    ("MOAV",       r"^(moav_|MOAV_)"),
    ("PRIMORIS",   r"^(primoris_|PRIMORIS_)"),
    ("AQUIFER",    r"^(aquifer_|artesian_)"),
    ("HODIE",      r"^(hodie_|acp_|mulberry_)"),
    ("PIXEL8",     r"^(PIXEL8|pixel8|PIXEL_)"),
    ("ESSENCE",    r"^(essence_|slime_|primal_)"),
    ("SACRED",     r"^(ember|thee|yod|conscious|myth_|runic_|sacred_)"),
    ("QUANTUM",    r"^quantum"),
    ("KA",         r"^(ka[-_\s]|ka_pressure|Expanding.the.Ka)"),
    ("SARGASSO",   r"^(sargasso|the.sargasso)"),
    ("PANDORA",    r"^(pandora|PANDORA)"),
    ("LIMINAL",    r"^(liminal|Liminal|💬🧁)"),
    ("SEEK",       r"^seek"),
    ("SVG",        r"^svg"),
    ("RESEARCH",   r"^research"),
    ("END_MATTER", r"^END.MATTER"),
    ("DEEP_DIVE",  r"^Deep.(?:Dive|Integration).Response"),
    ("DUNGEON",    r"^(Dungeon.Master|Port.as.a.Dungeon|dungeon_|dice_)"),
    ("ROUNDTABLE", r"^roundtable"),
    ("SESSION",    r"^(session[-_]|conversation[-_]|Claude\s*\(|claude[-_]|chatgpt)"),
    ("TERMINAL",   r"^.{0,10}Terminal[\s_]+transcript"),
    ("QUICKNOTE",  r"^(quicknote|quick[-_.]|quick$|chatgptnote|quicktext|gemininote|gemini$)"),
    ("MISSIONS",   r"^missions_"),
    ("TERMUX",     r"^termux_"),
    ("REFERENCE",  r"^reference_"),
    ("UTILITY",    r"^utility_"),
    ("DATA",       r"^data_"),
    ("NOISE",      r"^(Absolutely,|Ah,\s|Certainly!|Sure[,\s]|Here'?s\s|Let me|Yes,\s|Great[,\s]|Thank)"),
]
COMPILED = [(g, re.compile(p, re.IGNORECASE)) for g, p in GROUPS]

def detect_group(stem):
    s = stem.lower()
    for g, _ in COMPILED:
        if g in ("VETTING", "NOISE"):
            continue
        if s.startswith(g.lower() + "_"):
            return g
    for g, p in COMPILED:
        if p.search(stem): return g
    return "VETTING"

def is_code_file(path):
    try:
        first = path.read_text(encoding="utf-8", errors="replace")[:200].lstrip()
        return first.startswith("#!")
    except Exception:
        return False

def has_claude_suffix(stem):
    return bool(re.search(r"-\s*(Claude|ChatGPT)\s*$", stem, re.IGNORECASE))

def first_word(stem):
    stem = re.sub(r"^[\W_]+", "", stem)
    parts = re.split(r"[_\-\s]+", stem)
    return parts[0].upper() if parts else stem.upper()

def first_line(path):
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not set(line) <= set("=-#~*_"):
                return line[:70]
    except Exception:
        pass
    return ""

files = [
    f for f in LIBRARY.iterdir()
    if f.is_file() and f.suffix == ".txt"
    and f.name not in SKIP
    and detect_group(f.stem) == "VETTING"
    and not is_code_file(f)
    and not has_claude_suffix(f.stem)
]

print(f"VETTING files (pending triage): {len(files)}\n")

prefix_counts = Counter(first_word(f.stem) for f in files)
prefix_sizes  = defaultdict(int)
for f in files:
    prefix_sizes[first_word(f.stem)] += f.stat().st_size

print(f"{'PREFIX':<30} {'COUNT':>6}  {'~SIZE':>8}")
print("─" * 52)
for prefix, count in prefix_counts.most_common(60):
    sz = prefix_sizes[prefix]
    size_str = f"{sz/1024:.1f}KB" if sz < 1_048_576 else f"{sz/1_048_576:.1f}MB"
    print(f"  {prefix:<28} {count:>6}  {size_str:>8}")

print(f"\n{'─'*52}")
print("Top 15 largest VETTING files:")
for f in sorted(files, key=lambda x: x.stat().st_size, reverse=True)[:15]:
    sz = f.stat().st_size
    size_str = f"{sz/1024:.1f}KB" if sz < 1_048_576 else f"{sz/1_048_576:.1f}MB"
    print(f"  {size_str:>8}  {f.name[:65]}")

print(f"\n{'─'*52}")
print("Sample first lines (largest VETTING files):")
for f in sorted(files, key=lambda x: x.stat().st_size, reverse=True)[:20]:
    line = first_line(f)
    print(f"  [{f.name[:40]:<40}]  {line[:55]}")
