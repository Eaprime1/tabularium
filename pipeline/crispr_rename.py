#!/usr/bin/env python3
"""
Crispr-NiE Rename v2
Handles: broken filenames, (1) copies, spaces, trailing spaces, content duplicates.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

LIBRARY_JSON   = Path.home() / "pixel8" / "library" / ".json"

VERSION_PATTERN = re.compile(r"_v(\d*)$", re.IGNORECASE)


# ── bad-name detection ────────────────────────────────────────────────────────

EXPLICIT_BAD_STEMS = {
    "#", "{", "sudo apt", "from typing", "import os,",
    "# pass it", "# the", "#!", "# on your", "# test on", "# when ready",
}

BAD_PATTERNS = re.compile(
    r"^("
    r"#[!／\/\\]"                                          # shebangs
    r"|#\s*$"                                              # lone hash
    r"|\{"                                                 # lone brace
    r"|from\s+\w"                                          # python import
    r"|import\s+\w"                                        # python import
    r"|sudo\s+"                                            # shell cmd
    r"|(Absolutely|Certainly|Obviously|Essentially),?\s*$" # single-word filler
    r"|(Ah|Oh|Hi|Hey|Yes|No),\s"                          # conversational opener
    r"|(Here's\s+a|How\s+do\s+the|It\s+looks\s+like|Thank\s+you\s+for)"
    r"|(Your\s+(evolving|thoughts)|I\s+can\s+|I\s+see\s+)"
    r")",
    re.IGNORECASE,
)


def strip_leading_symbols(name: str) -> str:
    return re.sub(r"^[\W\d_]+", "", name).strip()


def is_bad_name(stem: str) -> bool:
    clean = strip_leading_symbols(stem).lower()
    if clean in EXPLICIT_BAD_STEMS:
        return True
    return bool(BAD_PATTERNS.match(strip_leading_symbols(stem)))


def is_copy(stem: str) -> bool:
    """Detect 'filename (1)', 'filename (2)' etc."""
    return bool(re.search(r"\s+\(\d+\)\s*$", stem))


# ── title extraction ──────────────────────────────────────────────────────────

TITLE_KEYS = ("title", "session_title", "name", "project_name", "session_id",
              "framework_name", "document_type", "entity_id", "id",
              "source_file", "conversation_id", "meta_title")


def _clean(s: str) -> str:
    s = re.sub(r"[^\w\s\-]", "", s).strip()
    s = re.sub(r"[\s\-]+", "_", s).lower()
    return s[:60]


def extract_title(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None

    # Check top-level keys
    for key in TITLE_KEYS:
        val = data.get(key)
        if val and isinstance(val, str) and 4 < len(val) < 100:
            c = _clean(val)
            if c and c not in ("source_file", "unknown", "none", "null"):
                return c

    # Check one level deep (first nested dict)
    for v in data.values():
        if isinstance(v, dict):
            for key in TITLE_KEYS:
                val = v.get(key)
                if val and isinstance(val, str) and 4 < len(val) < 100:
                    c = _clean(val)
                    if c and c not in ("source_file", "unknown", "none", "null"):
                        return c
            break

    # Use first top-level key as name hint
    first_key = list(data.keys())[0]
    c = _clean(first_key)
    if c and c not in ("source_file",) and len(c) > 3:
        return c

    return None


# ── filename normalization ────────────────────────────────────────────────────

def normalize_filename(stem: str) -> str:
    """Strip shell-unsafe chars, replace spaces with underscores, collapse runs."""
    # Replace full-width slashes (／ U+FF0F) with underscore
    stem = stem.replace("\uff0f", "_")
    # Remove shell-problematic characters: ' " ` $ ! & ; | < > \ * ( ) { } ^ # @
    stem = re.sub(r"['\"`$!&;|<>\\*()\{\}^#@]", "", stem)
    # Replace spaces/dashes/dots runs with single underscore
    stem = re.sub(r"[\s\-\.]+", "_", stem.strip())
    # Collapse multiple underscores
    stem = re.sub(r"_+", "_", stem)
    return stem.strip("_")


def needs_normalize(name: str) -> bool:
    """True if the filename has spaces, trailing spaces, or shell-unsafe chars."""
    return bool(re.search(r"[\s'\"`$!&;|<>\\*()\{\}^#@\uff0f]", name)) or name != name.strip()


def unique_path(dest: Path, src: Path | None = None) -> Path:
    if not dest.exists() or dest == src:
        return dest
    i = 1
    while True:
        c = dest.parent / f"{dest.stem}_{i}{dest.suffix}"
        if not c.exists():
            return c
        i += 1


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ── operations ────────────────────────────────────────────────────────────────

def do_copies(target: Path, dry_run: bool):
    print(f"\n--- COPIES: moving (1)(2)... files → copies/ ---\n")
    copies_dir = target / "copies"
    if not dry_run:
        copies_dir.mkdir(parents=True, exist_ok=True)
    moved = 0
    for f in sorted(target.iterdir()):
        if not f.is_file() or not is_copy(f.stem):
            continue
        dest = unique_path(copies_dir / f.name)
        print(f"  ⊕ {f.name}")
        print(f"    → copies/{dest.name}")
        if not dry_run:
            f.rename(dest)
        moved += 1
    if moved == 0:
        print("  (none found)")
    print(f"\n  moved={moved}")


def do_spaces(target: Path, dry_run: bool):
    print(f"\n--- SPACES: fixing spaces, quotes, shell-unsafe chars in filenames ---\n")
    renamed = 0
    for f in sorted(target.iterdir()):
        if not f.is_file() or not needs_normalize(f.name):
            continue
        new_stem = normalize_filename(f.stem)
        if new_stem == f.stem:
            continue
        dest = unique_path(target / f"{new_stem}{f.suffix}", src=f)
        print(f"  {repr(f.name)}")
        print(f"    → {dest.name}")
        if not dry_run:
            f.rename(dest)
        renamed += 1
    if renamed == 0:
        print("  (none found)")
    print(f"\n  renamed={renamed}")


def do_rename(target: Path, dry_run: bool):
    print(f"\n--- RENAME: fixing broken/fragment filenames ---\n")
    ext = next((f.suffix for f in target.iterdir() if f.is_file()), None)
    files = sorted(f for f in target.iterdir()
                   if f.is_file() and f.suffix == ext and f.parent == target)
    renamed = 0
    for f in files:
        if not is_bad_name(f.stem):
            continue
        title = extract_title(f)
        if not title:
            title = f"_unnamed_{f.stem[:20]}"
        title = re.sub(r"[^\w_\-]", "", title)
        dest = unique_path(target / f"{title}.json", src=f)
        print(f"  {f.name[:55]}")
        print(f"    → {dest.name}")
        if not dry_run:
            f.rename(dest)
        renamed += 1
    if renamed == 0:
        print("  (none found)")
    print(f"\n  renamed={renamed}")


def do_dedup(target: Path, dry_run: bool):
    print(f"\n--- DEDUP: moving content duplicates → duplicates/ ---\n")
    duplicates_dir = target / "duplicates"
    if not dry_run:
        duplicates_dir.mkdir(parents=True, exist_ok=True)
    seen: dict[str, Path] = {}
    moved = kept = 0
    for f in sorted(f for f in target.iterdir() if f.is_file() and f.parent == target):
        h = file_hash(f)
        if h in seen:
            dest = unique_path(duplicates_dir / f.name)
            print(f"  ⊕ {f.name[:50]}")
            print(f"    └─ dup of {seen[h].name[:50]}")
            if not dry_run:
                f.rename(dest)
            moved += 1
        else:
            seen[h] = f
            kept += 1
    if moved == 0:
        print("  (none found)")
    print(f"\n  unique={kept}  duplicates_moved={moved}")


def do_versions(target: Path, dry_run: bool):
    """
    _v (no number) = latest, KEEP in main.
      → move the un-suffixed counterpart to versions/ (it's older).
    _vN (numbered)  = specific older snapshot → move to versions/.
    """
    print(f"\n--- VERSIONS: moving superseded files → versions/ ---\n")
    versions_dir = target / "versions"
    if not dry_run:
        versions_dir.mkdir(parents=True, exist_ok=True)

    files = {f.name: f for f in target.iterdir() if f.is_file() and f.parent == target}
    to_move: list[Path] = []

    for name, f in files.items():
        stem = f.stem
        # Case 1: _vN (numbered) → old snapshot, move it
        if re.search(r"_v\d+$", stem, re.IGNORECASE):
            to_move.append(f)
            continue
        # Case 2: _v (no number) = latest → find un-suffixed counterpart and move that
        if re.search(r"_v$", stem, re.IGNORECASE):
            older_stem = re.sub(r"_v$", "", stem, flags=re.IGNORECASE)
            older_name = older_stem + f.suffix
            if older_name in files:
                to_move.append(files[older_name])

    moved = 0
    for f in sorted(set(to_move)):
        dest = unique_path(versions_dir / f.name)
        print(f"  ↓ {f.name}")
        print(f"    → versions/{dest.name}")
        if not dry_run:
            f.rename(dest)
        moved += 1

    if moved == 0:
        print("  (none found)")
    print(f"\n  moved={moved}")


def main():
    dry_run   = "--dry-run" in sys.argv
    do_all    = not any(a in sys.argv for a in ("--copies", "--spaces", "--rename", "--dedup", "--versions"))
    target_a  = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
    target    = Path(target_a).expanduser().resolve() if target_a else LIBRARY_JSON

    print(f"\n=== CRISPR RENAME v2 {'[DRY RUN] ' if dry_run else ''}===")
    print(f"Target: {target}")

    if do_all or "--copies" in sys.argv:
        do_copies(target, dry_run)
    if do_all or "--spaces" in sys.argv:
        do_spaces(target, dry_run)
    if do_all or "--rename" in sys.argv:
        do_rename(target, dry_run)
    if do_all or "--versions" in sys.argv:
        do_versions(target, dry_run)
    if do_all or "--dedup" in sys.argv:
        do_dedup(target, dry_run)


if __name__ == "__main__":
    main()
