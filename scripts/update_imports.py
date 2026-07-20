#!/usr/bin/env python3
"""Update import paths in podmanmcp source files."""
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent / "src" / "podmanmcp"

FILES_TO_UPDATE = {
    "tools/workflow/workflow_tools.py": [
        (r"from \.\.core\.", "from podmanmcp.core."),
        (r"from \.workflow_models", "from podmanmcp.tools.workflow.workflow_models"),
    ],
    "tools/volumes/volume_tools.py": [
        (r"from \.\.core\.", "from podmanmcp.core."),
        (r"from \.volume_models", "from podmanmcp.tools.volumes.volume_models"),
    ],
    "tools/system/system_tools.py": [
        (r"from \.\.core\.", "from podmanmcp.core."),
        (r"from \.\.utils\.", "from podmanmcp.utils."),
        (r"from \.system_models", "from podmanmcp.tools.system.system_models"),
    ],
    "tools/networks/network_tools.py": [
        (r"from \.\.core\.", "from podmanmcp.core."),
        (r"from \.network_models", "from podmanmcp.tools.networks.network_models"),
    ],
    "tools/images/image_tools.py": [
        (r"from \.\.core\.", "from podmanmcp.core."),
        (r"from \.image_models", "from podmanmcp.tools.images.image_models"),
    ],
    "tools/containers/container_tools.py": [
        (r"from \.\.core\.", "from podmanmcp.core."),
        (r"from \.container_models", "from podmanmcp.tools.containers.container_models"),
    ],
    "tools/compose/compose_tools.py": [
        (r"from \.\.core\.", "from podmanmcp.core."),
        (r"from \.compose_models", "from podmanmcp.tools.compose.compose_models"),
        (r"from \.\.\.utils\.", "from podmanmcp.utils."),
    ],
    "tools/examples/stateful_example.py": [
        (r"from \.\.state", "from podmanmcp.state"),
    ],
}


def update_file_imports(file_path, patterns):
    """Update imports in a file based on the given patterns."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        modified = False
        for pattern, replacement in patterns:
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                content = new_content
                modified = True
        if modified:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated: {file_path}")
        else:
            print(f"No changes needed: {file_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")


def main():
    for rel_path, patterns in FILES_TO_UPDATE.items():
        file_path = BASE_DIR / rel_path
        if file_path.exists():
            update_file_imports(file_path, patterns)
        else:
            print(f"File not found: {file_path}")


if __name__ == "__main__":
    main()
