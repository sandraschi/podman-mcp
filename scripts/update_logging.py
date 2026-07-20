"""
Script to update logging configuration across all Python files in the repository.

This script will:
1. Replace any basic logging configuration with the new structured logging
2. Update import statements to use the centralized logging config
3. Remove any direct print statements
"""

import os
import re
import sys
from pathlib import Path

# Directories to process
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"

# Patterns to search for
BASIC_LOGGING_PATTERN = re.compile(r"logging\.basicConfig\([^)]*\)", re.DOTALL)

PRINT_STATEMENT = re.compile(r"^\s*print\([^)]*\)", re.MULTILINE)

# New logging imports
LOGGING_IMPORTS = """from podmanmcp.logging_config import logger, configure_logging

# Configure logging
configure_logging()
"""


def update_file_content(content: str) -> str:
    """Update the content of a Python file with proper logging configuration."""
    # Remove basic logging config
    content = re.sub(BASIC_LOGGING_PATTERN, "", content)

    # Replace print statements with logger calls
    def replace_print(match):
        print_stmt = match.group(0).strip()
        # Extract the part inside print()
        content = print_stmt[6:-1]  # Remove 'print(' and ')'
        return f"logger.info({content})"

    content = re.sub(PRINT_STATEMENT, replace_print, content)

    # Add logging imports if not present
    if "import logging" in content and "from podmanmcp.logging_config" not in content:
        # Replace 'import logging' with our custom imports
        content = content.replace("import logging", LOGGING_IMPORTS)
    elif "import logging" not in content and "from podmanmcp.logging_config" not in content:
        # Add our imports at the top of the file if no logging imports exist
        lines = content.split("\n")
        import_line = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                import_line = i + 1
            elif line.strip() == "":
                continue
            else:
                break

        lines.insert(import_line, LOGGING_IMPORTS)
        content = "\n".join(lines)

    return content


def process_file(filepath: Path) -> None:
    """Process a single Python file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        # Skip files that don't need updating
        if "print(" not in content and "logging.basicConfig" not in content:
            return

        updated_content = update_file_content(content)

        if updated_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(updated_content)
            logger.info(f"Updated: {filepath}")
    except Exception as e:
        logger.error(f"Error processing {filepath}: {e}", file=sys.stderr)


def main():
    """Main function to update logging in all Python files."""
    # Process all Python files in the repository
    for root, _, files in os.walk(BASE_DIR):
        # Skip virtual environment directories
        if any(part.startswith(".") or part == "venv" for part in root.split(os.sep)):
            continue

        for filename in files:
            if filename.endswith(".py"):
                filepath = Path(root) / filename
                process_file(filepath)


logger.info("Logging update complete!")

if __name__ == "__main__":
    main()
