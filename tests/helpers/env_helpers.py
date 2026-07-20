"""Helper functions for managing environment variables in tests."""

import os
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def set_env_vars(env_vars: dict[str, str]) -> Iterator[None]:
    """Temporarily set environment variables for testing.

    Args:
        env_vars: Dictionary of environment variables to set

    Yields:
        None

    Example:
        with set_env_vars({"MY_VAR": "test"}):
            # Environment variable is set here
            assert os.environ["MY_VAR"] == "test"
        # Environment variable is restored here
    """
    old_env = {}

    # Store old values
    for key, value in env_vars.items():
        old_env[key] = os.environ.get(key)

        # Set new values
        if value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = value

    try:
        yield
    finally:
        # Restore old values
        for key, old_value in old_env.items():
            if old_value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = old_value


def get_test_env() -> dict[str, str]:
    """Get a dictionary of test environment variables."""
    return {
        "PODMAN_HOST": os.environ.get("PODMAN_HOST", "unix:///var/run/podman.sock"),
        "PODMAN_TLS_VERIFY": os.environ.get("PODMAN_TLS_VERIFY", ""),
        "PODMAN_CERT_PATH": os.environ.get("PODMAN_CERT_PATH", ""),
        "TEST_ENV": os.environ.get("TEST_ENV", "local"),
        "LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO"),
    }


def is_ci_environment() -> bool:
    """Check if running in a CI environment."""
    return (
        os.environ.get("CI", "false").lower() == "true" or os.environ.get("GITHUB_ACTIONS", "false").lower() == "true"
    )


def skip_if_ci():
    """Decorator to skip a test if running in CI environment."""
    import pytest

    return pytest.mark.skipif(is_ci_environment(), reason="Test skipped in CI environment")


def only_in_ci():
    """Decorator to run a test only in CI environment."""
    import pytest

    return pytest.mark.skipif(not is_ci_environment(), reason="Test only runs in CI environment")


def skip_if_no_podman():
    """Decorator to skip a test if Podman is not available."""
    import podman
    import pytest

    try:
        podman.from_env().ping()
        return lambda func: func
    except Exception:
        return pytest.mark.skip("Podman is not available")
