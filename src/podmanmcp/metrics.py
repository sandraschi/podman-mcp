"""
Metrics and timing utilities for Podman MCP.

This module provides utilities for tracking performance metrics and timing
operations in a structured way, with support for logging and analysis.
"""

import functools
import logging
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, TypeVar, cast

from .logging_config import log_context, logger

# Type variable for generic function wrapping
F = TypeVar("F", bound=Callable[..., Any])


def log_metrics(name: str, value: float, tags: dict[str, Any] | None = None) -> None:
    """Log a metric value with optional tags.

    Args:
        name: Name of the metric
        value: Numeric value of the metric
        tags: Optional key-value pairs of tags for additional context
    """
    if not hasattr(log_context, "metrics"):
        log_context.metrics = {}

    metric = {"value": value}
    if tags:
        metric["tags"] = tags

    # Initialize metrics list if it doesn't exist
    if name not in log_context.metrics:
        log_context.metrics[name] = []

    log_context.metrics[name].append(metric)
    logger.debug(f"Recorded metric: {name}={value}", extra={"metrics": {name: metric}})


def time_it(name: str, log_level: int = logging.DEBUG) -> Callable[[F], F]:
    """Decorator to measure and log the execution time of a function.

    Args:
        name: Name to identify this timing measurement
        log_level: Logging level to use for the timing message

    Returns:
        Decorated function that logs its execution time
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = (time.perf_counter() - start_time) * 1000  # Convert to ms
                log_metrics(f"{name}_duration_ms", duration)
                logger.log(log_level, f"{name} completed in {duration:.2f}ms", extra={"duration_ms": duration})

        return cast(F, wrapper)

    return decorator


@contextmanager
def time_block(name: str, log_level: int = logging.DEBUG) -> Any:
    """Context manager to measure and log the execution time of a code block.

    Args:
        name: Name to identify this timing measurement
        log_level: Logging level to use for the timing message

    Yields:
        None
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration = (time.perf_counter() - start_time) * 1000  # Convert to ms
        log_metrics(f"{name}_duration_ms", duration)
        logger.log(log_level, f"{name} completed in {duration:.2f}ms", extra={"duration_ms": duration})


def count_invocations(name: str) -> Callable[[F], F]:
    """Decorator to count function invocations.

    Args:
        name: Name to identify this counter

    Returns:
        Decorated function that counts its invocations
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log_metrics(f"{name}_invocations", 1)
            return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def track_errors(name: str) -> Callable[[F], F]:
    """Decorator to track and log function errors.

    Args:
        name: Name to identify this error tracker

    Returns:
        Decorated function that tracks errors
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_metrics(f"{name}_errors", 1, {"error_type": e.__class__.__name__})
                raise

        return cast(F, wrapper)

    return decorator


def get_metrics_summary() -> dict[str, dict[str, Any]]:
    """Get a summary of all recorded metrics.

    Returns:
        Dictionary with metric names as keys and their summaries as values
    """
    if not hasattr(log_context, "metrics") or not log_context.metrics:
        return {}

    summary: dict[str, dict[str, Any]] = {}

    for name, values in log_context.metrics.items():
        if not values:
            continue

        # Calculate basic statistics
        numeric_values = [v["value"] if isinstance(v, dict) else v for v in values]
        count = len(numeric_values)
        total = sum(numeric_values)
        avg = total / count if count > 0 else 0

        summary[name] = {
            "count": count,
            "total": total,
            "average": avg,
            "min": min(numeric_values) if numeric_values else None,
            "max": max(numeric_values) if numeric_values else None,
            "samples": numeric_values[-10:],  # Last 10 samples
        }

    return summary


def reset_metrics() -> None:
    """Reset all recorded metrics."""
    if hasattr(log_context, "metrics"):
        log_context.metrics = {}
