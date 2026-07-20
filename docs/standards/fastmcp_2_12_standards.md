# FastMCP 2.12+ Standards and Best Practices

## Table of Contents
1. [Tool Decorator Standards](#tool-decorator-standards)
2. [Import Conventions](#import-conventions)
3. [Tool Registration](#tool-registration)
4. [Type Hints and Annotations](#type-hints-and-annotations)
5. [Error Handling](#error-handling)
6. [Logging](#logging)
7. [Code Organization](#code-organization)
8. [Version Compatibility](#version-compatibility)

## Tool Decorator Standards

### The `@tool` Decorator
In FastMCP 2.12+, the standard decorator for tool functions is `@tool` (lowercase).

**Correct:**
```python
from fastmcp.tools import tool

@tool(
    name="example_tool",
    description="An example tool that demonstrates the correct decorator usage"
)
async def example_tool(param1: str, param2: int) -> dict:
    """Docstring explaining the tool's purpose and parameters."""
    # Implementation
    return {"result": "success"}
```

**Incorrect:**
```python
# Deprecated in FastMCP 2.12+
from fastmcp.tools import Tool  # Wrong import

@Tool(  # Wrong decorator case
    name="example_tool",
    description="This is the old way"
)
```

## Import Conventions

### Tool-Related Imports
```python
# Core tool functionality
from fastmcp.tools import tool, get_tools_metadata

# Exception handling
from fastmcp.exceptions import ToolError

# Type hints
from typing import Any, Dict, List, Optional

# Pydantic models for request/response
from pydantic import BaseModel, Field, field_validator
```

## Tool Registration

### Module-Level Registration
Each module should expose a `get_tools()` function that returns a list of all tools in that module:

```python
def get_tools() -> list:
    """Return all tools in this module for registration."""
    from . import tool1, tool2, tool3
    return [
        tool1.example_tool,
        tool2.another_tool,
        tool3.yet_another_tool
    ]
```

## Type Hints and Annotations

### Required Type Hints
All tool functions must include complete type hints for parameters and return values.

```python
@tool(
    name="calculate_total",
    description="Calculate the total of a list of numbers"
)
async def calculate_total(
    numbers: List[float],
    discount: float = 0.0,
    currency: str = "USD"
) -> Dict[str, Any]:
    """Calculate the total of numbers with an optional discount.
    
    Args:
        numbers: List of numbers to sum
        discount: Discount percentage (0.0 to 1.0)
        currency: Currency code (default: USD)
        
    Returns:
        Dictionary containing the total and currency
    """
    total = sum(numbers) * (1 - discount)
    return {
        "total": total,
        "currency": currency,
        "discount_applied": discount > 0
    }
```

## Error Handling

### Standard Error Response
All tools should follow a consistent error response format:

```python
@tool(name="example_tool")
async def example_tool():
    try:
        # Operation that might fail
        result = perform_operation()
        return {
            "status": "success",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in example_tool: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "error_type": e.__class__.__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
```

## Logging

### Standard Logging Setup
```python
import logging
from pathlib import Path

def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)
```

## Code Organization

### Directory Structure
```
project/
├── src/
│   ├── __init__.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── category1/
│   │   │   ├── __init__.py
│   │   │   └── tools.py
│   │   └── category2/
│   │       ├── __init__.py
│   │       └── tools.py
│   └── models/
│       └── __init__.py
└── tests/
    └── test_tools.py
```

## Version Compatibility

### FastMCP Version Check
Always include a version check in your main application:

```python
import fastmcp
from packaging import version

MIN_FASTMCP_VERSION = "2.12.0"

if version.parse(fastmcp.__version__) < version.parse(MIN_FASTMCP_VERSION):
    raise RuntimeError(
        f"FastMCP version {MIN_FASTMCP_VERSION} or higher is required. "
        f"Current version: {fastmcp.__version__}"
    )
```

## Best Practices

1. **Immutability**: Prefer immutable data structures for tool responses
2. **Documentation**: Always include docstrings with examples
3. **Testing**: Write unit tests for all tools
4. **Error Handling**: Be specific about error conditions
5. **Logging**: Log meaningful context with errors
6. **Performance**: Be mindful of resource usage in tools
7. **Security**: Validate all inputs and sanitize outputs
8. **Dependencies**: Keep tool dependencies minimal

## Migration Guide

### Upgrading from FastMCP < 2.12
1. Replace all `@Tool` with `@tool`
2. Update imports from `fastmcp.tools`
3. Ensure all tools have proper type hints
4. Update error handling to use the standard format
5. Test all tools after migration

## Example Tool Template

```python
"""
Example tool module demonstrating FastMCP 2.12+ standards.
"""
from typing import Any, Dict, List, Optional
import logging

from fastmcp.tools import tool
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

class ExampleRequest(BaseModel):
    """Request model for the example tool."""
    name: str = Field(..., description="The name to greet")
    count: int = Field(1, ge=1, le=10, description="Number of times to greet")
    
    @field_validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

@tool(
    name="example_greeter",
    description="A simple greeter tool that demonstrates FastMCP 2.12+ standards"
)
async def greeter(request: ExampleRequest) -> Dict[str, Any]:
    """Generate a greeting message.
    
    Args:
        request: The greeting request parameters
        
    Returns:
        Dictionary containing the greeting message and metadata
        
    Raises:
        ToolError: If there's an error generating the greeting
    """
    try:
        greeting = f"Hello, {request.name}!" * request.count
        return {
            "status": "success",
            "greeting": greeting,
            "length": len(greeting),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in greeter: {str(e)}", exc_info=True)
        raise ToolError(f"Failed to generate greeting: {str(e)}")

def get_tools() -> list:
    """Return all tools in this module for registration."""
    return [greeter]
```

## Additional Resources

- [FastMCP Documentation](https://fastmcp.readthedocs.io/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Python Typing Documentation](https://docs.python.org/3/library/typing.html)
