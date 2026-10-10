"""Unit tests for podman event parsing (Inbox backend)."""

from podman_mcp.web import parse_podman_events

SAMPLE = """{"Action": "pull", "Actor": {"Attributes": {"image": "nginx:alpine", "name": "nginx:alpine"}}, "Type": "image", "time": 100}
{"Action": "create", "Actor": {"Attributes": {"image": "nginx:alpine", "name": "web"}}, "Type": "container", "time": 200}
{"Action": "die", "Actor": {"Attributes": {"image": "nginx:alpine", "name": "web"}}, "Type": "container", "time": 150}

not-json
{"Action": "start", "Type": "container", "time": 300}
"""


def test_parse_orders_newest_first():
    events = parse_podman_events(SAMPLE)
    assert [e["time"] for e in events] == [300, 200, 150, 100]


def test_parse_fields():
    events = parse_podman_events(SAMPLE)
    top = events[0]
    assert top["action"] == "start"
    assert top["type"] == "container"
    assert top["name"] == ""
    by_name = [e for e in events if e["name"] == "web"]
    assert len(by_name) == 2
    assert by_name[0]["action"] == "create"


def test_parse_skips_blank_and_garbage():
    assert parse_podman_events("\n   \nnot json\n") == []
    assert parse_podman_events("") == []


def test_parse_limit():
    lines = "\n".join(
        f'{{"Action": "a{i}", "Type": "container", "time": {i}}}' for i in range(10)
    )
    assert len(parse_podman_events(lines, limit=3)) == 3
