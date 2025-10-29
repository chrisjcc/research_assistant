#!/usr/bin/env python3
"""
Custom coverage threshold checker.

Ensures per-module coverage thresholds are met.
Reads configuration from coverage.toml.
"""

import json
import logging
import subprocess
import sys
import tomllib  # Python 3.11+
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")

CONFIG_PATH = Path("coverage.toml")
COVERAGE_JSON = Path("coverage.json")


def load_thresholds():
    """Load per-module coverage thresholds from coverage.toml."""
    with CONFIG_PATH.open("rb") as f:
        cfg = tomllib.load(f)
    return cfg.get("coverage_thresholds", {})


def main():
    # Generate JSON coverage report, using coverage.toml explicitly
    result = subprocess.run(
        [
            "coverage",
            "json",
            "-q",
            "-i",  # ignore parse errors like couldn't-parse
            "--rcfile",
            str(CONFIG_PATH),
            "-o",
            str(COVERAGE_JSON),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.warning("⚠️  Warning: coverage json returned non-zero exit code.")
        if result.stderr:
            logger.error(result.stderr.strip())

    if not COVERAGE_JSON.exists():
        logger.warning("coverage.json was not generated.")
        logger.info("Make sure coverage.toml is valid and that pytest wrote .coverage data.")
        sys.exit(1)

    data = json.loads(COVERAGE_JSON.read_text())
    thresholds = load_thresholds()
    failures = []

    for file, summary in data["files"].items():
        if not file.startswith("src/research_assistant/"):
            continue
        rel_path = file.split("src/research_assistant/")[1]
        cov = summary["summary"]["percent_covered"]
        for pattern, threshold in thresholds.items():
            if pattern in rel_path and cov < threshold:
                failures.append((rel_path, cov, threshold))
                break

    if failures:
        logger.warning("\nCoverage threshold violations:\n")
        for f, cov, thr in failures:
            logger.warning(f"{f:<50} {cov:.1f}% < required {thr}%")
        sys.exit(1)
    else:
        logger.info("All coverage thresholds met.")


if __name__ == "__main__":
    main()
