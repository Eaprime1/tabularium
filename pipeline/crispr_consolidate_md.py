#!/usr/bin/env python3
"""
Crispr-NiE Consolidate (.md) v1
- Groups all .md files by theme prefix
- Builds library_master_md.json
- Flags noise candidates
- Appends removed metadata to removed_md.json
- Prints full library report
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

LIBRARY = Path.home() / "pixel8" / "library" / ".md"
MASTER  = LIBRARY / "library_master_md.json"
REMOVED = LIBRARY / "removed_md.json"
REPORT  = LIBRARY / "library_report_md.txt"

GROUPS = [
    # ── core systems ─────────────────────────────────────────────────────────
    ("PRIME",      r"^(PRIME_|ALPHA_PRIME|PINNACLE_PRIME|📘_PRIME|prime_codex)"),
    ("UNEXUS",     r"^(UNEXUS|UNEXUSI)"),
    ("CODEX",      r"^(CODEX_|COMMISSION|upgrade_CODEX|upgrade_C|CONSOLIDATION|CONSORTIUM|END_MATTER|FRONT_MATTER|MILESTONE|REVIEW_GUIDE|diamond_of_aces_CODEX)"),
    ("LEXEME",     r"^lexeme_"),
    ("MOAV",       r"^(moav_|MOAV_|🤰|🔬_Alignment_with_MOAV|moav_research|MOAV_Research)"),
    ("MOBIUS",     r"^mobius"),
    ("QUANTUM",    r"^quantum"),
    ("MERGE",      r"^merge"),
    ("PANDORA",    r"^(pandora|PANDORA)"),
    ("PORTAQUE",   r"^(PORTAQUE|📦PORTAQUE)"),
    ("PRIMORIS",   r"^(primoris|PRIMORIS)"),
    ("KA",         r"(^🧁|^🧁md|ka_pressure|ka-pressure|Expanding_the_Ka|Ka_Pressure)"),
    ("SARGASSO",   r"^(sargasso|The_Sargasso|spacetime|🜃)"),
    ("DIAMOND",    r"^diamond_of_aces"),
    ("SEEK",       r"^seek"),
    ("CHAITIN",    r"^chaitin"),
    ("OMEGA",      r"^omega"),
    ("BEASIS",     r"^beasis"),
    ("TRANSITION", r"^13-17_transition"),
    ("SHADOW",     r"(shadow_as_mother|mother_as_shadow|shadow_mother|🤱mother)"),
    ("QUILL",      r"^🪶"),
    ("TERMINAL",   r"^(💠|terminal_sacred_odyssey)"),
    ("LIMINAL",    r"^(💬🧁|Liminal_Lighthouse)"),
    ("VISIONARY",  r"^(visionary_project|🪬DUPLICATE|🪬VISIONARY)"),
    ("DUNGEON",    r"(Dungeon_Master|Port_as_a_Dungeon)"),
    # ── project / meta ───────────────────────────────────────────────────────
    ("README",     r"^README"),
    ("RESEARCH",   r"^(RESEARCH|research_|nano_concepts)"),
    ("SESSION",    r"^(session-|conversation[-_]|Roundtable_|Simple_IS_Catalog|distillation_)"),
    ("STAGED",     r"^(STAGED_|staged_)"),
    ("PIXEL8",     r"^(PIXEL8|PIXEL_|PIXELATOR_|pixel8a)"),
    ("GITHUB",     r"^github_"),
    ("SVG",        r"^svg_"),
    # ── external / recycle (confirmed non-original: courses, stdlib, tool docs) ──
    # MLOPS course, Rust/bitvec stdlib, React Native, Notion API, Cargo,
    # NextJS/Netlify/Cloudflare, SwiftUI WWDC
    ("EXTERNAL",   r"^(mlops|mcp[-_.]|mcp$|notion-|native-|cargo-|llms|licenses|Write_Bit|NoAlias|Bit[A-Z]|deref_|deriving|nom_|gguf|nix-setup|node_mcp|nextjs|netlify|deploy-cloudflare|maybe_types|meet_the_|mistral|ml-benchmark|reference_guide|claude-sdk|claude_sdk|css[-_]|react-native|swiftui|wwdc|navigationstack|measuring-|media-heartmula|media-songsee|general-purpose-issue|generate-account|generate-guidelines|geo-sra|getting_started\.md|CRATE_README|ORG_CODE|UserDocumentation|VERSIONING\.md|VERSION_HISTORY|VERSION_0_DOC|USAGE_EXAMPLES|NOTICES|CREDITS|file_with_spaces|table_with|table_wrap|table_truncate)"),
    # ── noise ────────────────────────────────────────────────────────────────
    ("NOISE",      r"^(source_file_|bin_bash|usr_bin_env|Pass_It|Heres_a|I_can|version$|snapshot_)"),
    # ── vetting (ambiguous — could be skills, project docs, or accumulated refs) ─
    ("VETTING",    r".*"),
]

COMPILED = [(g, re.compile(p, re.IGNORECASE)) for g, p in GROUPS]


def detect_group(stem: str) -> str:
    for group, pat in COMPILED:
        if pat.search(stem):
            return group
    return "OTHER"


def extract_heading(path: Path) -> str | None:
    """Return first H1 or H2 heading from the markdown file."""
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()[:80]
            if line.startswith("## "):
                return line[3:].strip()[:80]
    except Exception:
        pass
    return None


def _read_frontmatter(path: Path) -> str:
    """Return YAML frontmatter string if file starts with ---, else ''."""
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:800]
        if not head.startswith("---"):
            return ""
        end = head.find("---", 3)
        return head[3:end] if end != -1 else ""
    except Exception:
        return ""


def is_memory_file(path: Path) -> bool:
    """Claude Code auto-memory files have 'type:' field = user/project/feedback/reference."""
    fm = _read_frontmatter(path)
    if not fm:
        return False
    return bool(re.search(r"^type:\s*(user|project|feedback|reference)\b", fm, re.MULTILINE))


def is_skill_file(path: Path) -> bool:
    """Return True if file is a Claude Code skill definition.

    Detects two formats:
      1. YAML frontmatter with 'name:' and 'description:' (but NOT a memory file)
      2. Plain prompt starting with 'You are' (role-based agent prompt)
    """
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:600]
        if head.startswith("---"):
            fm = _read_frontmatter(path)
            if fm and "name:" in fm and "description:" in fm and not is_memory_file(path):
                return True
            return False
        first_line = head.lstrip().split("\n")[0].strip()
        return first_line.lower().startswith("you are")
    except Exception:
        return False


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

    skip = {"library_master_md.json", "removed_md.json", "library_report_md.txt"}
    files = sorted(
        f for f in LIBRARY.iterdir()
        if f.is_file() and f.suffix == ".md"
        and f.parent == LIBRARY
        and f.name not in skip
    )

    print(f"\n=== CRISPR CONSOLIDATE (.md) {'[DRY RUN] ' if dry_run else ''}===")
    print(f"Library : {LIBRARY}")
    print(f"Files   : {len(files)}\n")

    groups:  dict[str, list[str]] = {}
    index:   list[dict]           = []
    noise:   list[Path]           = []
    total_sz = 0

    for f in files:
        group = detect_group(f.stem)
        # Content-based overrides: memory and skill definitions trump filename groups
        if group == "VETTING":
            if is_memory_file(f):
                group = "MEMORY"
            elif is_skill_file(f):
                group = "SKILLS"
        sz    = f.stat().st_size
        total_sz += sz

        entry = {
            "file":    f.name,
            "group":   group,
            "size":    sz,
            "heading": extract_heading(f),
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
            "type":           "markdown",
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
        print(f"✓ library_master_md.json written ({fmt_size(MASTER.stat().st_size)})")

    lines = [
        f"CRISPR LIBRARY REPORT (.md) — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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
        "✓ All files valid (markdown)",
        "",
    ]

    memory_entries = [e for e in index if e["group"] == "MEMORY"]
    if memory_entries:
        lines.append(f"MEMORY files ({len(memory_entries)}) — Claude context/memory records:")
        for e in sorted(memory_entries, key=lambda x: x["file"]):
            lines.append(f"  - {e['file']}")
    else:
        lines.append("✓ No memory files detected")

    lines.append("")
    skills_entries = [e for e in index if e["group"] == "SKILLS"]
    if skills_entries:
        lines.append(f"SKILLS detected ({len(skills_entries)}) — review before archiving:")
        for e in sorted(skills_entries, key=lambda x: x["file"]):
            lines.append(f"  - {e['file']}")
    else:
        lines.append("✓ No skill files detected")

    lines.append("")
    if noise:
        lines.append(f"NOISE candidates ({len(noise)}) — run --remove-noise to archive:")
        for f in noise:
            lines.append(f"  - {f.name}")
    else:
        lines.append("✓ No noise files detected")

    report_text = "\n".join(lines)
    print(report_text)

    if not dry_run and not report_only:
        REPORT.write_text(report_text + "\n", encoding="utf-8")
        print(f"\n✓ report saved → library_report_md.txt")

    if remove_noise and noise:
        print(f"\nArchiving {len(noise)} noise files to removed_md.json...")
        for f in noise:
            sz = f.stat().st_size
            entry = {
                "archived_at": datetime.now().isoformat(timespec="seconds"),
                "file":        f.name,
                "reason":      "noise — bad filename / stub",
                "size":        sz,
                "heading":     extract_heading(f),
                "content":     None if sz > 512_000 else f.read_text(encoding="utf-8", errors="replace"),
            }
            if not dry_run:
                append_removed(entry)
                f.unlink()
                print(f"  → archived: {f.name}")


if __name__ == "__main__":
    main()
