#!/usr/bin/env python3
"""
Crispr-NiE Consolidate v1
The __init__.py of the JSON library.
- Auto-groups all files by theme prefix
- Builds library_master.json  (the unified entry point)
- Flags noise/redundant candidates
- Appends removed content to removed.json (audit trail, never deletes without --remove)
- Prints a full library report
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

LIBRARY  = Path.home() / "pixel8" / "library" / ".json"
MASTER   = LIBRARY / "library_master.json"
REMOVED  = LIBRARY / "removed.json"
REPORT   = LIBRARY / "library_report.txt"

# ── group detection (first match wins) ───────────────────────────────────────
GROUPS = [
    ("PRIME",      r"^(PRIME_|ALPHA_PRIME|PINNACLE_PRIME|📘_PRIME)"),
    ("UNEXUS",     r"^(UNEXUS|UNEXUSI)"),
    ("CODEX",      r"^(CODEX_|COMMISSION|upgrade_CODEX|upgrade_C|CONSOLIDATION|CONSORTIUM|END_MATTER|FRONT_MATTER|MILESTONE|REVIEW_GUIDE|prime_codex)"),
    ("LEXEME",     r"^lexeme_"),
    ("MOAV",       r"^(moav_|MOAV_|🤰|🔬_Alignment_with_MOAV)"),
    ("MOBIUS",     r"^mobius-"),
    ("QUANTUM",    r"^quantum-"),
    ("MERGE",      r"^merge"),
    ("PANDORA",    r"^(pandora|PANDORA)"),
    ("PORTAQUE",   r"^(PORTAQUE|📦PORTAQUE)"),
    ("PRIMORIS",   r"^(primoris|PRIMORIS)"),
    ("KA",         r"(^🧁|ka_pressure|ka-pressure|Expanding_the_Ka|Ka_Pressure)"),
    ("SARGASSO",   r"^(sargasso|The_Sargasso|spacetime|🜃)"),
    ("DIAMOND",    r"^diamond_of_aces"),
    ("SEEK",       r"^seek"),
    ("SVG",        r"^svg_"),
    ("CHAITIN",    r"^chaitin-"),
    ("OMEGA",      r"^omega_library"),
    ("BEASIS",     r"^beasis_"),
    ("TRANSITION", r"^13-17_transition"),
    ("SHADOW",     r"(shadow_as_mother|mother_as_shadow|shadow_mother|🤱mother|🐦\u200d🔥🍾)"),
    ("QUILL",      r"^🪶"),
    ("TERMINAL",   r"^💠"),
    ("LIMINAL",    r"^(💬🧁|Liminal_Lighthouse)"),
    ("VISIONARY",  r"^(visionary_project|🪬DUPLICATE_VISIO|🪬VISIONARY_INTER)"),
    ("DUNGEON",    r"(Dungeon_Master|The_Port_as_a_Dungeon)"),
    ("MANIFEST",   r"\.manifest$"),
    ("SESSION",    r"^(session-|conversation[-_]|Roundtable_|Simple_IS_Catalog|distillation_)"),
    ("NOISE",      r"^(source_file|bin_bash|usr_bin_env|Pass_It|Heres_a|I_can|version|🪬_|Q_test_result|DEDUPLICATION_LOG|conversations_test_result|applet_access_history)"),
    ("OTHER",      r".*"),
]

CRED_PATTERN = re.compile(r"(gdrive.key|private.key|service.account|client.secret|oauth.token|auth.token|api.key)", re.IGNORECASE)

COMPILED = [(g, re.compile(p, re.IGNORECASE)) for g, p in GROUPS]


def detect_group(stem: str) -> str:
    for group, pat in COMPILED:
        if pat.search(stem):
            return group
    return "OTHER"


def load_safe(path: Path) -> tuple:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return data, "valid"
    except json.JSONDecodeError as e:
        return None, f"line {e.lineno}: {e.msg}"


def first_keys(data, n=4) -> list:
    if isinstance(data, dict):
        return list(data.keys())[:n]
    return []


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


def fmt_size(n: int) -> str:
    return f"{n/1024:.1f}KB" if n < 1_048_576 else f"{n/1_048_576:.1f}MB"


def main():
    dry_run      = "--dry-run"      in sys.argv
    remove_noise = "--remove-noise" in sys.argv
    report_only  = "--report"       in sys.argv

    # Gather all JSON files (skip master/removed/subfolders)
    skip = {"library_master.json", "removed.json", "library_report.txt"}
    files = sorted(
        f for f in LIBRARY.iterdir()
        if f.is_file() and f.suffix == ".json"
        and f.parent == LIBRARY
        and f.name not in skip
    )

    print(f"\n=== CRISPR CONSOLIDATE {'[DRY RUN] ' if dry_run else ''}===")
    print(f"Library : {LIBRARY}")
    print(f"Files   : {len(files)}\n")

    groups:   dict[str, list[str]] = {}
    index:    list[dict]           = []
    invalid:  list[str]            = []
    noise:    list[Path]           = []
    total_sz  = 0

    for f in files:
        data, status = load_safe(f)
        group = detect_group(f.stem)
        sz = f.stat().st_size
        total_sz += sz

        entry = {
            "file":   f.name,
            "group":  group,
            "size":   sz,
            "status": status,
            "keys":   first_keys(data),
        }
        index.append(entry)
        groups.setdefault(group, []).append(f.name)

        if status != "valid":
            invalid.append(f.name)
        if group == "NOISE":
            noise.append(f)

    # ── build master document ─────────────────────────────────────────────────
    master = {
        "__library__": {
            "version":     "1.0",
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
        print(f"✓ library_master.json written ({fmt_size(MASTER.stat().st_size)})")

    # ── report ────────────────────────────────────────────────────────────────
    lines = [
        f"CRISPR LIBRARY REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Library : {LIBRARY}",
        f"Total   : {len(files)} files  /  {fmt_size(total_sz)}",
        "",
        f"{'GROUP':<14} {'FILES':>6}  {'~SIZE':>8}",
        "─" * 35,
    ]

    for group in sorted(groups):
        grp_files = [f for f in index if f["group"] == group]
        grp_sz = sum(f["size"] for f in grp_files)
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
        lines.append("✓ All files valid JSON")

    if noise:
        lines.append(f"\nNOISE candidates ({len(noise)}) — run --remove-noise to archive:")
        for f in noise:
            lines.append(f"  - {f.name}")
    else:
        lines.append("\n✓ No noise files detected")

    cred_suspects = [e for e in index if CRED_PATTERN.search(e["file"])]
    if cred_suspects:
        lines.append(f"\n⚠  CREDENTIAL SUSPECTS ({len(cred_suspects)}) — move out of library before archiving:")
        for e in cred_suspects:
            lines.append(f"  ! {e['file']}  ({fmt_size(e['size'])})")

    lines += [
        "",
        f"Master index : {MASTER}",
        f"Removed log  : {REMOVED}",
        f"Versions     : {LIBRARY / 'versions/'}",
        f"Duplicates   : {LIBRARY / 'duplicates/'}",
        f"Copies       : {LIBRARY / 'copies/'}",
    ]

    report_text = "\n".join(lines)
    print(report_text)

    if not dry_run and not report_only:
        REPORT.write_text(report_text + "\n", encoding="utf-8")
        print(f"\n✓ report saved → library_report.txt")

    # ── noise removal ─────────────────────────────────────────────────────────
    if remove_noise and noise:
        print(f"\nArchiving {len(noise)} noise files to removed.json...")
        for f in noise:
            sz = f.stat().st_size
            if sz > 512_000:
                # Large files: store metadata only to keep removed.json manageable
                entry = {
                    "archived_at": datetime.now().isoformat(timespec="seconds"),
                    "file":        f.name,
                    "reason":      "noise — bad original filename / auto-generated stub",
                    "size":        sz,
                    "content":     None,
                    "note":        f"content omitted — file was {fmt_size(sz)}",
                }
            else:
                data, _ = load_safe(f)
                entry = {
                    "archived_at": datetime.now().isoformat(timespec="seconds"),
                    "file":        f.name,
                    "reason":      "noise — bad original filename / auto-generated stub",
                    "content":     data,
                }
            if not dry_run:
                append_removed(entry)
                f.unlink()
                print(f"  → archived: {f.name}")


if __name__ == "__main__":
    main()
