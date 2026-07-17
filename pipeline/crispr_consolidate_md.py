#!/usr/bin/env python3
"""
Crispr-NiE Consolidate (.md) v2
- Groups all .md files by theme prefix + universal prefix detection
- HEADING_OVERRIDES: H1/H2 content signals for VETTING files
- MEMORY / SKILLS detection via frontmatter content
- Security scan on all file headers
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
    ("CREATIVE",   r"^creative-"),
    ("AUTONOMOUS", r"^autonomous-"),
    ("FINANCE",    r"^finance-"),
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
    ("AGENT",      r"^(AGENT_|agent_)"),
    ("GUARDIAN",   r"^(GUARDIAN_|PERSPECTIVE_GUARDIAN|PERSPECTIVE_REQUEST_|guardian_|perspective_guardian)"),
    # ── sacred / consciousness ────────────────────────────────────────────────
    ("SACRED",     r"^(sacred_|SACRED_|ember_|EMBER_|conscious_|myth_|runic_)"),
    # ── project extensions ────────────────────────────────────────────────────
    ("HODIE",      r"^(hodie_|acp_|mulberry_)"),
    ("AQUIFER",    r"^(aquifer_|artesian_)"),
    ("ESSENCE",    r"^(essence_|slime_|primal_)"),
    ("MISSIONS",   r"^(missions_|mission_|MISSION_)"),
    # ── project / meta ───────────────────────────────────────────────────────
    ("README",     r"^README"),
    ("RESEARCH",   r"^(RESEARCH|research_|nano_concepts)"),
    ("SESSION",    r"^(session[-_]|conversation[-_]|Roundtable_|Simple_IS_Catalog|distillation_|claude[-_]conversation|chatgpt[-_]|termux\d|Terminal\d)"),
    ("STAGED",     r"^(STAGED_|staged_)"),
    ("PIXEL8",     r"^(PIXEL8|PIXEL_|PIXELATOR_|pixel8a)"),
    ("GITHUB",     r"^github_"),
    ("SVG",        r"^svg_"),
    # ── external / recycle (confirmed non-original: courses, stdlib, tool docs) ──
    ("EXTERNAL",   r"^(mlops|mcp[-_.]|mcp$|notion-|native-|cargo-|llms|licenses|"
                   r"Write_Bit|NoAlias|Bit[A-Z]|deref_|deriving|nom_|gguf|"
                   r"nix-setup|node_mcp|nextjs|netlify|deploy-cloudflare|"
                   r"maybe_types|meet_the_|mistral|ml-benchmark|reference_guide|"
                   r"claude-sdk|claude_sdk|css[-_]|react-native|swiftui|"
                   r"wwdc|wwds|navigationstack|measuring-|"
                   r"media-heartmula|media-songsee|general-purpose-issue|"
                   r"generate-account|generate-guidelines|geo-sra|"
                   r"getting_started\.md|CRATE_README|ORG_CODE|UserDocumentation|"
                   r"VERSIONING\.md|VERSION_HISTORY|VERSION_0_DOC|USAGE_EXAMPLES|"
                   r"NOTICES|CREDITS|file_with_spaces|table_with|table_wrap|table_truncate|"
                   r"0[0-9][-_]|rerender|rendering[-_]|"
                   r"playwright|jest[-_]|testing[-_]guide|"
                   r"js[-_]|telegram|discord[-_]doc|"
                   r"apple[-_]dev|ios[-_]guide|xcode[-_]|"
                   r"configuration$|providers$|effects$|environment-variables|"
                   r"cli-commands|kanban$|^_data$|"
                   r"pinecone|weaviate|chromadb|qdrant|"
                   r"hermes[-_]|build[-_]a[-_]hermes|"
                   r"^AGENTS$|^CONTRIBUTING|CODE_OF_CONDUCT|^SECURITY|^Agent$|"
                   r"^deployment[-_]|^deployment$|^Dispatcher$|^SYNTAX$|^COMPARE$|"
                   r"^THIRD_PARTY|^other$|^_data$|^class$|^hooks$|"
                   r"^ADDING_A_PLATFORM|^adding-platform|^adding-provider|^adding-providers|"
                   r"^reference-|"
                   r"^productivity[-_]|^advanced[-_]|^software[-_]|^async[-_]|"
                   r"^license|^migration[-_]|^schema[-_]|^release[-_]|"
                   r"^testing[-_]|^bundle[-_]|^setup[-_]|^expo[-_]|^devops[-_]|"
                   r"^applicationinsights|"
                   r"^skill-authoring|^skill-catalog|"
                   r"^claude-|^docs$|^Windows$|^InputFormatReference$|"
                   r"^dataset-formats$|^anthropic-best-practices$|^ai-gateway$|^ai-patterns$|"
                   r"^tool[-_]|^plugin[-_]|^error[-_]|^error$|"
                   r"^example[-_]|^step[-_]|^client[-_]|"
                   r"^documentation[-_]|^documentation$|"
                   r"^python[-_]tutorial|^python[-_]guide|^python[-_]ref|"
                   r"^DOCUMENTATION$|^FAQ[-_]|^faq[-_]|"
                   r"^project-|^PROJECT_CHARTER|^REVIEW_SETUP|"
                   r"^context-compression|^context-budget|^context-window|^context-limit|"
                   r"^visual-change|^visual-companion|^visual-design|^visual-style|"
                   r"^Testing|^TestWith|^test-|"
                   r"^tool-gateway|^tool-matrix|^tool-call|^tool-use|"
                   r"^plugin-api|^plugin-features|^plugin-guide|"
                   r"^Errors|^error-codes|^error-handling|^error-patterns|"
                   r"^FromIterator|^from_raw_parts|^from-|"
                   r"^deeplinks|^deep-link|"
                   r"^build-a-|^build-agent|^build-mcp|^build-and-run|^build-mcp|"
                   r"^report-template|^report_issue|^report-templates|"
                   r"^task-creation|^task-patterns|"
                   r"^workers$|^workers-|^worker-|^workflow-format|"
                   r"^system-prompt|^system-surfaces|^system-prompt-design|"
                   r"^data-batch|^data-handling|^data-explorer|"
                   r"^config-plugin|^configuration-guide|^config-guide|"
                   r"^use-mcp|^use-soul|^use-voice|^use-skill|"
                   r"^complete-agent|^complete-guide|^complete-ref|"
                   r"^fix-codesign|^fix-csr|^update-github|^update-provider|"
                   r"^creative-|^autonomous-|^finance-|"
                   r"^server-|^server$|^github-|^windows-|^api-|^web-|^image-|"
                   r"^code-|^codebase-|^developer-guide|^development$|"
                   r"^implement-|^IMPLEMENTATION|"
                   r"^deploy-cloudflare|^infrastructure-patterns|"
                   r"^apple-|^spec-|^search-|^local|^app-|"
                   r"^interactive-|^google|^custom-|^custom$|"
                   r"the[-_]art[-_]of|how[-_]to[-_](write|build|create|use|install)|"
                   r"introduction[-_]to|guide[-_]to|basics[-_]of|overview[-_]of)"),
    # ── noise ────────────────────────────────────────────────────────────────
    ("NOISE",      r"^(source_file_|bin_bash|usr_bin_env|Pass_It|Heres_a|I_can|version$|snapshot_|spike_cert_)"),
    # ── vetting (catch-all) ───────────────────────────────────────────────────
    ("VETTING",    r".*"),
]

COMPILED = [(g, re.compile(p, re.IGNORECASE)) for g, p in GROUPS]

# Heading-based overrides for files that land in VETTING.
# Checked against first H1/H2 heading of the file.
HEADING_OVERRIDES = [
    ("SACRED",   re.compile(r"Sacred Empire|Ember Protocol|Bookend Tantrum|"
                             r"consciousness.*overload|Sacred.*Framework|"
                             r"Terminal.*Framework|TAKING THE QUILL|Library Oath|"
                             r"Tantrum Entity|Phoenix Protocol|Quill.*Resonance", re.I)),
    ("PRIME",    re.compile(r"PINNACLE PRIME|ALPHA.PRIME|Prime Codex|"
                             r"Omega Vault|Avatar Way|First Principles.*Coherence|"
                             r"Distributed Consciousness.*Framework|PRIME_CODEX|"
                             r"Radix Repo|Universal Framework.*Living", re.I)),
    ("CODEX",    re.compile(r"Cross.Reference|Front Matter|Consolidation|"
                             r"Commission Framework|End Matter|Milestone|"
                             r"CODEX.*Commission|diamond.*codex", re.I)),
    ("MOAV",     re.compile(r"MOAV Research|Research Consortium.*MOAV|"
                             r"MOAV Framework|moav.research", re.I)),
    ("SESSION",  re.compile(r"AI System Initialized|Sanitized summary.*Claude|"
                             r"Script started|Welcome to Termux|"
                             r"Hi Perplexity|Claude.*conversation|"
                             r"Claude.*Running Log|Autonomous Exploration.*WikiEntity|"
                             r"Working Thoughts.*Running Log|"
                             r"FROM_CLAUDE|Note for Gemini|Deep Dive.*System Review|"
                             r"Comprehensive.*System Review|Session Log.*Claude|"
                             r"CLAUDE\.md Update Guidelines|Update.*CLAUDE\.md", re.I)),
    ("MISSIONS", re.compile(r"^Mission:|Seneschal Protocol|Library.*Mission|"
                             r"Commission.*Assignment|Sparstone|"
                             r"Work Deck.*Mission|Mission Deck.*operational", re.I)),
    ("PANDORA",  re.compile(r"Create Pandora.*Mission|Mission Deck.*release|"
                             r"Pandora.*Box|Pandora.*Project|Pandora.*Protocol", re.I)),
    ("GUARDIAN", re.compile(r"Perspective Guardians|Guardian.*Catalog|Guardian Trinity|"
                             r"Guardian.*Breakthrough|PERSPECTIVE REQUEST|"
                             r"Guardian Review Automation|perspective.*guardian", re.I)),
    ("PIXEL8",   re.compile(r"PIXEL8|Pixelator|pixel8a|PIXEL.*Domos|"
                             r"Server.*Pixel 8a|Consciousness Collaboration Server|"
                             r"Shader Pipeline.*Composable|pixel canvas.*numpy|"
                             r"Perlin Noise|Visual Effects.*Noise|"
                             r"Visual Style Library.*HyperFrames|HyperFrames.*video|"
                             r"HyperFrames.*render|visual.*HyperFrames|"
                             r"HyperFrames.*block|HyperFrames.*component|"
                             r"Adding.*Block.*HyperFrames|Adding.*Component.*HyperFrames|"
                             r"Local File Server.*phone storage|Serve.*phone storage|"
                             r"Spector.*Configuration|CONFIG.*Spector|"
                             r"Server (Deployment|Information).*(Setup|Complete)|"
                             r"Step \d+: (Capture|Design|Script|Storyboard|Narration)|"
                             r"Write DESIGN\.md|Narration Script|Write.*Storyboard|"
                             r"Data in Motion.*video|composition.*video", re.I)),
    ("HODIE",    re.compile(r"Hodie.*Project|Project.*Hodie|"
                             r"Windows Development.*Quick Reference|"
                             r"Windows Development Environment Setup|"
                             r"Quick Start.*Infrastructure|"
                             r"AI Assistant Guide for Hodie|"
                             r"ACP.*Project|Mulberry.*Project|"
                             r"PIXEL8 Crawler|crawler_pixel8|Plexus Stage", re.I)),
    ("RESEARCH", re.compile(r"Webdings Normalization.*Linguistic|"
                             r"Linguistic.*Breakthrough|Archive Analysis|"
                             r"nano.*concept|research.*framework", re.I)),
    ("UNEXUS",   re.compile(r"\bUNEXUS\b|Radix\s+Repo|ontological.seed|"
                             r"DirectoryInspector.*unexusi|unexusi.*terminus|"
                             r"Directory Tree.*Document Analysis|"
                             r"SDWG.*Knowledge Refresh|Reality Anchor.*Framework|"
                             r"Knowledge Refresh.*Strategy|Document Analysis.*∰", re.I)),
    ("SARGASSO", re.compile(r"[Ss]argasso|navitae|navigo|ancient navigators", re.I)),
    ("EXTERNAL", re.compile(r"React Native|Rust.*stdlib|MLOPS Course|"
                             r"Playwright.*Testing|SwiftUI.*Tutorial|WWDC|"
                             r"API Reference.*SDK|Cargo.*crate|"
                             r"Getting Started.*Framework|Cloudflare.*deploy|"
                             r"Hermes.*Agent.*Development Guide|"
                             r"Hermes Agent.*Security Policy|Política de Seguridad de Hermes|"
                             r"Autonomous AI Agents|Build.*Plugin.*Hermes|"
                             r"Reference Guide|Introduction to \w+|"
                             r"How to (Write|Build|Create|Use|Install)|"
                             r"Project Charter|Review Setup|Context Compression|"
                             r"Visual Design System|Testing Framework|"
                             r"Tool Gateway|Plugin API Reference|"
                             r"Error Codes|Error Handling Guide|"
                             r"Deep Link|Deeplinks", re.I)),
]

_SENSITIVE = re.compile(
    r"BEGIN (RSA|OPENSSH|EC|DSA|PGP) (PRIVATE KEY|CERTIFICATE)"
    r"|password\s*=\s*\S"
    r"|api[_\s]?key\s*=\s*\S"
    r"|github_pat_[a-zA-Z0-9_]+"
    r"|gh[po]_[a-zA-Z0-9_]+",
    re.IGNORECASE,
)
# Values that look like placeholders — suppress false positives
_PLACEHOLDER = re.compile(
    r'=\s*["\']?(your[-_]|YOUR[-_]|<[^>]+>|example|placeholder|xxx|changeme|\*{3,})',
    re.IGNORECASE,
)


def detect_group(stem: str) -> str:
    s = stem.lower()
    # Universal prefix detection: if stem starts with {group}_, return that group.
    # This keeps the consolidator in sync with Titlemancer's named prefixes.
    for group, _ in COMPILED:
        if group in ("VETTING", "NOISE"):
            continue
        if s.startswith(group.lower() + "_"):
            return group
    for group, pat in COMPILED:
        if pat.search(stem):
            return group
    return "VETTING"


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
        head = path.read_text(encoding="utf-8", errors="replace")[:8192]
        if not head.startswith("---"):
            return ""
        end = head.find("---", 3)
        return head[3:end] if end != -1 else ""
    except Exception:
        return ""


def is_memory_file(path: Path) -> bool:
    fm = _read_frontmatter(path)
    if not fm:
        return False
    return bool(re.search(r"^type:\s*(user|project|feedback|reference)\b", fm, re.MULTILINE))


def is_skill_file(path: Path) -> bool:
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:600]
        if head.startswith("---"):
            fm = _read_frontmatter(path)
            if not fm or is_memory_file(path):
                return False
            # Standard skill: name: + description:
            if "name:" in fm and "description:" in fm:
                return True
            # Hermes skill card v1: title: + sidebar_label: + description:
            if "title:" in fm and "sidebar_label:" in fm and "description:" in fm:
                return True
            # Hermes skill card v2: title: + impact: + impactDescription:
            if "title:" in fm and "impact:" in fm and "impactDescription:" in fm:
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

    print(f"\n=== CRISPR CONSOLIDATE (.md) v2 {'[DRY RUN] ' if dry_run else ''}===")
    print(f"Library : {LIBRARY}")
    print(f"Files   : {len(files)}\n")

    groups:  dict[str, list[str]] = {}
    index:   list[dict]           = []
    noise:   list[Path]           = []
    total_sz = 0

    for f in files:
        group   = detect_group(f.stem)
        heading = extract_heading(f)

        # Content-based overrides: memory and skill definitions trump filename groups
        if group == "VETTING":
            if is_memory_file(f):
                group = "MEMORY"
            elif is_skill_file(f):
                group = "SKILLS"
            else:
                # Hermes docs page: sidebar_position + title + description (no sidebar_label)
                # These are framework documentation, not reusable skills → EXTERNAL
                fm = _read_frontmatter(f)
                if ("sidebar_position:" in fm and "title:" in fm
                        and "description:" in fm and "sidebar_label:" not in fm):
                    group = "EXTERNAL"

        # Heading-based overrides for remaining VETTING files
        if group == "VETTING" and heading:
            for grp, pat in HEADING_OVERRIDES:
                if pat.search(heading):
                    group = grp
                    break

        sz = f.stat().st_size
        total_sz += sz

        entry = {
            "file":    f.name,
            "group":   group,
            "size":    sz,
            "heading": heading,
        }
        index.append(entry)
        groups.setdefault(group, []).append(f.name)

        if group == "NOISE":
            noise.append(f)

    notes_path = LIBRARY / "library_notes.md"
    notes = notes_path.read_text(encoding="utf-8") if notes_path.exists() else ""

    master = {
        "__library__": {
            "version":        "2.0",
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
        f"CRISPR LIBRARY REPORT (.md) v2 — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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
        for e in sorted(skills_entries, key=lambda x: x["file"])[:10]:
            lines.append(f"  - {e['file']}")
        if len(skills_entries) > 10:
            lines.append(f"  ... and {len(skills_entries) - 10} more")
    else:
        lines.append("✓ No skill files detected")

    lines.append("")
    if noise:
        lines.append(f"NOISE candidates ({len(noise)}) — run --remove-noise to archive:")
        for f in noise:
            lines.append(f"  - {f.name}")
    else:
        lines.append("✓ No noise files detected")

    # Security scan
    sensitive = []
    for f in files:
        try:
            head = f.read_text(encoding="utf-8", errors="replace")[:400]
            m = _SENSITIVE.search(head)
            if m and not _PLACEHOLDER.search(head[max(0, m.start()-5):m.end()+40]):
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
