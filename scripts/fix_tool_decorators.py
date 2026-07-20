#!/usr/bin/env python3
"""
Fix FastMCP 2.11.3+ compatibility: Remove 'returns' parameters from @Tool decorators
"""

import os
import re
import sys


def fix_tool_decorator(content: str) -> tuple[str, int]:
    """
    Remove 'returns' parameter from @Tool decorators in the content.

    Returns:
        Tuple of (modified_content, number_of_changes)
    """
    changes = 0

    # Pattern to match @Tool decorator with returns parameter
    # This handles multi-line decorators
    pattern = r"(@Tool\s*\(\s*[^)]*?)(,\s*returns\s*=\s*\{[^}]*?\}[^)]*?)(\s*\))"

    def replace_func(match):
        nonlocal changes
        changes += 1
        before = match.group(1)
        _returns_part = match.group(2)  # This is what we remove
        after = match.group(3)

        # Clean up any trailing comma before the closing parenthesis
        before_clean = re.sub(r",\s*$", "", before)

        print(f"  ✅ Removed returns parameter (change #{changes})")
        return before_clean + after

    # Apply the fix
    fixed_content = re.sub(pattern, replace_func, content, flags=re.DOTALL)

    # Handle edge case where returns is the only parameter after decorator name
    pattern2 = r"(@Tool\s*\(\s*[^,)]*?)(,\s*returns\s*=\s*\{[^}]*?\}\s*)(\))"

    def replace_func2(match):
        nonlocal changes
        changes += 1
        before = match.group(1)
        _returns_part = match.group(2)
        after = match.group(3)

        print(f"  ✅ Removed returns parameter (edge case, change #{changes})")
        return before + after

    fixed_content = re.sub(pattern2, replace_func2, fixed_content, flags=re.DOTALL)

    return fixed_content, changes


def fix_file(file_path: str) -> bool:
    """
    Fix a single Python file by removing returns parameters from @Tool decorators.

    Returns:
        True if file was modified, False otherwise
    """
    try:
        print(f"\n🔧 Processing: {file_path}")

        # Read the file
        with open(file_path, encoding="utf-8") as f:
            original_content = f.read()

        # Apply fixes
        fixed_content, changes = fix_tool_decorator(original_content)

        if changes > 0:
            # Write the fixed content back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            print(f"  ✅ Fixed {changes} @Tool decorators in {file_path}")
            return True
        else:
            print(f"  ℹ️  No @Tool decorators with 'returns' found in {file_path}")
            return False

    except Exception as e:
        print(f"  ❌ Error processing {file_path}: {e!s}")
        return False


def find_python_files(directory: str) -> list[str]:
    """Find all Python files in the directory tree."""
    python_files = []
    for root, _dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def main():
    """Main function to fix all Python files in the podmanmcp tools directory."""
    tools_dir = "src/podmanmcp/tools"

    if not os.path.exists(tools_dir):
        print(f"❌ Tools directory not found: {tools_dir}")
        print("Run this script from the podmanmcp project root directory.")
        sys.exit(1)

    print("🎯 FastMCP 2.11.3+ Tool Decorator Compatibility Fix")
    print("=" * 60)
    print(f"Scanning: {os.path.abspath(tools_dir)}")

    # Find all Python files in the tools directory
    python_files = find_python_files(tools_dir)

    if not python_files:
        print(f"❌ No Python files found in {tools_dir}")
        sys.exit(1)

    print(f"Found {len(python_files)} Python files")

    # Process each file
    modified_files = 0
    total_changes = 0

    for file_path in python_files:
        if fix_file(file_path):
            modified_files += 1

    # Summary
    print("\n" + "=" * 60)
    print("🎉 SUMMARY:")
    print(f"   📁 Files processed: {len(python_files)}")
    print(f"   ✏️  Files modified: {modified_files}")
    print(f"   🔧 Total fixes applied: {total_changes}")

    if modified_files > 0:
        print("\n✅ SUCCESS: Fixed @Tool decorators for FastMCP 2.11.3+ compatibility!")
        print("   You can now test the podmanmcp server.")
    else:
        print("\nℹ️  No changes needed - files are already compatible.")


if __name__ == "__main__":
    main()
