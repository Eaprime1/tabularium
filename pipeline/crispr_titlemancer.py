#!/usr/bin/env python3
"""
Crispr-NiE Titlemancer v1
Reads VETTING files, extracts title from content, suggests group-prefixed names.

Usage:
  python3 ~/crispr_titlemancer.py .txt               # show rename plan (dry run)
  python3 ~/crispr_titlemancer.py .txt --apply       # execute renames
  python3 ~/crispr_titlemancer.py .txt --limit 30    # first N files only
  python3 ~/crispr_titlemancer.py .txt --group VETTING  # target group (default)
  python3 ~/crispr_titlemancer.py .txt --format tsv  # tsv output for piping
"""
import json
import re
import sys
from pathlib import Path

LIBRARY_BASE = Path.home() / "pixel8/library"

# ── args ────────────────────────────────────────────────────────────────────
EXT      = next((a for a in sys.argv[1:] if a.startswith(".")), ".txt")
_args    = [a.strip() for a in sys.argv]   # strip any \r contamination
APPLY    = "--apply"  in _args
_mi      = _args.index("--mode") if "--mode" in _args else -1
CLEAN    = _mi >= 0 and _mi + 1 < len(_args) and _args[_mi + 1] == "clean"
LIMIT    = None
GROUP    = "VETTING"
FMT      = "report"
SKIP_NOS: set[int] = set()

for i, a in enumerate(sys.argv[1:], 1):
    if a == "--limit"  and i < len(sys.argv) - 1: LIMIT = int(sys.argv[i + 1])
    if a == "--group"  and i < len(sys.argv) - 1: GROUP = sys.argv[i + 1]
    if a == "--format" and i < len(sys.argv) - 1: FMT   = sys.argv[i + 1]
    if a == "--skip"   and i < len(sys.argv) - 1:
        SKIP_NOS = {int(x) for x in sys.argv[i + 1].split(",")}

_dot  = LIBRARY_BASE / f".{EXT.lstrip('.')}"
_bare = LIBRARY_BASE / EXT.lstrip(".")
LIB_DIR = _dot if _dot.is_dir() else _bare
ext_name = EXT.lstrip(".")
# crispr_consolidate.py (the original .json consolidator) predates the _ext
# suffix convention and writes the unsuffixed library_master.json — every
# later consolidator (_py, _md, _txt, ...) uses the _ext-suffixed name.
MASTER    = (LIB_DIR / "library_master.json" if ext_name == "json"
             else LIB_DIR / f"library_master_{ext_name}.json")
AI_CACHE  = LIB_DIR / "ai_titles.json"

# ── AI title cache (populated by crispr_ai_title.py) ────────────────────────
def _load_ai_cache() -> dict:
    if AI_CACHE.exists():
        try:
            return json.loads(AI_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

_AI_TITLES: dict = _load_ai_cache()

# ── content-based group detection ────────────────────────────────────────────
CONTENT_GROUPS = [
    ("CODE",     re.compile(r"^(import\s+\w|from\s+\w.*import|#!/|def\s+\w|class\s+\w)", re.MULTILINE)),
    ("DATA",     re.compile(r"^\s*[\{\[]", re.MULTILINE)),
    ("PRIME",    re.compile(r"PINNACLE PRIME|ALPHA.PRIME|prime codex|Prime Progression|PRIME_CODEX", re.I)),
    ("CODEX",    re.compile(r"\bCODEX\b|Codex of Prime|Cross.Reference Standards|Front.Matter", re.I)),
    ("KA",       re.compile(r"\bKa\b.{0,10}[Pp]ressure|Ka Pressure|ka_pressure", re.I)),
    ("SACRED",   re.compile(r"consciousness.*collab|EMBER|mythology foundation|tantrum entity|Safe Bookend|Bookend Tantrum|Sacred Empire|Phoenix Protocol|∰", re.I)),
    ("MOAV",     re.compile(r"\bMOAV\b|moav.research|research.consortium.*moav", re.I)),
    ("SARGASSO", re.compile(r"[Ss]argasso", re.I)),
    ("DIAMOND",  re.compile(r"[Dd]iamond.of.[Aa]ces|Diamond of Aces", re.I)),
    ("PIXEL8",   re.compile(r"PIXEL\s*Domos|pixelator|pixel8\s", re.I)),
    ("TERMUX",   re.compile(r"Termux.*setup|termux.*universe|Dynamics\s*/", re.I)),
    ("SESSION",  re.compile(r"Sanitized summary.*Claude|AI System Initialized", re.I)),
    ("MISSIONS", re.compile(r"mission|front.matter.*expert|strategic.*consciousness|distributed.*consciousness", re.I)),
    ("UNEXUS",   re.compile(r"\bUNEXUS\b|Radix\s+Repo|ontological.seed", re.I)),
]


def detect_content_group(text: str) -> str | None:
    sample = text[:600]
    for group, pat in CONTENT_GROUPS:
        if pat.search(sample):
            return group
    return None


_CONVERSATIONAL = re.compile(
    r"^(i can|i can'|it looks|how do |what is|when did|where is|why is|"
    r"you're|you are|we can|they |i'm |i am |"
    r"thank you|certainly!|absolutely,|ah,\s|sure,|here is|let me)",
    re.IGNORECASE,
)

def stem_is_title(stem: str) -> tuple[bool, str]:
    """Return (is_title, confidence) for the filename stem."""
    clean = re.sub(r'^[\W_]+', '', stem).strip()
    words = re.split(r'[\s_\-]+', clean)
    # 5+ words that aren't conversational → high confidence real title
    if len(words) >= 5 and not _CONVERSATIONAL.match(clean):
        return True, "high"
    # 3-4 words non-conversational → medium
    if len(words) >= 3 and not _CONVERSATIONAL.match(clean):
        return True, "medium"
    # 1-2 word noun stems (Android, Godels Incompleteness) → still usable as title
    if len(words) >= 1 and not _CONVERSATIONAL.match(clean):
        return True, "medium"
    # Conversational openers → need content extraction
    return False, "low"


def extract_title(path: Path) -> tuple[str, str, str]:
    """Return (title_text, source, confidence)."""
    # AI cache takes highest priority — human-verified or AI-extracted real titles
    if path.name in _AI_TITLES:
        return _AI_TITLES[path.name], "ai", "high"
    stem = path.stem
    is_title, conf = stem_is_title(stem)
    if is_title:
        return stem, "stem", conf
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("# "):
                return line[2:].strip(), "heading", "medium"
            if line.startswith("## "):
                return line[3:].strip(), "heading", "medium"
            if set(line) <= set("=-#~*_/"):
                continue
            if line.startswith(("import ", "from ", "#!/", "{", "[", "*")):
                continue
            return line, "content", "low"
    except Exception:
        pass
    return stem, "stem", "low"


def clean_name(title: str, group: str, orig_ext: str = ".txt") -> str:
    """Convert title + group into a clean snake_case filename."""
    # Strip markdown markers and emoji
    title = re.sub(r'^#+\s*', '', title)
    title = re.sub(r'[\U0001F000-\U0010FFFF]', '', title)  # emoji / symbols
    title = re.sub(r'[∰◊€π¿🌌∞∋∫∂∆∇√∞∑∏]', '', title)     # math/special
    title = re.sub(r'[^\w\s\-]', ' ', title)
    title = re.sub(r'\s+', '_', title.strip())
    title = re.sub(r'_+', '_', title).strip('_').lower()
    title = title[:50]

    prefix = group.lower()
    proposed = f"{prefix}_{title}{orig_ext}"
    return proposed


# Stems already starting with these prefixes (+ underscore) are considered named.
# Titlemancer will skip them if they're also clean snake_case.
_NAMED_PREFIXES = {
    "vetting","reference","utility","code","data","sacred","prime","codex",
    "ka","moav","missions","pixel8","termux","unexus","session","terminal",
    "quicknote","dirlist","dungeon","seek","svg","research","diamond",
    "roundtable","sargasso","pandora","liminal","quantum","deep_dive","end_matter",
}
def already_named(stem: str) -> bool:
    """True if stem already starts with a known group prefix."""
    s = stem.lower()
    return any(s.startswith(pfx + "_") for pfx in _NAMED_PREFIXES)


def read_master_vetting(group: str) -> list[dict]:
    if not MASTER.exists():
        print(f"Master not found: {MASTER}\nRun stage 3 first.")
        sys.exit(1)
    data = json.loads(MASTER.read_text(encoding="utf-8"))
    return [e for e in data.get("index", []) if e.get("group") == group]


def main():
    entries = read_master_vetting(GROUP)
    if LIMIT:
        entries = entries[:LIMIT]

    print(f"\n=== CRISPR TITLEMANCER ({EXT}) ===")
    print(f"Library : {LIB_DIR}")
    print(f"Group   : {GROUP}  ({len(entries)} files)")
    print(f"Mode    : {'APPLY renames' if APPLY else 'DRY RUN — pass --apply to rename'}\n")

    plan = []  # (path, proposed, group, title, source, confidence)

    for e in entries:
        fpath = LIB_DIR / e["file"]
        if not fpath.exists():
            continue
        try:
            text = fpath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            text = ""

        # Skip files that are already properly group-prefixed and clean
        if already_named(fpath.stem):
            continue

        content_group           = detect_content_group(text) or GROUP
        title, src, conf        = extract_title(fpath)
        if CLEAN and conf == "low":
            continue  # --mode clean: skip messy content-extraction cases
        proposed                = clean_name(title, content_group, fpath.suffix)

        if proposed == fpath.name:
            continue
        target = LIB_DIR / proposed
        if target.exists() and target != fpath:
            proposed = proposed.replace(fpath.suffix, f"_2{fpath.suffix}")

        plan.append((fpath, proposed, content_group, title, src, conf))

    # Sort: high confidence first, then medium, then low
    _order = {"high": 0, "medium": 1, "low": 2}
    plan.sort(key=lambda x: _order.get(x[5], 3))

    if FMT == "tsv":
        print("ORIGINAL\tPROPOSED\tGROUP\tCONF\tTITLE")
        for fpath, proposed, grp, title, src, conf in plan:
            print(f"{fpath.name}\t{proposed}\t{grp}\t{conf}\t{title[:60]}")
        return

    mode_note = " [--mode clean: high+medium only]" if CLEAN else " [use --mode clean for safe-only renames]"
    print(f"  Proposed names use underscores. Pass --apply to rename.{mode_note}\n")
    cur_conf = None
    for i, (fpath, proposed, grp, title, src, conf) in enumerate(plan, 1):
        if conf != cur_conf:
            cur_conf = conf
            label = {"high": "── HIGH confidence (stem is the title / AI-extracted)", "medium": "── MEDIUM confidence (3-4 word stem)", "low": "── LOW confidence (content/heading extracted)"}.get(conf, conf)
            print(f"\n  {label}")
        print(f"  {i:>3}. [{grp}]  {proposed}")
        print(f"       from: {fpath.name[:70]}")
        if src != "stem":
            print(f"       via:  {title[:70]}  ({src})")

    print(f"\n{'─'*70}")
    print(f"  {len(plan)} renames proposed")

    if APPLY and plan:
        print("\nApplying renames...")
        renamed = 0
        for idx, (fpath, proposed, grp, title, src, conf) in enumerate(plan, 1):
            if idx in SKIP_NOS:
                print(f"  — skip #{idx}: {fpath.name[:50]}")
                continue
            target = LIB_DIR / proposed
            if target.exists():
                print(f"  ✗ skip (exists): {proposed}")
                continue
            fpath.rename(target)
            print(f"  ✓ {fpath.name[:40]} → {proposed}")
            renamed += 1
        print(f"\n✓ {renamed} files renamed — re-run stage 3 to update master index")
    elif plan:
        print("\nRun with --apply to execute renames.")


if __name__ == "__main__":
    main()
