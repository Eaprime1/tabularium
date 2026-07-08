#!/usr/bin/env python3
"""
Crispr-NiE Repair — Fix invalid JSON files in the library.
Backs up originals before any write.
"""
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

LIBRARY_JSON = Path.home() / "pixel8" / "library" / ".json"
BACKUP_DIR = LIBRARY_JSON / "repair_backups"


def backup(path: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    dest = BACKUP_DIR / f"{path.stem}_{ts}.bak"
    shutil.copy2(path, dest)
    return dest


def strip_trailing(text: str) -> str:
    """Keep only the first valid JSON value, drop everything after."""
    decoder = json.JSONDecoder()
    try:
        _, idx = decoder.raw_decode(text.lstrip())
        return text.lstrip()[:idx].rstrip() + "\n"
    except json.JSONDecodeError:
        return text


def fix_inline_annotations(text: str) -> str:
    """Fix: "word" (annotation) → "word (annotation)" in JSON values."""
    return re.sub(r'"([^"]+)"\s+\(([^)]+)\)', r'"\1 (\2)"', text)


def close_truncated(text: str) -> str:
    """Close truncated JSON using a stack so closers emit in correct LIFO order."""
    stack = []
    in_string = skip_next = False
    for ch in text:
        if skip_next:
            skip_next = False
            continue
        if ch == "\\" and in_string:
            skip_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            stack.append("}")
        elif ch == "}" and stack and stack[-1] == "}":
            stack.pop()
        elif ch == "[":
            stack.append("]")
        elif ch == "]" and stack and stack[-1] == "]":
            stack.pop()
    result = text.rstrip()
    if in_string:
        result += '"'
    result += "".join(reversed(stack))
    return result + "\n"


def fix_annotations_then_close(text: str) -> str:
    return close_truncated(fix_inline_annotations(text))


REPAIRS = {
    "beasis_conversation_handoff_package_v.json":    fix_inline_annotations,
    "conversation-essence-json (1).json":            strip_trailing,
    "conversation-essence-json.json":               strip_trailing,
    "lexeme_consciousness_concordance.json":         strip_trailing,
    "lexeme_consciousness_concordance_v1.json":      fix_annotations_then_close,
    "lexeme_consciousness_spectrum_database.json":   fix_inline_annotations,
    "lexeme_consciousness_spectrum_upgraded.json":   close_truncated,
    "moav_research_welcome.json":                    close_truncated,
}


def repair(path: Path, fix_fn, dry_run: bool) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    fixed = fix_fn(text)
    result = {"file": path.name, "status": "unknown", "note": ""}

    try:
        json.loads(fixed)
        result["status"] = "fixed"
    except json.JSONDecodeError as e:
        result["status"] = "still_invalid"
        result["note"] = f"line {e.lineno}: {e.msg}"
        return result

    if not dry_run:
        bak = backup(path)
        path.write_text(fixed, encoding="utf-8")
        result["note"] = f"backup → {bak.name}"

    return result


def main():
    dry_run = "--dry-run" in sys.argv
    target_arg = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
    target = Path(target_arg).expanduser().resolve() if target_arg else LIBRARY_JSON

    print(f"\n=== CRISPR REPAIR {'[DRY RUN] ' if dry_run else ''}===")
    print(f"Target: {target}\n")

    fixed = invalid = missing = 0
    for name, fix_fn in REPAIRS.items():
        path = target / name
        if not path.exists():
            print(f"  · {name:<50} [not found]")
            missing += 1
            continue
        r = repair(path, fix_fn, dry_run)
        icon = "✓" if r["status"] == "fixed" else "✗"
        print(f"  {icon} {name}")
        if r["note"]:
            print(f"    └─ {r['status']}: {r['note']}")
        else:
            print(f"    └─ {r['status']}")
        if r["status"] == "fixed":
            fixed += 1
        else:
            invalid += 1

    print(f"\n  fixed={fixed}  still_invalid={invalid}  not_found={missing}")
    if not dry_run and fixed:
        print(f"  backups → {BACKUP_DIR}")


if __name__ == "__main__":
    main()
