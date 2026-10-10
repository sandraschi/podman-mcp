"""Regression test: PODMAN_CMD with Windows backslashes must survive parsing."""

import os

from podmanmcp import podman_context


def test_windows_path_backslashes_preserved(monkeypatch):
    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.setenv(
        "PODMAN_CMD", r"C:\Users\sandr\AppData\Local\Programs\Podman\podman.exe"
    )
    cmd = podman_context.get_podman_command()
    assert cmd == [r"C:\Users\sandr\AppData\Local\Programs\Podman\podman.exe"]


def test_windows_path_with_args(monkeypatch):
    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.setenv("PODMAN_CMD", r'"C:\Program Files\Podman\podman.exe" --log-level debug')
    cmd = podman_context.get_podman_command()
    assert cmd[0] == r"C:\Program Files\Podman\podman.exe"
    assert cmd[1:] == ["--log-level", "debug"]


def test_posix_split_unchanged(monkeypatch):
    monkeypatch.setattr(os, "name", "posix")
    monkeypatch.setenv("PODMAN_CMD", "podman --log-level debug")
    assert podman_context.get_podman_command() == ["podman", "--log-level", "debug"]
