# Guide: Antigravity CLI (agy) on Termux + PRoot Distro

> Completed: 2026-07-08 · Environment: Pixel phone, Termux, PRoot Debian 13 (aarch64)

## What This Solves

Running `agy` (Google Antigravity CLI) inside a PRoot Distro environment on Android.
Standard install methods fail because:
- `pkg install glibc` blocks root (PRoot runs as root)
- The official binary needs glibc's loader, not Android's linker
- Termux's `LD_PRELOAD` breaks glibc processes

## Outcome

`agy 1.1.0` running from both:
- **Termux shell**: `~/.local/bin/agy-run`
- **Inside PRoot**: `/root/.local/bin/agy-run` (or `agy` shell function)
- **Python subprocess**: `["/root/.local/bin/agy-run"]` — works in crispr_ai_title.py

---

## Step 1 — Install glibc (bypassing pkg root block)

`pkg install glibc` refuses to run as root. Download and extract the `.deb` directly:

```bash
mkdir -p /tmp/glibc-install && cd /tmp/glibc-install
curl -fL "https://packages.termux.dev/apt/termux-glibc/pool/stable/g/glibc/glibc_2.43_aarch64.deb" -o glibc.deb
dpkg-deb -x glibc.deb extracted/
cp -a extracted/data/data/com.termux/files/usr/glibc /data/data/com.termux/files/usr/
```

Verify:
```bash
test -x /data/data/com.termux/files/usr/glibc/lib/ld-linux-aarch64.so.1 && echo OK
test -f /data/data/com.termux/files/usr/glibc/lib/libc.so.6 && echo OK
```

---

## Step 2 — Install official agy binary (from inside PRoot)

```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash
# Installs to ~/.local/bin/agy (157MB ARM64 ELF)
```

No VA39 patch needed for v1.1.0 — the binary works directly with glibc.

---

## Step 3 — Create PRoot wrapper

```bash
cat > ~/.local/bin/agy-run << 'EOF'
#!/bin/sh
G=/data/data/com.termux/files/usr/glibc/lib
unset LD_PRELOAD
unset LD_LIBRARY_PATH
export GODEBUG=netdns=go
export SSL_CERT_FILE=/data/data/com.termux/files/usr/etc/tls/cert.pem
exec $G/ld-linux-aarch64.so.1 --library-path $G \
  /root/.local/bin/agy "$@"
EOF
chmod +x ~/.local/bin/agy-run
~/.local/bin/agy-run --version  # → 1.1.0
```

Add to `~/.bashrc` (shell convenience):
```bash
export PATH="$HOME/.local/bin:$PATH"
agy() { hash -r; ~/.local/bin/agy-run "$@"; }
a()   { hash -r; ~/.local/bin/agy-run "$@"; }
```

---

## Step 4 — Create Termux-side wrapper (for running from Termux shell)

From inside PRoot, create a wrapper in the Termux home:

```bash
TDEST=/data/data/com.termux/files/home/.local/bin

# Copy official binary to Termux-accessible path
cp ~/.local/bin/agy $TDEST/agy-official

# Create Termux-side wrapper (uses proot for /dev/tty)
cat > $TDEST/agy-run << 'WEOF'
#!/data/data/com.termux/files/usr/bin/sh
G=/data/data/com.termux/files/usr/glibc/lib
P=/data/data/com.termux/files/usr/bin/proot
unset LD_PRELOAD
unset LD_LIBRARY_PATH
export GODEBUG=netdns=go
export SSL_CERT_FILE=/data/data/com.termux/files/usr/etc/tls/cert.pem
exec $P \
  -b /data/data/com.termux/files/usr/etc/resolv.conf:/etc/resolv.conf \
  $G/ld-linux-aarch64.so.1 --library-path $G \
  /data/data/com.termux/files/home/.local/bin/agy-official "$@"
WEOF
chmod +x $TDEST/agy-run
```

From Termux shell: `~/.local/bin/agy-run --version` → `1.1.0`
Interactive: `~/.local/bin/agy-run` (open in a dedicated Termux session for full TUI)

---

## Updating agy

When a new version releases:
```bash
# Inside PRoot:
curl -fsSL https://antigravity.google/cli/install.sh | bash
cp ~/.local/bin/agy /data/data/com.termux/files/home/.local/bin/agy-official
~/.local/bin/agy-run --version
```

---

## Key Files

| Path | Purpose |
|------|---------|
| `/root/.local/bin/agy` | Official Google binary (157MB ARM64) |
| `/root/.local/bin/agy-run` | PRoot wrapper — glibc loader |
| `/data/data/com.termux/files/home/.local/bin/agy-official` | Copy for Termux-side use |
| `/data/data/com.termux/files/home/.local/bin/agy-run` | Termux wrapper — proot + glibc |
| `/data/data/com.termux/files/usr/glibc/lib/` | glibc 2.43 (manually extracted) |

---

## Why VA39 Patch Wasn't Needed

agy v1.1.0 appears to no longer use TCMalloc with 48-bit VA assumptions. The patch
script (`patch_agy_va39.py`) found 0 TCMalloc patches — only the `faccessat2` syscall
fix applied (1 match). The binary runs correctly without the TCMalloc patch.

If a future version fails with `MmapAligned() failed`, re-run `~/patch_agy_va39.py`.

---

## Use in crispr_ai_title.py

The script and library both live in **Termux home** — run from the Termux shell, not inside PRoot.

```python
# Termux-side wrapper — subprocess cannot use shell aliases/functions
AI_CMD = ["/data/data/com.termux/files/home/.local/bin/agy-run"]
```

Run the AI title pass from Termux shell (`~ $`):
```bash
python3 ~/crispr_ai_title.py .txt               # dry run — show snippets
python3 ~/crispr_ai_title.py .txt --limit 5 --apply   # test 5 files first
python3 ~/crispr_ai_title.py .txt --apply        # full pass (45 VETTING files)
```
