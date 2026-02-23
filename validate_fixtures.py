#!/usr/bin/env python3
"""Validate test fixture JSON files."""

import json
import sys

def validate_fixture(filepath):
    """Validate a JSON fixture file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"✓ {filepath}: Valid JSON")

        # Check for required top-level keys
        required_keys = ['metadata', 'sections', 'tables', 'claims', 'experiments']
        for key in required_keys:
            if key not in data:
                print(f"  ⚠ Missing key: {key}")

        return True
    except json.JSONDecodeError as e:
        print(f"✗ {filepath}: Invalid JSON - {e}")
        return False
    except Exception as e:
        print(f"✗ {filepath}: Error - {e}")
        return False

if __name__ == "__main__":
    files = [
        'tests/fixtures/alphaotp_paper.json',
        'tests/fixtures/or_r1_paper.json'
    ]

    all_valid = True
    for filepath in files:
        if not validate_fixture(filepath):
            all_valid = False

    if all_valid:
        print("\nAll fixtures are valid!")
        sys.exit(0)
    else:
        print("\nSome fixtures are invalid!")
        sys.exit(1)
