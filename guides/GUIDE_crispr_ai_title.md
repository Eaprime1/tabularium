# Crispr-NiE — AI Title Extractor: Setup Guide

## What We're Building

A personal text library (~210 .txt files, Termux on Pixel 8a Android) has 45 files
in a `VETTING` group — uncategorized, often with meaningless or AI-opener filenames.

We built `crispr_ai_title.py` (at `~/crispr_ai_title.py`) to:
1. Read the first ~900 chars of each VETTING file
2. Ask an AI to generate a clean 3-7 word title
3. Save results to `ai_titles.json` in the library folder
4. The Titlemancer (`crispr_titlemancer.py`) reads this cache and proposes
   group-prefixed snake_case renames like `sacred_bookend_tantrum_entity.txt`

## Installing Antigravity CLI (`agy`) on Termux

The command name after install is `agy` (also aliased as `a`).

### Option A: wallentx release (RECOMMENDED — no proot, no glibc, no wrappers)

wallentx packaged the Brajesh2022 patching work as standalone versioned releases
with `agy update` support. Much simpler than the manual method.

Go to: https://github.com/wallentx/antigravity-cli-termux/releases

Download the latest release tarball for arm64-android and extract to `~/.local/bin/`.

Or use the wallentx installer (if available):
```bash
curl -fsSL https://raw.githubusercontent.com/wallentx/antigravity-cli-termux/dev/install.sh | bash
```

### Option B: Brajesh2022 auto-installer (manual method, requires glibc + proot)

Source: https://gist.github.com/Brajesh2022/Running-Antigravity-CLI-on-Termux.md

Prerequisites:
```bash
pkg install python proot curl ca-certificates
# Verify glibc is present:
test -x /data/data/com.termux/files/usr/glibc/lib/ld-linux-aarch64.so.1
test -f /data/data/com.termux/files/usr/glibc/lib/libc.so.6
```

Step 0 — Install official Antigravity binary:
```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash
```

Auto-installer for Termux compatibility layer:
```bash
curl -fsSL https://raw.githubusercontent.com/Brajesh2022/antigravity-cli-termux/dev/install.sh | bash
```

Expected files after setup:
```
~/.local/bin/agy        # original official binary
~/.local/bin/agy.va39  # patched binary (TCMalloc → 39-bit VA)
~/.local/bin/agy-va39  # wrapper script (proot + glibc env)
~/.local/lib/agy-glibc/libc.so{,.6}
~/patch_agy_va39.py    # reusable patch script
```

Verify:
```bash
agy-va39 --version
agy --version
```

### Option C: Gemini or other CLI

Any CLI that accepts a prompt as argument works. Change `AI_CMD` in crispr_ai_title.py.

## The AI Call in the Script

In `~/crispr_ai_title.py`, the command is set here:

```python
AI_CMD = ["agy"]   # ← change to ["agy"], ["gemini"], ["llm", "-m", "gemini-pro"], etc.
```

After installing `agy`, update this to `["agy"]` (it already is the default target).

## The Prompt We Send

```
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
[first 900 chars of file]
---

Title:
```

## Running It (once agy is working)

```bash
# Dry run — shows snippets, no AI calls
python3 ~/crispr_ai_title.py .txt --limit 10

# Live — calls AI, saves ai_titles.json incrementally
python3 ~/crispr_ai_title.py .txt --apply

# Review cache
python3 ~/crispr_ai_title.py .txt --show-cache

# Then run Titlemancer — AI titles appear as HIGH confidence
python3 ~/crispr_titlemancer.py .txt --group VETTING --mode clean
python3 ~/crispr_titlemancer.py .txt --group VETTING --mode clean --apply
```

## Environment Notes

- Device: Termux on Pixel 8a (Android 14, not rooted)
- Python 3.13 via Termux packages
- No `/tmp` access — use `$TMPDIR` (`/data/data/com.termux/files/usr/tmp`)
- Library path: `/data/data/com.termux/files/home/pixel8/library/.txt/`
- Master index: `library_master_txt.json` (built by `crispr_consolidate_txt.py`)

## Status

- 2026-07-07: wallentx option identified as the correct path (no proot/glibc needed)
- 2026-07-08: PDF guide read and confirmed — wallentx is the better install
- Remaining .txt VETTING: 45 files (all vetting_-prefixed, ready for AI title pass)

---
*Updated 2026-07-08 — PDF source: "Antigravity CLI on Termux: Auto-Installer and Manual Patching Guide" (Brajesh2022)*
