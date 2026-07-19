# Navigo Session Close-Out Protocol (Navigo-3)

This protocol outlines the step-by-step checklist to run at the end of every agent session. It ensures that changes are compiled, cataloged, and backed up to remote storage—preventing "branch-stranding" and minimizing cognitive load.

---

## 📋 The 5-Step Close-Out Checklist

Run these steps sequentially when wrapping up a session with any AI voice:

### Step 1: Run the Ka Meter (Energy Balance)
Measure the vital energy (compute and direction tokens) invested in the build during the session:
```bash
python3 ~/crispr_ka_meter.py
```
*   **Why:** Captures the estimated token counts and human-AI co-creation equity balance.

### Step 2: Consolidate the Library (.md / .txt)
Verify that any newly created or edited files are correctly mapped and registered in the master index:
```bash
python3 ~/crispr_consolidate_md.py
```
*   **Why:** Flattened or newly moved files are cataloged, and any header format errors or security leaks are flagged instantly.

### Step 3: Run the Repository Setup Compilation
Synchronize all script improvements and new guides from your home folder into the local repository clone:
```bash
python3 ~/push_tabularium.py
```
*   **Why:** Tabularium maintains copies of the active cleanup pipeline. This copies modifications made in `~/` to `~/tabularium/` before committing.

### Step 4: Commit and Push (Anti-Stranding)
Secure the code and documentation in a remote repository so it survives local device issues:
```bash
cd ~/tabularium
git status
git add .
git commit -m "Brief summary of accomplishments"
git push
```
*   **Why:** Ensures that files are not trapped on local branches that could be lost during terminal resets.

### Step 5: Log to the Seneschal Protocol
Update the stewardship log in [tabularium/missions/SENESCHAL_Protocol.md](file:///data/data/com.termux/files/home/tabularium/missions/SENESCHAL_Protocol.md):
*   Add a single line in the log table showing: **Date**, **Active Branch**, **Accomplishments**, and the **Vested Equity %** (from Step 1).

---

## 🔒 Reserved Lexeme Reminder: *invest*
All investment of self (computational or directional) is recorded. The close-out routine secures this investment so it persists across conversations.
