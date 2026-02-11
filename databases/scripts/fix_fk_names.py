#!/usr/bin/env python3
"""
Post-process a Liquibase generated changelog and inject deterministic
constraintName attributes for any addForeignKeyConstraint elements that
are missing them. Usage:

  python3 fix_fk_names.py path/to/generated_changelog.xml

The generated name pattern: fk_<baseTable>_<baseCols>_to_<refTable>
If that name already exists in the changelog, a numeric suffix is appended.

This is intended to help with SQLite diffs where constraint names are not
exposed by the JDBC driver and Liquibase emits empty names.
"""
import sys
from xml.etree import ElementTree as ET
from collections import defaultdict


def safe_name(s: str) -> str:
    # keep lowercase, alphanumeric and underscores
    return ''.join(c if c.isalnum() else '_' for c in s).lower()


def main():
    if len(sys.argv) < 2:
        print("Usage: fix_fk_names.py <changelog.xml>")
        sys.exit(2)

    path = sys.argv[1]
    try:
        tree = ET.parse(path)
    except Exception as e:
        print(f"Failed to parse {path}: {e}")
        sys.exit(1)

    root = tree.getroot()

    # Collect existing constraintName values to avoid collisions.
    existing = set()
    # Use a namespace-agnostic search: element.tag may include namespace in '{ns}local'
    for elem in root.iter():
        tag = elem.tag
        if isinstance(tag, str) and tag.rsplit('}', 1)[-1] == 'addForeignKeyConstraint':
            name = elem.get('constraintName')
            if name:
                existing.add(name)

    counts = defaultdict(int)

    modified = False
    for elem in root.iter():
        tag = elem.tag
        if not (isinstance(tag, str) and tag.rsplit('}', 1)[-1] == 'addForeignKeyConstraint'):
            continue
        fk = elem
        if fk.get('constraintName'):
            continue
        base = fk.get('baseTableName') or 'tbl'
        cols = (fk.get('baseColumnNames') or 'col').replace(',', '_').replace(' ', '')
        ref = fk.get('referencedTableName') or 'ref'
        base_n = safe_name(base)
        cols_n = safe_name(cols)
        ref_n = safe_name(ref)
        candidate = f"fk_{base_n}_{cols_n}_to_{ref_n}"
        # ensure uniqueness
        if candidate in existing:
            counts[candidate] += 1
            candidate = f"{candidate}_{counts[candidate]}"
        existing.add(candidate)
        fk.set('constraintName', candidate)
        modified = True
        print(f"Injected constraintName='{candidate}' for FK {base}({cols}) -> {ref}")

    if modified:
        try:
            tree.write(path, encoding='utf-8', xml_declaration=True)
            print(f"Updated changelog written to {path}")
        except Exception as e:
            print(f"Failed to write updated changelog: {e}")
            sys.exit(1)
    else:
        print("No missing foreign key constraintName attributes found.")


if __name__ == '__main__':
    main()
