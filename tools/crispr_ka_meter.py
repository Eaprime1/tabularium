#!/usr/bin/env python3
"""
CRISPR-NiE Ka Meter v1 — Vested Sweat Equity & Token Usage Tracker
Philosophical & physical measurement of human-AI co-creation.
"""
import sys
import json
import os
from pathlib import Path

# Constants for token estimation
# Standard approximation: 1 token ~= 4 characters for English text
CHAR_TO_TOKEN_RATIO = 4.0

def estimate_tokens(val) -> int:
    if isinstance(val, int):
        return max(1, int(val / CHAR_TO_TOKEN_RATIO))
    if not val:
        return 0
    return max(1, int(len(str(val)) / CHAR_TO_TOKEN_RATIO))

def analyze_transcript(transcript_path: Path):
    metrics = {
        "user": {"chars": 0, "tokens": 0},
        "model": {"chars": 0, "tokens": 0},
        "system": {"chars": 0, "tokens": 0},
        "total_steps": 0
    }
    
    if not transcript_path.exists():
        return None
        
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                step = json.loads(line)
                metrics["total_steps"] += 1
                source = step.get("source", "SYSTEM").lower()
                
                # If source is model, we count thinking, content, and tool calls
                char_count = 0
                if source == "model":
                    char_count += len(step.get("thinking", ""))
                    char_count += len(step.get("content", ""))
                    # Add tool calls representation length
                    tool_calls = step.get("tool_calls", [])
                    if tool_calls:
                        char_count += len(json.dumps(tool_calls))
                elif "user" in source:
                    char_count += len(step.get("content", ""))
                else: # SYSTEM
                    char_count += len(step.get("content", ""))
                    
                # Map to categories
                if source == "model":
                    metrics["model"]["chars"] += char_count
                elif "user" in source:
                    metrics["user"]["chars"] += char_count
                else:
                    metrics["system"]["chars"] += char_count
                    
            except Exception:
                continue
                
    # Calculate tokens
    for key in ["user", "model", "system"]:
        metrics[key]["tokens"] = estimate_tokens(metrics[key]["chars"])
        
    return metrics

def draw_bar(percentage: float, width: int = 40, char: str = "█", empty_char: str = "░") -> str:
    filled = int(round(width * percentage / 100.0))
    return char * filled + empty_char * (width - filled)

def main():
    home = Path.home()
    app_dir = home / ".gemini/antigravity-cli"
    brain_dir = app_dir / "brain"
    
    # Check if a specific conversation ID was passed
    target_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not brain_dir.exists():
        print(f"Error: Brain directory not found at {brain_dir}")
        sys.exit(1)
        
    sessions = []
    
    # Scan all brain directories
    for child in brain_dir.iterdir():
        if not child.is_dir():
            continue
            
        # Skip system or hidden dirs
        if child.name.startswith("."):
            continue
            
        logs_dir = child / ".system_generated/logs"
        full_transcript = logs_dir / "transcript_full.jsonl"
        normal_transcript = logs_dir / "transcript.jsonl"
        
        transcript_to_use = None
        if full_transcript.exists():
            transcript_to_use = full_transcript
        elif normal_transcript.exists():
            transcript_to_use = normal_transcript
            
        if transcript_to_use:
            metrics = analyze_transcript(transcript_to_use)
            if metrics:
                sessions.append({
                    "id": child.name,
                    "metrics": metrics,
                    "mtime": transcript_to_use.stat().st_mtime
                })
                
    # Sort sessions by modification time (newest first)
    sessions.sort(key=lambda x: x["mtime"], reverse=True)
    
    if not sessions:
        print("No active conversation logs found.")
        sys.exit(0)
        
    print("====================================================================")
    print("      CRISPR-NiE KA METER — VESTED CO-CREATION & TOKENS CHECK")
    print("====================================================================")
    print("Ka (vital energy/compute/words) measures the focus and investment")
    print("contributed to the build. This index tracks the balance of creation.")
    print()
    
    # If a specific ID is selected or we default to the newest one
    active_session = None
    if target_id:
        for s in sessions:
            if s["id"].startswith(target_id):
                active_session = s
                break
        if not active_session:
            print(f"Session matching prefix '{target_id}' not found. Defaulting to newest.")
            active_session = sessions[0]
    else:
        active_session = sessions[0]
        
    # Print summary list of sessions
    print("Recent Sessions:")
    for i, s in enumerate(sessions[:5]):
        marker = "▶" if s["id"] == active_session["id"] else " "
        total_tok = sum(s["metrics"][k]["tokens"] for k in ["user", "model", "system"])
        print(f"  {marker} [{i}] {s['id'][:8]}... | {s['metrics']['total_steps']} steps | {total_tok:,} total tokens")
    print()
    
    # Active session details
    met = active_session["metrics"]
    u_tok = met["user"]["tokens"]
    a_tok = met["model"]["tokens"]
    s_tok = met["system"]["tokens"]
    total_tokens = u_tok + a_tok + s_tok
    
    if total_tokens == 0:
        print("Active session has no token history yet.")
        sys.exit(0)
        
    u_pct = (u_tok / total_tokens) * 100
    a_pct = (a_tok / total_tokens) * 100
    s_pct = (s_tok / total_tokens) * 100
    
    # Vested Sweat Equity (excluding System overhead)
    co_creation_total = u_tok + a_tok
    if co_creation_total > 0:
        u_vest = (u_tok / co_creation_total) * 100
        a_vest = (a_tok / co_creation_total) * 100
    else:
        u_vest = a_vest = 50.0
        
    print(f"Active Session: {active_session['id']}")
    print(f"Total Steps:    {met['total_steps']}")
    print(f"Total Tokens:   {total_tokens:,} (est.)")
    print("--------------------------------------------------------------------")
    print("Ka Share Breakdown:")
    print(f"  User Ka   (Input/Direction):  {u_tok:8,} tokens | {u_pct:5.1f}%")
    print(f"  AI Ka     (Output/Curation):  {a_tok:8,} tokens | {a_pct:5.1f}%")
    print(f"  System Ka (Resource/Context): {s_tok:8,} tokens | {s_pct:5.1f}%")
    print("--------------------------------------------------------------------")
    print("Vested Co-Creation Equity (User vs AI Focus Share):")
    print(f"  Human (Directional Equity): {u_vest:5.1f}% [{draw_bar(u_vest, char='█', empty_char='░')}]")
    print(f"  AI    (Curatorial Equity):  {a_vest:5.1f}% [{draw_bar(a_vest, char='♦', empty_char='░')}]")
    print("====================================================================")
    print("Reserved Lexeme Status: *invest* is a Ka-locked parameter.")
    print("Investment reflects focus, time, and computational vitality of self.")
    print("====================================================================")

if __name__ == "__main__":
    main()
