#!/usr/bin/env python3
"""
Crispr-NiE AI Title Extractor v1
Reads VETTING files, asks AI for a clean title, saves ai_titles.json.
Titlemancer reads this cache as its highest-priority title source.

Usage:
  python3 ~/crispr_ai_title.py .txt               # dry run — show snippet + prompt
  python3 ~/crispr_ai_title.py .txt --apply        # call AI, save ai_titles.json
  python3 ~/crispr_ai_title.py .txt --limit 10     # first N files only
  python3 ~/crispr_ai_title.py .txt --group VETTING  # target group (default)
  python3 ~/crispr_ai_title.py .txt --show-cache   # print current ai_titles.json

AI backend: agy (Antigravity CLI / Gemini).
Adjust AI_CMD below if the CLI interface differs.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

LIBRARY_BASE = Path.home() / "pixel8/library"

# ── args ────────────────────────────────────────────────────────────────────
EXT   = next((a for a in sys.argv[1:] if a.startswith(".")), ".txt")
_args = [a.strip() for a in sys.argv]
APPLY = "--apply" in _args
SHOW  = "--show-cache" in _args
GROUP = "VETTING"
LIMIT = None

for i, a in enumerate(sys.argv[1:], 1):
    if a == "--limit" and i < len(sys.argv) - 1:
        LIMIT = int(sys.argv[i + 1])
    if a == "--group" and i < len(sys.argv) - 1:
        GROUP = sys.argv[i + 1]

_dot  = LIBRARY_BASE / f".{EXT.lstrip('.')}"
_bare = LIBRARY_BASE / EXT.lstrip(".")
LIB_DIR   = _dot if _dot.is_dir() else _bare
ext_name  = EXT.lstrip(".")
MASTER    = LIB_DIR / f"library_master_{ext_name}.json"
AI_CACHE  = LIB_DIR / "ai_titles.json"

# ── AI backend ──────────────────────────────────────────────────────────────
# antigravity sends the first positional argument as the prompt.
# Adjust this list if your CLI flags differ (e.g. ["ag", "--prompt"]).
AI_CMD = ["agy"]

TITLE_PROMPT = """\
You are titling documents from a personal knowledge library. Domain vocabulary:
- "consciousness" = a technical/sacred system term (not generic awareness)
- PRIME / CODEX = philosophical progression frameworks
- SACRED / EMBER / BOOKEND TANTRUM = mythological/ritual system names
- MOAV = research consortium project
- KA = pressure/energy system
- PIXEL8 / Termux = Android dev environment
- SARGASSO = exploratory archive
Preserve these domain terms in titles. Do NOT paraphrase them into generic words.

Read this excerpt. Reply with ONLY a 3-7 word descriptive title.
No quotes, no punctuation at the end, no explanation.

---
{snippet}
---

Title:"""

SNIPPET_LEN = 900  # chars to send to AI per file


# ── helpers ─────────────────────────────────────────────────────────────────

def load_master(group: str) -> list[dict]:
    if not MASTER.exists():
        print(f"Master not found: {MASTER}\nRun stage 3 first.")
        sys.exit(1)
    data = json.loads(MASTER.read_text(encoding="utf-8"))
    return [e for e in data.get("index", []) if e.get("group") == group]


def load_cache() -> dict:
    if AI_CACHE.exists():
        try:
            return json.loads(AI_CACHE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_cache(cache: dict):
    AI_CACHE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def extract_snippet(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        # Strip leading blank lines and separator-only lines
        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if set(stripped) <= set("=-#~*_/"):
                continue
            lines.append(line)
            if sum(len(l) for l in lines) >= SNIPPET_LEN:
                break
        return "\n".join(lines)[:SNIPPET_LEN]
    except Exception:
        return ""


def call_ai(snippet: str) -> str | None:
    prompt = TITLE_PROMPT.format(snippet=snippet)
    try:
        result = subprocess.run(
            AI_CMD + [prompt],
            capture_output=True, text=True, timeout=60,
        )
        raw = result.stdout.strip()
        if not raw and result.stderr.strip():
            return None  # AI error
        # Clean up: strip quotes, "Title:", trailing punctuation
        raw = re.sub(r'^["\']|["\']$', '', raw)
        raw = re.sub(r'^Title:\s*', '', raw, flags=re.IGNORECASE)
        raw = raw.strip().strip('.')
        return raw if raw else None
    except subprocess.TimeoutExpired:
        print("  [timeout]")
        return None
    except FileNotFoundError:
        print(f"  [AI command not found: {AI_CMD[0]}]")
        return None


# ── main ────────────────────────────────────────────────────────────────────

def main():
    if SHOW:
        cache = load_cache()
        if not cache:
            print("ai_titles.json is empty or missing.")
            return
        print(f"ai_titles.json — {len(cache)} entries:\n")
        for fname, title in sorted(cache.items()):
            print(f"  {fname[:55]:<55}  →  {title}")
        return

    entries = load_master(GROUP)
    if LIMIT:
        entries = entries[:LIMIT]

    cache = load_cache()
    already = set(cache.keys())

    # Only process files not already in cache
    pending = [e for e in entries if e["file"] not in already]

    print(f"\n=== CRISPR AI TITLE EXTRACTOR ({EXT}) ===")
    print(f"Library  : {LIB_DIR}")
    print(f"Group    : {GROUP}  ({len(entries)} files, {len(pending)} uncached)")
    print(f"Cache    : {AI_CACHE.name}  ({len(already)} existing entries)")
    print(f"Mode     : {'APPLY — calling AI' if APPLY else 'DRY RUN — pass --apply to call AI'}\n")

    if not pending:
        print("All files already in cache. Run --show-cache to review.")
        return

    errors = 0
    for i, e in enumerate(pending, 1):
        fpath = LIB_DIR / e["file"]
        if not fpath.exists():
            continue

        snippet = extract_snippet(fpath)
        if not snippet:
            print(f"  {i:>3}. [empty] {fpath.name[:60]}")
            continue

        print(f"  {i:>3}. {fpath.name[:60]}")
        print(f"       snippet: {snippet[:80].replace(chr(10), ' ')!r}")

        if not APPLY:
            continue

        title = call_ai(snippet)
        if title:
            cache[e["file"]] = title
            print(f"       → {title}")
        else:
            print(f"       → [no result]")
            errors += 1

        # Save incrementally so a crash doesn't lose progress
        if i % 5 == 0:
            save_cache(cache)

    if APPLY:
        save_cache(cache)
        new_entries = len(cache) - len(already)
        print(f"\n✓ {new_entries} new titles saved → {AI_CACHE}")
        if errors:
            print(f"  {errors} files returned no result — re-run to retry")
    else:
        print(f"\n  Pass --apply to call AI on {len(pending)} files.")


if __name__ == "__main__":
    main()
