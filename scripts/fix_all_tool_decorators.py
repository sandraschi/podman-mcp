#!/usr/bin/env python3
"""
Comprehensive fix for FastMCP Tool decorator compatibility - Update to FastMCP 2.12+ standards

This script updates tool decorators to be compatible with FastMCP 2.12+ by:
1. Removing 'returns' parameter from @Tool decorators
2. Ensuring proper import of Tool from fastmcp.tools.tool
"""

import re
from pathlib import Path


def update_tool_decorators(content: str) -> str:
    """
    Update tool decorators to FastMCP 2.12+ standards.

    This function:
    1. Updates @tool to @Tool
    2. Removes 'returns' parameter
    3. Ensures proper parameter structure
    """
    # Update @tool to @Tool
    content = re.sub(r"@tool\s*\(", "@Tool(", content)

    # Remove 'returns' parameter from @Tool decorators
    pattern = r"(@Tool\s*\(\s*)((?:[^()]*|\([^)]*\))*)\s*\)"

    def fix_decorator(match):
        prefix = match.group(1)  # "@Tool("
        params_content = match.group(2)  # Everything between the parentheses

        # Remove returns parameter if it exists
        if "returns=" in params_content:
            # This pattern matches the returns parameter and its value (including nested objects)
            returns_pattern = r',?\s*returns\s*=\s*(?:"[^"]*"|\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\S+)(?:\s*,?)'
            params_content = re.sub(returns_pattern, "", params_content, flags=re.DOTALL)

            # Clean up any resulting formatting issues
            params_content = re.sub(r",\s*,", ",", params_content)  # Double commas
            params_content = re.sub(r"^\s*,", "", params_content)  # Leading comma
            params_content = re.sub(r",\s*$", "", params_content)  # Trailing comma

        return f"{prefix}{params_content})"

    # Apply the fix
    content = re.sub(pattern, fix_decorator, content, flags=re.DOTALL)
    return content


def fix_file(file_path: Path) -> tuple[bool, str]:
    """
    Fix a single file to update tool decorators to FastMCP 2.12+ standards.

    Args:
        file_path: Path to the file to fix

    Returns:
        Tuple of (success: bool, message: str)
    """
    print(f"Processing: {file_path}")

    try:
        content = file_path.read_text(encoding="utf-8")

        # Skip if no tool decorators found
        if "@tool(" not in content and "@Tool(" not in content:
            return False, "No tool decorators found"

        # Update the content
        updated_content = update_tool_decorators(content)

        # Ensure we have the correct import
        if "from fastmcp.tools.tool import Tool" not in updated_content:
            # Add import after existing imports or at the top of the file
            import_match = list(re.finditer(r"^(import |from \w+ import )", updated_content, re.MULTILINE))
            if import_match:
                last_import = import_match[-1]
                insert_pos = last_import.end()
                updated_content = (
                    updated_content[:insert_pos]
                    + "\nfrom fastmcp.tools.tool import Tool"
                    + updated_content[insert_pos:]
                )
            else:
                # Add after docstring if present
                docstring_match = re.search(r'^\s*"{3}.*?"{3}\s*', updated_content, re.DOTALL)
                if docstring_match:
                    insert_pos = docstring_match.end()
                    updated_content = (
                        updated_content[:insert_pos]
                        + "\n\nfrom fastmcp.tools.tool import Tool"
                        + updated_content[insert_pos:]
                    )
                else:
                    updated_content = "from fastmcp.tools.tool import Tool\n\n" + updated_content

        # Write changes if modified
        if updated_content != content:
            file_path.write_text(updated_content, encoding="utf-8")
            return True, "Updated tool decorators to FastMCP 2.12+ standards"

        return False, "No changes needed"

    except Exception as e:
        return False, f"Error processing file: {e!s}"


def main():
    """
    Main function to update tool decorators in all Python files.

    Scans the project directory for Python files and updates any tool decorators
    to be compatible with FastMCP 2.12+ standards.
    """
    # Get all Python files in the project
    project_root = Path(__file__).parent.parent
    python_files = list(project_root.glob("**/*.py"))

    # Filter out virtual environment and other excluded directories
    excluded_dirs = {
        "venv",
        "env",
        ".venv",
        ".git",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        "build",
        "dist",
        ".mypy_cache",
        ".idea",
        ".vscode",
    }

    python_files = [f for f in python_files if not any(part in excluded_dirs for part in f.parts)]

    print(f"Found {len(python_files)} Python files to process")

    # Process each file
    updated_count = 0
    error_count = 0

    for file_path in python_files:
        success, message = fix_file(file_path)
        if success:
            updated_count += 1
            print(f"✅ Updated: {file_path.relative_to(project_root)}")
        elif message.startswith("Error"):
            error_count += 1
            print(f"❌ {message}")

    print("\nProcessing complete:")
    print(f"- Updated {updated_count} files")
    print(f"- {error_count} errors encountered")
    print(f"- {len(python_files) - updated_count - error_count} files unchanged")

    if updated_count > 0:
        print("\n🚀 Next steps:")
        print("   1. Test podman-mcp startup: python -m podmanmcp.server")
        print("   2. Check for any remaining compatibility issues")
        print("   3. Run integration tests if available")


if __name__ == "__main__":
    main()
