import os
import re
from pathlib import Path


def fix_imports_in_file(file_path):
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Replace imports
    content = re.sub(r"from fastmcp\\.tools\\.tool import Tool, tool", "from fastmcp.tools import Tool", content)

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
                fix_imports_in_file(file_path)


if __name__ == "__main__":
    main()
