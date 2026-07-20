"""
JSON utilities for Podman MCP.

Provides robust JSON parsing and serialization with consistent error handling,
validation, and recovery mechanisms.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

# Type variable for JSON-serializable types
T = TypeVar("T", dict, list, str, int, float, bool, None)


class JSONValidationError(ValueError):
    """Raised when JSON validation fails."""

    pass


def validate_json_schema(data: Any, schema: dict) -> bool:
    """
    Validate JSON data against a JSON Schema.

    Args:
        data: JSON data to validate
        schema: JSON Schema to validate against

    Returns:
        bool: True if data is valid according to the schema

    Raises:
        JSONValidationError: If validation fails
    """
    try:
        from jsonschema import ValidationError, validate

        validate(instance=data, schema=schema)
        return True
    except ImportError:
        logger.warning("jsonschema not installed, skipping schema validation")
        return True
    except ValidationError as e:
        raise JSONValidationError(f"JSON validation error: {e}") from e


def safe_json_loads(
    json_str: str, default: Any = None, context: str = "", schema: dict | None = None, strict: bool = False
) -> dict | list | Any:
    """
    Safely parse JSON string with error handling, validation, and recovery.

    Args:
        json_str: JSON string to parse
        default: Default value to return on error
        context: Context for error messages
        schema: Optional JSON Schema for validation
        strict: If True, raises exceptions on validation errors

    Returns:
        Parsed JSON object or default value on error

    Raises:
        JSONValidationError: If validation fails and strict=True
    """
    if not json_str or not isinstance(json_str, str):
        if strict:
            raise JSONValidationError("Input must be a non-empty string")
        return default

    def try_parse(s: str):
        try:
            return json.loads(s)
        except json.JSONDecodeError as e:
            logger.debug(f"JSON decode error: {e}")
            return None

    # Try direct parse first
    result = try_parse(json_str)
    if result is not None:
        if schema:
            try:
                validate_json_schema(result, schema)
            except JSONValidationError as e:
                if strict:
                    raise
                logger.warning(f"Schema validation failed: {e}")
        return result

    # If direct parse fails, try recovery
    logger.warning(f"Failed to parse JSON {f'in {context} ' if context else ''}")

    # Try common recovery patterns
    recovery_attempts = [
        # Try extracting JSON from the string
        lambda s: try_parse(s[s.find("{") :]) or try_parse(s[s.find("[") :]),
        # Try fixing common JSON syntax errors
        lambda s: try_parse(re.sub(r",\s*([}\]])", r"\1", s)),  # Trailing commas
        lambda s: try_parse(re.sub(r"([{\[,])\s*([}\],])", r"\1null\2", s)),  # Missing values
        # Try parsing as JSON Lines
        lambda s: [try_parse(line) for line in s.splitlines() if try_parse(line)] or None,
    ]

    for attempt in recovery_attempts:
        result = attempt(json_str.strip())
        if result is not None:
            if schema:
                try:
                    validate_json_schema(result, schema)
                except JSONValidationError as e:
                    if strict:
                        raise
                    logger.warning(f"Schema validation failed after recovery: {e}")
            return result

    if strict:
        raise JSONValidationError(f"Failed to parse JSON after recovery attempts: {json_str[:100]}...")
    return default


def safe_json_dumps(data: Any, default: Any = None, schema: dict | None = None, strict: bool = False, **kwargs) -> str:
    """
    Safely serialize data to JSON with error handling and validation.

    Args:
        data: Data to serialize
        default: Default value to return on error
        schema: Optional JSON Schema for validation
        strict: If True, raises exceptions on validation errors
        **kwargs: Additional arguments to json.dumps()

    Returns:
        JSON string or default value on error

    Raises:
        JSONValidationError: If validation fails and strict=True
    """
    try:
        if schema:
            try:
                validate_json_schema(data, schema)
            except JSONValidationError as e:
                if strict:
                    raise
                logger.warning(f"Schema validation failed: {e}")

        # Handle common non-serializable types
        def json_serial(obj):
            if isinstance(obj, (datetime,)):
                return obj.isoformat()
            if hasattr(obj, "__dict__"):
                return obj.__dict__
            if hasattr(obj, "to_dict"):
                return obj.to_dict()
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

        return json.dumps(data, default=json_serial, **kwargs)
    except (TypeError, ValueError) as e:
        if strict:
            raise JSONValidationError(f"Failed to serialize to JSON: {e}") from e
        logger.error(f"Failed to serialize to JSON: {e}")
        return default if default is not None else "{}"


def safe_json_parse_file(
    file_path: str | Path,
    default: Any = None,
    encoding: str = "utf-8",
    schema: dict | None = None,
    strict: bool = False,
) -> dict | list | Any:
    """
    Safely parse JSON from a file with validation and error recovery.

    Args:
        file_path: Path to JSON file (str or Path)
        default: Default value to return on error
        encoding: File encoding
        schema: Optional JSON Schema for validation
        strict: If True, raises exceptions on validation errors

    Returns:
        Parsed JSON object or default value on error

    Raises:
        JSONValidationError: If validation fails and strict=True
        FileNotFoundError: If file doesn't exist and strict=True
        PermissionError: If no read permissions and strict=True
    """
    file_path = Path(file_path) if isinstance(file_path, str) else file_path

    try:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with file_path.open("r", encoding=encoding) as f:
            content = f.read()

        result = safe_json_loads(content, default=default, context=str(file_path), schema=schema, strict=strict)

        if result is None and strict:
            raise JSONValidationError(f"Failed to parse JSON from {file_path}")

        return result

    except (FileNotFoundError, PermissionError) as e:
        if strict:
            raise
        logger.error(f"File error reading {file_path}: {e}")
        return default
    except json.JSONDecodeError as e:
        if strict:
            raise JSONValidationError(f"Invalid JSON in {file_path}: {e}") from e
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return default


def safe_json_dump_file(
    data: Any,
    file_path: str | Path,
    default: Any = None,
    encoding: str = "utf-8",
    schema: dict | None = None,
    ensure_ascii: bool = False,
    indent: int = 2,
    sort_keys: bool = True,
    strict: bool = False,
    **kwargs,
) -> bool:
    """
    Safely write data to a JSON file with validation and atomic write.

    Args:
        data: Data to write
        file_path: Path to output file (str or Path)
        default: Default value to return on error
        encoding: File encoding
        schema: Optional JSON Schema for validation
        ensure_ascii: If False, non-ASCII characters are written as-is
        indent: Number of spaces for indentation (None for compact)
        sort_keys: Whether to sort dictionary keys
        **kwargs: Additional arguments to json.dump()

    Returns:
        bool: True if successful, False otherwise

    Raises:
        JSONValidationError: If validation fails and strict=True
        OSError: If file operations fail and strict=True
    """
    file_path = Path(file_path) if isinstance(file_path, str) else file_path

    try:
        # Validate against schema if provided
        if schema:
            try:
                validate_json_schema(data, schema)
            except JSONValidationError as e:
                if strict:
                    raise
                logger.warning(f"Schema validation failed: {e}")

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Use a temporary file for atomic write
        temp_path = file_path.with_suffix(f".{os.urandom(4).hex()}.tmp")

        try:
            with temp_path.open("w", encoding=encoding) as f:
                json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent, sort_keys=sort_keys, **kwargs)

            # On Windows, we need to remove the destination file first
            if file_path.exists():
                file_path.unlink()

            # Atomic rename
            temp_path.rename(file_path)
            return True

        except Exception:
            # Clean up temp file if something went wrong
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

    except Exception as e:
        if strict:
            if isinstance(e, JSONValidationError):
                raise
            raise OSError(f"Failed to write JSON to {file_path}: {e}") from e
        logger.error(f"Failed to write JSON to {file_path}: {e}")
        return default if default is not None else False
