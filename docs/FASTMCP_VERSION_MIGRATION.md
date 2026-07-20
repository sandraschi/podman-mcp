# FastMCP 2.x to 3.2.0 Migration Guide

This document outlines the key differences between older FastMCP versions and 3.2.0, focusing on tool development patterns, the singleton MCP pattern, and the removal of `ToolResult`.

## Table of Contents
- [Singleton MCP Pattern](#singleton-mcp-pattern)
- [Tool Definition](#tool-definition)
- [Response Formats](#response-formats)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

## Singleton MCP Pattern

In FastMCP 3.2.0, we use a singleton instance of the FastMCP server to avoid circular dependencies and ensure all parts of the application share the same tool registry.

### FastMCP 3.2.0 (SOTA)
Create a centralized `mcp_instance.py`:
```python
from fastmcp import FastMCP

_mcp = None

def get_mcp():
    global _mcp
    if _mcp is None:
        _mcp = FastMCP("PodmanMCP")
    return _mcp
```

Then in each tool file:
```python
from podmanmcp.mcp_instance import get_mcp

mcp = get_mcp()

@mcp.tool()
async def my_tool(param1: str) -> dict:
    return {"status": "success", "data": param1}
```

## Tool Definition

### FastMCP 3.2.0 (New)
```python
@mcp.tool()
async def my_tool(param1: str) -> dict:
    """
    Detailed docstring following SOTA standards.
    """
    return {
        "status": "success",
        "data": param1,
        "message": "Operation completed successfully"
    }
```

## Response Formats

### FastMCP 3.x (Deprecated)
The `ToolResult` class was used in earlier 3.x previews for complex responses.

### FastMCP 3.2.0 (SOTA)
Simple dictionaries are now the preferred return type for tools. FastMCP 3.2.0 automatically handles conversion to the appropriate MCP response format.

```json
{
  "status": "success",
  "data": {
    "key": "value"
  },
  "message": "Operation completed successfully"
}
```

## Error Handling

### FastMCP 3.2.0 (SOTA)
Instead of raising `ToolError`, return a standard error dictionary to ensure graceful handling and informative feedback for the user.

```python
try:
    # Operation
    return {
        "status": "success",
        "data": result_data
    }
except Exception as e:
    return {
        "status": "error",
        "message": f"Failed to complete operation: {str(e)}"
    }
```

## Best Practices

1. **Always use type hints** for function parameters and return values
2. **Document all tools** with detailed docstrings
3. **Use async/await** for I/O bound operations
4. **Log errors** with context
5. **Validate inputs** using Pydantic models when possible
6. **Follow consistent** response formats
7. **Test tools** thoroughly

## Common Pitfalls

1. **Missing type hints** - Can cause issues with FastMCP's type system
2. **Blocking I/O** in async functions - Use `asyncio.to_thread` for CPU-bound operations
3. **Incomplete error handling** - Always catch and log exceptions
4. **Circular imports** - Be careful with imports between tool modules
5. **Resource leaks** - Ensure resources are properly closed
6. **Inconsistent response formats** - Follow the standard response format
7. **Missing documentation** - Document all tools, parameters, and return values
