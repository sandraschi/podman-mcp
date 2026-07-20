import os
import re
from pathlib import Path


def update_imports(file_path):
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Replace imports and fix duplicates
    content = re.sub(r"from fastmcp\\.tools import (?:Tool, )?get_tools_metadata", "", content)

    # Fix duplicate imports
    content = re.sub(r"from fastmcp\\.tools import (Tool, tool)(?:, tool)*", r"from fastmcp.tools import \1", content)

    # Add tool import if missing
    if "from fastmcp.tools import Tool" in content and "from fastmcp.tools import tool" not in content:
        content = content.replace("from fastmcp.tools import Tool", "from fastmcp.tools import Tool, tool")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    tools_dir = Path("src/podmanmcp/tools")

    # Process all Python files in the tools directory
    for root, _, files in os.walk(tools_dir):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                file_path = os.path.join(root, file)
                print(f"Updating imports in {file_path}")
                update_imports(file_path)


if __name__ == "__main__":
    main()
