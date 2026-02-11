import re
import sys
from pathlib import Path
import os

# Print debugging info
print("📂 Execution directory:", os.getcwd())
print("📁 Script directory:", Path(__file__).resolve().parent)

# Ensure file argument is passed
if len(sys.argv) < 2:
    print("❌ Usage: python fix_empty_fk_names.py <path_to_diff.xml>")
    sys.exit(1)

diff_file = Path(sys.argv[1]).resolve()
if not diff_file.exists():
    print(f"❌ File not found: {diff_file}")
    sys.exit(1)

content = diff_file.read_text()

# Regex pattern to find addForeignKeyConstraint tags missing constraintName
pattern = re.compile(
    r'(<addForeignKeyConstraint\s+)(?=[^>]*>)((?:(?!constraintName=)[^>])*)>',
    re.MULTILINE
)

def add_constraint_name(match):
    tag_start, attrs = match.groups()
    # Try to find baseTableName for meaningful FK name
    base_match = re.search(r'baseTableName="([^"]+)"', attrs)
    base = base_match.group(1) if base_match else "unknown"
    constraint = f'constraintName="fk_{base}_{abs(hash(attrs)) & 0xFFFF}" '
    return f"{tag_start}{constraint}{attrs}>"

fixed_content = pattern.sub(add_constraint_name, content)
diff_file.write_text(fixed_content)

print(f"✅ Fixed empty constraintName entries in {diff_file.name}")
