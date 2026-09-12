"""Unit tests for Podman dashboard error classification."""

from podmanmcp.podman_context import classify_podman_error


def test_classify_missing_executable():
    assert classify_podman_error("Executable 'podman' not found") == "podman_missing"


def test_classify_machine_not_running():
    msg = (
        "Failed to list containers: Cannot connect to Podman. "
        "try `podman machine start`"
    )
    assert classify_podman_error(msg) == "podman_not_started"


def test_classify_socket_refused():
    assert (
        classify_podman_error("unable to connect: dial tcp 127.0.0.1:62633: connectex: actively refused")
        == "podman_not_started"
    )
