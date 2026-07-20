#!/usr/bin/env python3
"""
Fix FastMCP imports for podman-mcp compatibility
Updates outdated FastMCP imports to work with current FastMCP version
"""

import re
from pathlib import Path


def fix_file_imports(file_path):
    """Fix FastMCP imports in a single file"""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Fix get_tools_metadata import - remove it since it doesn't exist
        content = re.sub(
            r"from fastmcp\.tools import (.*?)get_tools_metadata(.*?)\n",
            lambda m: f"from fastmcp.tools import {m.group(1).rstrip(', ')}{m.group(2).lstrip(', ')}\n".replace(
                ", \n", "\n"
            ),
            content,
        )

        # Fix ToolException import - change to ToolError
        content = re.sub(
            r"from fastmcp\.exceptions import ToolException", "from fastmcp.exceptions import ToolError", content
        )

        # Fix ToolException usage - change to ToolError
        content = re.sub(r"ToolException", "ToolError", content)

        # Remove get_tools_metadata() function calls
        content = re.sub(r"get_tools_metadata\(\)", "{}", content)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix all files"""
    src_dir = Path("src")
    if not src_dir.exists():
        print("Error: src directory not found")
        return

    fixed_files = 0
    total_files = 0

    # Find all Python files
    for py_file in src_dir.rglob("*.py"):
        total_files += 1
        if fix_file_imports(py_file):
            fixed_files += 1

    print(f"\nSummary: Fixed {fixed_files} out of {total_files} Python files")


if __name__ == "__main__":
    main()
