import inspect
import sys

try:
    import fastmcp

    print("FastMCP is installed.")

    # Print version if available
    if hasattr(fastmcp, "__version__"):
        print(f"FastMCP version: {fastmcp.__version__}")
    else:
        print("FastMCP version not found in module attributes.")

    # Print module location
    print(f"Module location: {inspect.getfile(fastmcp)}")

    # List all attributes in fastmcp
    print("\nFastMCP attributes:")
    for name, obj in inspect.getmembers(fastmcp):
        print(f"- {name}: {type(obj).__name__}")

    # Check if tools submodule exists
    if hasattr(fastmcp, "tools"):
        print("\nFastMCP.tools attributes:")
        for name, obj in inspect.getmembers(fastmcp.tools):
            print(f"- {name}: {type(obj).__name__}")
    else:
        print("\nFastMCP.tools submodule not found.")

    # Print sys.path to see where Python is looking for modules
    print("\nPython module search paths:")
    for path in sys.path:
        print(f"- {path}")

except ImportError as e:
    print(f"Error importing FastMCP: {e}")
    print("Make sure FastMCP is installed in your Python environment.")
    print("You can install it with: pip install fastmcp")
