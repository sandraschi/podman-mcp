"""
Script to analyze and document tool decorator patterns in the codebase.
"""

import json
import re
from pathlib import Path
from typing import Any

# Define the patterns to search for
PATTERNS = {
    "mcp_tool": r"@mcp\.tool\s*\([^)]*patterns\s*=",
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
    "tests",
}


def find_files_with_patterns(root_dir: str) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Find all Python files containing tool decorator patterns."""
    results = {pattern: {} for pattern in PATTERNS}
    root_path = Path(root_dir)

    for file_path in root_path.rglob("*.py"):
        # Skip excluded directories
        if any(part in EXCLUDE_DIRS for part in file_path.parts):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            relative_path = str(file_path.relative_to(root_dir))

            for pattern_name, pattern in PATTERNS.items():
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
    output_file = "tool_decorator_analysis.json"

    print(f"Analyzing tool decorators in {root_dir}...")
    results = find_files_with_patterns(root_dir)

    # Count total matches
    total_matches = sum(len(files) for pattern in results.values() for files in pattern.values())
    print(
        f"Found {total_matches} total matches across {sum(len(files) for pattern in results.values() for files in pattern.values())} files"
    )

    # Save results
    save_results(results, output_file)
    print(f"Results saved to {output_file}")

    # Print summary
    print("\nSummary of findings:")
    for pattern, files in results.items():
        print(f"\nPattern: {pattern}")
        print(f"  Found in {len(files)} files")
        for file_path, matches in files.items():
            print(f"  - {file_path} ({len(matches)} matches)")


if __name__ == "__main__":
    main()
