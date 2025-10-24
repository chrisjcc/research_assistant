#!/usr/bin/env python3
"""
Note:
    coverage.py doesn’t natively support per-file thresholds,
    so we’ll implement this check via a custom post-processing
    script (check_coverage.py) that enforces these rules.
"""

import sys
import subprocess
import json
from pathlib import Path

# Define thresholds
THRESHOLDS = {
    "core/schemas.py": 95,
    "nodes/": 85,
    "tools/": 80,
    "graphs/": 75,
    "utils/": 85,
}

def main():
    result = subprocess.run(
        ["coverage", "json", "-q", "-o", "coverage.json"],
        check=True,
        capture_output=True,
        text=True
    )
    data = json.loads(Path("coverage.json").read_text())
    failures = []

    for file, summary in data["files"].items():
        if not file.startswith("src/research_assistant/"):
            continue
        rel_path = file.split("src/research_assistant/")[1]
        cov = summary["summary"]["percent_covered"]
        for pattern, threshold in THRESHOLDS.items():
            if pattern in rel_path and cov < threshold:
                failures.append((rel_path, cov, threshold))
                break

    if failures:
        print("\n❌ Coverage threshold violations:\n")
        for f, cov, thr in failures:
            print(f"  {f:<50} {cov:.1f}% < required {thr}%")
        sys.exit(1)
    else:
        print("✅ All coverage thresholds met.")

if __name__ == "__main__":
    main()
