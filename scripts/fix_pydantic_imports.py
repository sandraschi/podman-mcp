#!/usr/bin/env python3
"""Fix Pydantic 2.x import compatibility for podman-mcp."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def fix_imports_in_file(filepath: Path) -> bool:
    """Fix ValidationInfo import in a single file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        original_content = content
        content = content.replace(
            "from pydantic.functional_validators import ValidationInfo",
            "from pydantic import ValidationInfo",
        )
        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)
        return False


def main():
    model_files = [
        "src/podmanmcp/tools/containers/container_models.py",
        "src/podmanmcp/tools/images/image_models.py",
        "src/podmanmcp/tools/networks/network_models.py",
        "src/podmanmcp/tools/volumes/volume_models.py",
        "src/podmanmcp/tools/system/system_models.py",
        "src/podmanmcp/tools/compose/compose_models.py",
    ]
    fixed_files = []
    for file_path in model_files:
        full_path = REPO_ROOT / file_path
        if full_path.exists():
            if fix_imports_in_file(full_path):
                fixed_files.append(file_path)
                print(f"Fixed: {file_path}")
            else:
                print(f"No changes needed: {file_path}")
        else:
            print(f"File not found: {file_path}")
    if fixed_files:
        print(f"Successfully fixed {len(fixed_files)} files.")
    else:
        print("No files were fixed.")
    return 0 if fixed_files else 1


if __name__ == "__main__":
    sys.exit(main())
