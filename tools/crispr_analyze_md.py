#!/usr/bin/env python3
"""
Analyze OTHER group in .md library — show prefix clusters and size distribution.
Helps identify groups to add to crispr_consolidate_md.py.
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

LIBRARY = Path.home() / "pixel8/library/.md"
SKIP = {"library_master_md.json", "removed_md.json", "library_report_md.txt"}

# Reuse same group detection as consolidate to find OTHER files
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
    # Numbered course sequences (02-, 03-, 04-, 06-)
    # React/JS/rendering frameworks, Playwright, Apple dev (WWDC/WWDS/SwiftUI)
    # MCP, Notion, cargo, MLOPS, glibc, NextJS, Netlify, Cloudflare, etc.
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
        if p.search(stem):
            return g
    return "VETTING"

def first_word(stem):
    """Extract first meaningful word/prefix for clustering."""
    stem = re.sub(r"^[\W_]+", "", stem)  # strip leading symbols
    parts = re.split(r"[_\-\s]+", stem)
    return parts[0].upper() if parts else stem.upper()

files = [
    f for f in LIBRARY.iterdir()
    if f.is_file() and f.suffix == ".md"
    and f.name not in SKIP
    and detect_group(f.stem) == "VETTING"
]

print(f"VETTING files (pending triage): {len(files)}\n")

# Prefix cluster analysis
prefix_counts = Counter(first_word(f.stem) for f in files)
prefix_sizes  = defaultdict(int)
for f in files:
    prefix_sizes[first_word(f.stem)] += f.stat().st_size

print(f"{'PREFIX':<30} {'COUNT':>6}  {'~SIZE':>8}")
print("─" * 50)
for prefix, count in prefix_counts.most_common(60):
    sz = prefix_sizes[prefix]
    size_str = f"{sz/1024:.1f}KB" if sz < 1_048_576 else f"{sz/1_048_576:.1f}MB"
    print(f"  {prefix:<28} {count:>6}  {size_str:>8}")

# Largest individual files
print(f"\n{'─'*50}")
print("Top 15 largest OTHER files:")
for f in sorted(files, key=lambda x: x.stat().st_size, reverse=True)[:15]:
    sz = f.stat().st_size
    size_str = f"{sz/1024:.1f}KB" if sz < 1_048_576 else f"{sz/1_048_576:.1f}MB"
    print(f"  {size_str:>8}  {f.name[:65]}")
