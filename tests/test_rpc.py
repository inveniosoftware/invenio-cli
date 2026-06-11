# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""RPC client tests."""

import json
import socketserver
import sys
import tempfile
import threading
from pathlib import Path

import pytest

from invenio_cli.helpers.package_managers import UV
from invenio_cli.helpers.rpc import RPCCall, RPCClient


class FakeInvenioHandler(socketserver.StreamRequestHandler):
    """Respond to the RPC protocol like the invenio RPC server."""

    def handle(self):
        """Answer one JSON-line request with one JSON-line response."""
        request = json.loads(self.rfile.readline())
        if request.get("ping"):
            response = {"pong": True}
        else:
            response = {
                "exit_code": 7,
                "stdout": " ".join(request["argv"]),
                "stderr": "warning\n",
            }
        self.wfile.write(json.dumps(response).encode("utf-8") + b"\n")


@pytest.fixture()
def short_tmp_path():
    """A directory short enough for AF_UNIX paths (~104 bytes on macOS)."""
    with tempfile.TemporaryDirectory(prefix="rpc", dir="/tmp") as tmp:
        yield Path(tmp)


@pytest.fixture()
def rpc_socket(short_tmp_path):
    """A running protocol server on a temporary socket."""
    socket_path = short_tmp_path / "rpc.sock"
    server = socketserver.UnixStreamServer(str(socket_path), FakeInvenioHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield socket_path
    server.shutdown()
    server.server_close()


def test_ping(rpc_socket):
    """Ping detects a running server."""
    assert RPCClient(rpc_socket, start_command=None).ping() is True


def test_ping_without_server(short_tmp_path):
    """Ping without a server is False, not an error."""
    client = RPCClient(short_tmp_path / "nope.sock", start_command=None)
    assert client.ping() is False


def test_call_maps_the_response_to_a_process_response(rpc_socket):
    """Exit code, stdout and stderr come back as a ProcessResponse."""
    client = RPCClient(rpc_socket, start_command=None)
    response = client.call(["webpack", "build"])
    assert response.output == "webpack build"
    assert response.error == "warning\n"
    assert response.status_code == 7


# A stand-in for "invenio rpc-server start": serves the protocol on the
# socket given as first argument until it is terminated.
SERVER_SCRIPT = """
import json, socketserver, sys

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        request = json.loads(self.rfile.readline())
        if request.get("ping"):
            response = {"pong": True}
        else:
            response = {"exit_code": 0, "stdout": "ok", "stderr": ""}
        self.wfile.write(json.dumps(response).encode("utf-8") + b"\\n")

with socketserver.UnixStreamServer(sys.argv[1], Handler) as server:
    server.serve_forever()
"""


def test_call_spawns_and_terminates_a_server(short_tmp_path):
    """Without a listening server, one is spawned, used and shut down."""
    socket_path = short_tmp_path / "rpc.sock"
    client = RPCClient(
        socket_path, [sys.executable, "-c", SERVER_SCRIPT, str(socket_path)]
    )
    response = client.call(["collect"])
    assert response.status_code == 0
    assert response.output == "ok"
    client.shutdown()
    assert client.server.poll() is not None


def test_call_reports_a_server_that_dies_during_startup(short_tmp_path):
    """A start command that exits early fails the call instead of hanging."""
    client = RPCClient(
        short_tmp_path / "rpc.sock", [sys.executable, "-c", "raise SystemExit(3)"]
    )
    response = client.call(["collect"])
    assert response.status_code == 1
    assert "exited with code 3" in response.error


def test_send_command_builds_an_rpc_call(short_tmp_path):
    """With a socket path, send_command defers to the RPC server."""
    manager = UV(rpc_socket_path=short_tmp_path / "rpc.sock")
    op = manager.send_command("invenio", "webpack", "build")
    assert isinstance(op, RPCCall)
    assert op.argv == ["webpack", "build"]
    assert op.label == "build"


def test_send_command_without_rpc_is_the_plain_command():
    """Without a socket path, send_command falls back to run_command."""
    assert UV().send_command("invenio", "collect") == [
        "uv",
        "run",
        "--no-sync",
        "invenio",
        "collect",
    ]
