"""
Script to fix logging imports in all Python files in the tools directory.

This script ensures that all Python files in the tools directory have the correct
logging imports and configuration.
"""

import os


def fix_logging_imports(file_path: str) -> bool:
    """Fix logging imports in a Python file.

    Args:
        file_path: Path to the Python file to fix.

    Returns:
        bool: True if the file was modified, False otherwise.
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Skip files that already have the correct logging import
    if "from podmanmcp.logging_config import logger, configure_logging" in content:
        return False

    # Skip __init__.py files as they might have special handling
    if os.path.basename(file_path) == "__init__.py":
        return False

    # Skip models files
    if file_path.endswith("_models.py"):
        return False

    # Add the logging import after the docstring
    new_content = content

    # Find the end of the docstring
    docstring_end = 0
    if content.startswith('"""'):
        # Handle multi-line docstring
        docstring_end = content.find('"""', 3) + 3
    elif content.startswith("'''"):
        # Handle multi-line docstring with single quotes
        docstring_end = content.find("'''", 3) + 3

    # Add the logging import after the docstring
    if docstring_end > 0:
        # Get the indentation of the first non-empty line after the docstring
        lines = content[docstring_end:].splitlines()
        first_line = next((line for line in lines if line.strip()), "")
        indent = " " * (len(first_line) - len(first_line.lstrip())) if first_line else "    "

        # Add the logging import
        logging_import = (
            f"\n{indent}from podmanmcp.logging_config import logger, configure_logging\n{indent}configure_logging()\n"
        )
        new_content = content[:docstring_end] + logging_import + content[docstring_end:]

    # Only write if content changed
    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    return False


def main():
    """Main function to fix logging imports in all Python files."""
    tools_dir = os.path.join("src", "podmanmcp", "tools")
    modified_files = []

    for root, _, files in os.walk(tools_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if fix_logging_imports(file_path):
                    modified_files.append(file_path)

    if modified_files:
        print("Fixed logging imports in the following files:")
        for file_path in modified_files:
            print(f"- {file_path}")
    else:
        print("No files needed logging import fixes.")


if __name__ == "__main__":
    main()
