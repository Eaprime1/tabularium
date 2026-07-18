#!/usr/bin/env python3
"""
Crispr-NiE Consolidate (.txt) v1
- Groups all .txt files by theme prefix and content signals
- Detects code-as-txt (shebang content) and AI-response chat exports
- Extracts description from first meaningful line
- Builds library_master_txt.json
- Flags noise candidates
- Appends removed metadata to removed_txt.json
- Prints full library report
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

LIBRARY = Path.home() / "pixel8" / "library" / ".txt"
MASTER  = LIBRARY / "library_master_txt.json"
REMOVED = LIBRARY / "removed_txt.json"
REPORT  = LIBRARY / "library_report_txt.txt"

GROUPS = [
    # ── filename starts with # → code/script fragment saved as .txt ──────────
    ("CODE",       r"^(#|code_)"),
    # ── directory / tree dumps (often very large) ─────────────────────────────
    ("DIRLIST",    r"^(directory_\d|pixeltree)"),
    # ── project named systems ─────────────────────────────────────────────────
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
    ("SARGASSO",   r"^(sargasso|the.sargasso|navigo)"),
    ("PANDORA",    r"^(pandora|PANDORA)"),
    ("LIMINAL",    r"^(liminal|Liminal|💬🧁)"),
    ("SEEK",       r"^seek"),
    ("SVG",        r"^svg"),
    ("RESEARCH",   r"^research"),
    # ── typed document classes ────────────────────────────────────────────────
    ("END_MATTER", r"^END.MATTER"),
    ("DEEP_DIVE",  r"^Deep.(?:Dive|Integration).Response"),
    ("DUNGEON",    r"^(Dungeon.Master|Port.as.a.Dungeon|dungeon_|dice_)"),
    ("ROUNDTABLE", r"^roundtable"),
    ("SESSION",    r"^(session[-_]|conversation[-_]|Claude\s*\(|claude[-_]|chatgpt|termux\d|Terminal\d)"),
    # Terminal transcripts — allow emoji/symbol prefix before "Terminal transcript"
    ("TERMINAL",   r"^.{0,10}Terminal[\s_]+transcript"),
    # ── quick notes / short captures ─────────────────────────────────────────
    ("QUICKNOTE",  r"^(quicknote|quick[-_.]|quick$|chatgptnote|quicktext|gemininote|gemini$)"),
    # ── Titlemancer-assigned group prefixes (catch after pattern matching) ────
    ("MISSIONS",   r"^missions_"),
    ("TERMUX",     r"^termux_"),
    ("REFERENCE",  r"^reference_"),
    ("UTILITY",    r"^utility_"),
    ("DATA",       r"^data_"),
    # ── noise: AI chat exports saved with response-opener filenames ───────────
    ("NOISE",      r"^(Absolutely,|Ah,\s|Certainly!|Sure[,\s]|Here'?s\s|Let me|Yes,\s|Great[,\s]|Thank)"),
    # ── vetting (catch-all) ───────────────────────────────────────────────────
    ("VETTING",    r".*"),
]

# Description-based overrides for files that land in VETTING
DESC_OVERRIDES = [
    ("DIRLIST",   re.compile(r"^\.$|^\.:$|^/data/data/com\.termux|^/storage/emulated|^total \d+", re.MULTILINE)),
    ("SESSION",   re.compile(r"^Script started on |AI System Initialized|Sanitized summary of a Claude|Welcome to Termux|^[Hh]i [Pp]erplexity", re.IGNORECASE)),
    ("PRIME",     re.compile(r"PINNACLE PRIME|ALPHA.PRIME|prime codex|Pinnacle Prime|Radix Repo|Avatar Way|Distributed Consciousness|Universal Framework.*Living|PRIME_CODEX|PRIME CODEX|OMEGA_VAULT|First Principles.*Coherence", re.IGNORECASE)),
    ("TERMINAL",  re.compile(r"Welcome to Termux|Terminal transcript", re.IGNORECASE)),
    ("SACRED",    re.compile(r"Mythology Foundation|Bookend Tantrum|Consciousness Overload|deep bow of gratitude|ACKNOWLEDGMENTS|Ember Protocol|Tantrum Entity|TAKING THE QUILL|accept the Quill|Taking the Quill|Quill.*Resonance|Library Oath", re.IGNORECASE)),
    ("MOAV",      re.compile(r"moav.research|research.consortium|MOAV Research|MOAV Framework", re.IGNORECASE)),
    ("CODE",      re.compile(r"^import\s+React|^import\s+\{.*useState|^'use client'|^\"use client\"", re.IGNORECASE)),
    ("DATA",      re.compile(r"^\s*[\{\[]", re.IGNORECASE)),
    ("TERMUX",    re.compile(r"^Hit:\d+.*termux\.net|^Get:\d+.*termux|^Reading package lists|^pkg (install|update|upgrade)", re.IGNORECASE)),
    ("SARGASSO",  re.compile(r"navitae|navigo|ancient navigators", re.IGNORECASE)),
]

COMPILED = [(g, re.compile(p, re.IGNORECASE)) for g, p in GROUPS]

_TXT_PREFIX = re.compile(r'^txt_', re.IGNORECASE)

def normalize_stem(stem: str) -> str:
    """Strip wrapper prefixes (txt_) before group detection."""
    return _TXT_PREFIX.sub('', stem)

def detect_group(stem: str) -> str:
    normalized = normalize_stem(stem)
    s = normalized.lower()
    # Honor {group}_ prefixes produced by Titlemancer — stays in sync automatically
    for group, _ in COMPILED:
        if group in ("VETTING", "NOISE"):
            continue
        if s.startswith(group.lower() + "_"):
            return group
    for group, pat in COMPILED:
        if pat.search(normalized):
            return group
    return "VETTING"


def is_code_file(path: Path) -> bool:
    """Return True if file content starts with a shebang line."""
    try:
        first = path.read_text(encoding="utf-8", errors="replace")[:200].lstrip()
        return first.startswith("#!")
    except Exception:
        return False


def extract_description(path: Path) -> str | None:
    """Return first non-empty, non-separator line of the file."""
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            if set(line) <= set("=-#~*_"):
                continue
            return line[:80]
    except Exception:
        pass
    return None


def fmt_size(n: int) -> str:
    return f"{n/1024:.1f}KB" if n < 1_048_576 else f"{n/1_048_576:.1f}MB"


def append_removed(entry: dict):
    existing = []
    if REMOVED.exists():
        try:
            existing = json.loads(REMOVED.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = [existing]
        except Exception:
            pass
    existing.append(entry)
    REMOVED.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    dry_run      = "--dry-run"      in sys.argv
    remove_noise = "--remove-noise" in sys.argv
    report_only  = "--report"       in sys.argv

    skip = {"library_master_txt.json", "removed_txt.json", "library_report_txt.txt"}
    files = sorted(
        f for f in LIBRARY.iterdir()
        if f.is_file() and f.suffix == ".txt"
        and f.parent == LIBRARY
        and f.name not in skip
    )

    print(f"\n=== CRISPR CONSOLIDATE (.txt) {'[DRY RUN] ' if dry_run else ''}===")
    print(f"Library : {LIBRARY}")
    print(f"Files   : {len(files)}\n")

    groups:  dict[str, list[str]] = {}
    index:   list[dict]           = []
    noise:   list[Path]           = []
    total_sz = 0

    for f in files:
        group = detect_group(f.stem)
        # Claude/ChatGPT conversation exports often end with "- Claude" in stem
        if group == "VETTING" and re.search(r"-\s*(Claude|ChatGPT)\s*$", f.stem, re.IGNORECASE):
            group = "SESSION"
        # Content override: shebang in body → CODE even if filename didn't signal it
        if group == "VETTING" and is_code_file(f):
            group = "CODE"
        desc  = extract_description(f)
        # Description-based overrides for remaining VETTING files
        if group == "VETTING" and desc:
            for grp, pat in DESC_OVERRIDES:
                if pat.search(desc):
                    group = grp
                    break
        sz    = f.stat().st_size
        total_sz += sz

        entry = {
            "file":        f.name,
            "group":       group,
            "size":        sz,
            "description": desc,
        }
        index.append(entry)
        groups.setdefault(group, []).append(f.name)

        if group == "NOISE":
            noise.append(f)

    notes_path = LIBRARY / "library_notes.md"
    notes = notes_path.read_text(encoding="utf-8") if notes_path.exists() else ""

    master = {
        "__library__": {
            "version":        "1.0",
            "type":           "text",
            "generated":      datetime.now().isoformat(timespec="seconds"),
            "total_files":    len(files),
            "total_size":     fmt_size(total_sz),
            "groups":         {g: len(v) for g, v in sorted(groups.items())},
            "files_by_group": {g: sorted(v) for g, v in sorted(groups.items())},
            "notes":          notes,
        },
        "index": index,
    }

    if not dry_run and not report_only:
        MASTER.write_text(json.dumps(master, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ library_master_txt.json written ({fmt_size(MASTER.stat().st_size)})")

    lines = [
        f"CRISPR LIBRARY REPORT (.txt) — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Library : {LIBRARY}",
        f"Total   : {len(files)} files  /  {fmt_size(total_sz)}",
        "",
        f"{'GROUP':<14} {'FILES':>6}  {'~SIZE':>8}",
        "─" * 35,
    ]
    for group in sorted(groups):
        grp_files = [e for e in index if e["group"] == group]
        grp_sz = sum(e["size"] for e in grp_files)
        lines.append(f"  {group:<12} {len(grp_files):>6}  {fmt_size(grp_sz):>8}")
    lines += [
        "─" * 35,
        f"  {'TOTAL':<12} {len(files):>6}  {fmt_size(total_sz):>8}",
        "",
        "✓ All files valid (plain text)",
        "",
    ]

    code_entries = [e for e in index if e["group"] == "CODE"]
    if code_entries:
        lines.append(f"CODE files ({len(code_entries)}) — scripts saved as .txt, consider renaming to .sh/.py:")
        for e in sorted(code_entries, key=lambda x: x["file"]):
            desc = e.get("description") or ""
            lines.append(f"  - {e['file'][:55]}  {desc[:35]}")
    else:
        lines.append("✓ No code-as-txt files detected")

    lines.append("")
    if noise:
        lines.append(f"NOISE candidates ({len(noise)}) — run --remove-noise to archive:")
        for f in noise:
            lines.append(f"  - {f.name}")
    else:
        lines.append("✓ No noise files detected")

    # Security scan — flag files that look like they contain sensitive data
    _SENSITIVE = re.compile(r"BEGIN (RSA|OPENSSH|EC|DSA|PGP) (PRIVATE KEY|CERTIFICATE)|password\s*=\s*\S|api[_\s]?key\s*=\s*\S|github_pat_[a-zA-Z0-9_]+|gh[po]_[a-zA-Z0-9_]+", re.IGNORECASE)
    sensitive = []
    for f in files:
        try:
            head = f.read_text(encoding="utf-8", errors="replace")[:400]
            if _SENSITIVE.search(head):
                sensitive.append(f.name)
        except Exception:
            pass
    lines.append("")
    if sensitive:
        lines.append(f"⚠️  SECURITY — {len(sensitive)} file(s) may contain sensitive data:")
        for name in sensitive:
            lines.append(f"  ⚠️  {name}")
    else:
        lines.append("✓ No sensitive data detected in file headers")

    report_text = "\n".join(lines)
    print(report_text)

    if not dry_run and not report_only:
        REPORT.write_text(report_text + "\n", encoding="utf-8")
        print(f"\n✓ report saved → library_report_txt.txt")

    if remove_noise and noise:
        print(f"\nArchiving {len(noise)} noise files to removed_txt.json...")
        for f in noise:
            sz = f.stat().st_size
            entry = {
                "archived_at": datetime.now().isoformat(timespec="seconds"),
                "file":        f.name,
                "reason":      "noise — AI chat response export",
                "size":        sz,
                "description": extract_description(f),
                "content":     None if sz > 512_000 else f.read_text(encoding="utf-8", errors="replace"),
            }
            if not dry_run:
                append_removed(entry)
                f.unlink()
                print(f"  → archived: {f.name}")


if __name__ == "__main__":
    main()
