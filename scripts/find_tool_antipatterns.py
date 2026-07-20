"""
Script to find tool decorator anti-patterns in the codebase.

Anti-patterns to find and remove:
1. @mcp.tool(patterns=...) - Old pattern using 'patterns' parameter
2. @Tool - Direct Tool class usage as decorator
3. @tool - Lowercase tool decorator
"""

import json
import re
from pathlib import Path
from typing import Any

# Define anti-patterns to search for
ANTI_PATTERNS = {
    "mcp_tool_patterns": r"@mcp\.tool\s*\([^)]*patterns\s*=",
    "tool_decorator": r"@tool\s*\(",
    "tool_class": r"@Tool\s*\(",
}

# File extensions to search
PYTHON_EXTENSIONS = {".py"}

# Directories to exclude
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "tests",  # Exclude test files
    "examples",  # Example files might have different patterns
    "docs",  # Documentation might have example code
}


def find_antipatterns(root_dir: str) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Find all Python files containing tool decorator anti-patterns."""
    results = {pattern_name: {} for pattern_name in ANTI_PATTERNS}
    root_path = Path(root_dir)

    for file_path in root_path.rglob("*.py"):
        # Skip excluded directories
        if any(part in EXCLUDE_DIRS for part in file_path.parts):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            relative_path = str(file_path.relative_to(root_dir))

            for pattern_name, pattern in ANTI_PATTERNS.items():
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                if matches:
                    results[pattern_name][relative_path] = [
                        {
                            "line": m.group(0).strip(),
                            "line_number": content[: m.start()].count("\n") + 1,
                            "context": "\n".join(
                                content.split("\n")[
                                    max(0, content[: m.start()].count("\n") - 2) : content[: m.start()].count("\n") + 3
                                ]
                            ),
                        }
                        for m in matches
                    ]
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    return results


def save_results(results: dict[str, Any], output_file: str):
    """Save the analysis results to a JSON file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


def main():
    root_dir = r"d:\Dev\repos\podmanmcp"
    output_file = "tool_antipattern_report.json"

    print(f"Scanning for tool decorator anti-patterns in {root_dir}...")
    results = find_antipatterns(root_dir)

    # Count total matches
    total_matches = sum(len(files) for pattern in results.values() for files in pattern.values())
    print(f"Found {total_matches} total anti-pattern matches")

    # Save results
    save_results(results, output_file)
    print(f"Report saved to {output_file}")

    # Print summary
    print("\nSummary of anti-patterns found:")
    for pattern, files in results.items():
        match_count = sum(len(matches) for matches in files.values())
        if match_count > 0:
            print(f"\n{pattern.upper()} (found {match_count} instances):")
            for file_path, matches in files.items():
                print(f"  - {file_path} ({len(matches)} matches)")
                for match in matches[:3]:  # Show first 3 matches per file
                    print(f"    Line {match['line_number']}: {match['line']}")
                if len(matches) > 3:
                    print(f"    ... and {len(matches) - 3} more")


if __name__ == "__main__":
    main()
