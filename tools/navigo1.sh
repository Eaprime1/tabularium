#!/data/data/com.termux/files/usr/bin/bash
# navigo1.sh — Crispr-NiE pipeline launcher
#
# Usage (interactive):    bash ~/navigo1.sh
# Usage (from Claude !):  bash ~/navigo1.sh 2
#                         bash ~/navigo1.sh a
#
# ── NOTES ────────────────────────────────────────────────────────────────────
# Add session notes below. These are visible when you run option n.
# ──────────────────────────────────────────────────────────────────────────────

NOTES_FILE="$HOME/navigo_notes.md"

RG_LINK="/data/data/com.termux/files/usr/lib/node_modules/@anthropic-ai/claude-code/vendor/ripgrep/arm64-android/rg"
RG_BIN="/data/data/com.termux/files/usr/bin/rg"

fix_ripgrep() {
    python3 -c "
import os
t = '$RG_LINK'
b = '$RG_BIN'
os.makedirs(os.path.dirname(t), exist_ok=True)
if os.path.lexists(t):
    os.remove(t)
os.symlink(b, t)
print('ripgrep ok:', os.readlink(t))
"
}

show_menu() {
    echo ""
    echo "╔══════════════════════════════════╗"
    echo "║  NAVIGO-1 — Library Pipeline     ║"
    echo "╚══════════════════════════════════╝"
    echo ""
    echo "  1) Fix ripgrep symlink"
    echo "  2) Run .md consolidator"
    echo "  3) Run .md analyzer  (VETTING report)"
    echo "  4) Sample VETTING clusters"
    echo "  5) Peek cluster contents"
    echo "  6) Push scripts to tabularium"
    echo "  a) ALL: fix + consolidate + analyze"
    echo "  n) Show notes"
    echo ""
}

# Accept choice as argument (for non-interactive use from Claude ! prefix)
if [ -n "$1" ]; then
    choice="$1"
    show_menu
    echo "Running: $choice"
    echo ""
else
    show_menu
    read -rp "Choice: " choice
fi

case "$choice" in
    1) fix_ripgrep ;;
    2) python3 ~/crispr_consolidate_md.py ;;
    3) python3 ~/crispr_analyze_md.py ;;
    4) python3 ~/sample_clusters.py ;;
    5) python3 ~/peek_clusters.py ;;
    6) python3 ~/push_tabularium.py ;;  # loose home-root script, not tracked in this repo — copies ~/crispr_*.py into ~/tabularium for commit
    a|A)
        fix_ripgrep
        echo ""
        python3 ~/crispr_consolidate_md.py
        echo ""
        python3 ~/crispr_analyze_md.py
        ;;
    n|N)
        if [ -f "$NOTES_FILE" ]; then
            cat "$NOTES_FILE"
        else
            echo "No notes yet. Create ~/navigo_notes.md to add notes."
        fi
        ;;
    *) echo "Unknown: $choice"; exit 1 ;;
esac
