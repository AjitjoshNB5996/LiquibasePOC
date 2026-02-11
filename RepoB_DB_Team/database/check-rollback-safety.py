import os
import sys
import re

# --- Cleanup temporary history file ---
def safe_cleanup(file_path):
    """Safely delete temporary history files (only those starting with 'temp_')."""
    import os
    try:
        if os.path.basename(file_path).startswith("temp_") and os.path.exists(file_path):
            os.remove(file_path)
            # print(f"🧹 Removed temp file: {file_path}")
    except Exception as e:
        # print(f"⚠️ Could not delete temp file: {e}")
        pass

def main():
    if len(sys.argv) < 3:
        print("Usage: python check-rollback-safety.py <history_file> <rollback_count>")
        sys.exit(1)

    history_file = sys.argv[1]
    rollback_count = int(sys.argv[2])

    # --- Detect repo name properly ---
    current_path = os.getcwd()
    repo_name = os.path.basename(os.path.abspath(os.path.join(current_path, "../../..")))
    print(f"🔍 Detected repo: {repo_name}")

    # --- Read Liquibase history ---
    with open(history_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # Extract table lines (ignore headers)
    change_sets = []
    for line in lines:
        if re.match(r"^\|.*\|$", line) and "Changelog Path" not in line:
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 5:
                change_sets.append({
                    "changelog": parts[2],
                    "author": parts[3],
                    "id": parts[4],
                })

    if not change_sets:
        print("⚠️ No changeSets found in history.")
        sys.exit(0)

    # Get last N changeSets
    rollback_count = min(rollback_count, len(change_sets))
    last_changes = change_sets[-rollback_count:]

    print(f"🧾 Checking last {rollback_count} changeSets...\n")

    # Check authors
    invalid = [c for c in last_changes if c["author"].lower() != repo_name.lower()]

    if invalid:
        print("🚫 Rollback blocked!")
        print(f"Out of last {rollback_count} changeSets, {len(invalid)} belong to another repo:\n")
        for c in invalid:
            print(f"   → Author: {c['author']}, ID: {c['id']}, File: {c['changelog']}")
        print("\n⚠️ Please rollback using the corresponding repo to maintain data integrity.")
        sys.exit(1)
    else:
        print(f"✅ Rollback safe — all recent changeSets belong to '{repo_name}'.")
        sys.exit(0)
    
    print(f"\n📊 Total changesets in DB: {len(change_sets)} | Checked last: {rollback_count}")

if __name__ == "__main__":
    try:
        main()
    finally:
        # Always try to clean up the temp file after running
        import sys
        if len(sys.argv) > 1:
            safe_cleanup(sys.argv[1])
