#!/usr/bin/env python3
"""
Crispr-NiE Consolidate (.py) v1
- Groups all .py files by theme prefix
- Builds library_master_py.json
- Flags noise/invalid candidates
- Appends removed content metadata to removed_py.json
- Prints full library report
"""
import ast
import json
import re
import sys
from datetime import datetime
from pathlib import Path

LIBRARY  = Path.home() / "pixel8" / "library" / ".py"
MASTER   = LIBRARY / "library_master_py.json"
REMOVED  = LIBRARY / "removed_py.json"
REPORT   = LIBRARY / "library_report_py.txt"

GROUPS = [
    # ── named systems ────────────────────────────────────────────────────────
    ("FLEET",        r"^fleet"),
    ("CRISPR",       r"^crispr"),
    ("AQUIFER",      r"^(aquifer_|artesian_)"),
    ("DOOZER",       r"^(doozer_|maw_doozer)"),
    ("FRAGGLE",      r"^(fraggle|spike_)"),
    ("HENRY",        r"^henry_"),
    ("MANCER",       r"(mancer)"),
    ("HODIE",        r"^(hodie_|sync_hodie|crawl_consolidated)"),
    ("SIMPLEX",      r"^simplex_"),
    ("PRIME",        r"^prime_"),
    ("REDUNDANCY",   r"^redundancy_"),
    ("PIXELATOR",    r"^pixelator_"),
    ("BBS",          r"(_bbs$|^dialer$|^ascii_art$|^animations$)"),
    ("DISTILLATION", r"^distillation"),
    ("ONE_HERTZ",    r"^one_hertz"),
    ("VETTING",      r"^vetting_"),
    ("SACRED",       r"^sacred_seven"),
    ("SEEDS",        r"^seeds$"),
    ("CERT",         r"^cert_"),
    ("LEVEL",        r"^level_"),
    ("ENTITY",       r"^entity_"),
    ("CONVERSATION", r"^(conversation|batch_processor|chat$)"),
    ("RAIL",         r"^rail"),
    ("UI",           r"^(directory_navigator|terminal_ui|simplex_command|animations$|ascii_art$)"),
    ("COMMAND",      r"^(cmd$|cmd_)"),
    ("COMPLEXITY",   r"^(complexity|normalize$)"),
    ("EXPORT",       r"^extract_to_json"),
    ("ANALYSIS",     r"^(pattern_extractor|detect_patterns|analyze_content|redundancy_entity)"),
    ("SYMBOLS",      r"^symbols$"),
    ("CUSTODY",      r"^(transfer_inventory|chain_of_custody)"),
    ("LEXEME",       r"^lexeme_"),
    ("UTILITY",      r"^(file_sorter|zip_finder|session_logger|helpers$|io$|stream_utils|file$|simple_file_finder|connection_manager|do_the_move|update_favorites|main$|validators$|local_processor|advanced_processor|content_types|colab_drive)"),
    # ── project areas ────────────────────────────────────────────────────────
    ("NIE",          r"^nie_"),
    ("PORT",         r"^port_"),
    ("MOAV",         r"^moav"),
    ("CODEX",        r"^codex"),
    ("PRIMORIS",     r"^primoris"),
    ("QUANTUM",      r"^quantum"),
    ("PANDORA",      r"^pandora"),
    ("MERGE",        r"^merge"),
    ("SARGASSO",     r"^sargasso"),
    ("OMEGA",        r"^omega"),
    ("BEASIS",       r"^beasis"),
    # ── file types / utilities ───────────────────────────────────────────────
    ("CATALOGER",    r"^(faceted_|simple_is_catalog|simple_consciousness_catalog|termux_document|document_organizer|doc_)"),
    ("TERMINUS",     r"^terminus"),
    ("PHYSICS",      r"^(split_root|uproot|root_|particle|phoenix|inspect_root)"),
    ("KEYS",         r"^(my\.git|myrootkeys|myroot)"),
    ("SETUP",        r"^(setup_|install_|config_|termux_setup|check_|conf$|config$|__init__)"),
    ("TEST",         r"^(test_|tester_|testing_|simple_test$|conftest|sample$)"),
    ("NOISE",        r"^(temp_|tmp_|scratch_|unused_|old_|backup_|trailing_spaces$|clean_file$|spike_clean)"),
    ("OTHER",        r".*"),
]

COMPILED = [(g, re.compile(p, re.IGNORECASE)) for g, p in GROUPS]


def detect_group(stem: str) -> str:
    for group, pat in COMPILED:
        if pat.search(stem):
            return group
    return "OTHER"


def check_valid(path: Path) -> str:
    try:
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return "valid"
    except SyntaxError as e:
        return f"line {e.lineno}: {e.msg}"


def extract_symbols(path: Path, n=4) -> list:
    """Return first N top-level def/class names."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        names = [
            node.name for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and isinstance(getattr(node, "col_offset", 0), int)
            and node.col_offset == 0
        ]
        return names[:n]
    except Exception:
        return []


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

    skip = {"library_master_py.json", "removed_py.json", "library_report_py.txt"}
    files = sorted(
        f for f in LIBRARY.iterdir()
        if f.is_file() and f.suffix == ".py"
        and f.parent == LIBRARY
        and f.name not in skip
    )

    print(f"\n=== CRISPR CONSOLIDATE (.py) {'[DRY RUN] ' if dry_run else ''}===")
    print(f"Library : {LIBRARY}")
    print(f"Files   : {len(files)}\n")

    groups:  dict[str, list[str]] = {}
    index:   list[dict]           = []
    invalid: list[str]            = []
    noise:   list[Path]           = []
    total_sz = 0

    for f in files:
        status = check_valid(f)
        group  = detect_group(f.stem)
        sz     = f.stat().st_size
        total_sz += sz

        entry = {
            "file":    f.name,
            "group":   group,
            "size":    sz,
            "status":  status,
            "symbols": extract_symbols(f),
        }
        index.append(entry)
        groups.setdefault(group, []).append(f.name)

        if status != "valid":
            invalid.append(f.name)
        if group == "NOISE":
            noise.append(f)

    master = {
        "__library__": {
            "version":     "1.0",
            "type":        "python",
            "generated":   datetime.now().isoformat(timespec="seconds"),
            "total_files": len(files),
            "total_size":  fmt_size(total_sz),
            "invalid":     len(invalid),
            "groups":      {g: len(v) for g, v in sorted(groups.items())},
            "files_by_group": {g: sorted(v) for g, v in sorted(groups.items())},
        },
        "index": index,
    }

    if not dry_run and not report_only:
        MASTER.write_text(json.dumps(master, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ library_master_py.json written ({fmt_size(MASTER.stat().st_size)})")

    lines = [
        f"CRISPR LIBRARY REPORT (.py) — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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
    ]

    if invalid:
        lines.append(f"✗ INVALID ({len(invalid)}):")
        for f in invalid:
            lines.append(f"  - {f}")
    else:
        lines.append("✓ All files valid Python")

    if noise:
        lines.append(f"\nNOISE candidates ({len(noise)}) — run --remove-noise to archive:")
        for f in noise:
            lines.append(f"  - {f.name}")
    else:
        lines.append("\n✓ No noise files detected")

    report_text = "\n".join(lines)
    print(report_text)

    if not dry_run and not report_only:
        REPORT.write_text(report_text + "\n", encoding="utf-8")
        print(f"\n✓ report saved → library_report_py.txt")

    if remove_noise and noise:
        print(f"\nArchiving {len(noise)} noise files to removed_py.json...")
        for f in noise:
            entry = {
                "archived_at": datetime.now().isoformat(timespec="seconds"),
                "file":        f.name,
                "reason":      "noise — temp/scratch/unused file",
                "symbols":     extract_symbols(f),
            }
            if not dry_run:
                append_removed(entry)
                f.unlink()
                print(f"  → archived: {f.name}")


if __name__ == "__main__":
    main()
