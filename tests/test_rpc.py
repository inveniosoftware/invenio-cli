# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""RPC client tests."""

import array
import json
import os
import socket
import socketserver
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

from invenio_cli.commands.steps import CommandStep
from invenio_cli.helpers.package_managers import UV, LocalOp
from invenio_cli.helpers.rpc import RPCClient, RPCOp


def _recv_request(sock):
    """Read one JSON line plus any file descriptors sent with it."""
    buf = b""
    fds = []
    fd_size = array.array("i").itemsize
    while b"\n" not in buf:
        data, ancdata, _, _ = sock.recvmsg(4096, socket.CMSG_SPACE(2 * fd_size))
        if not data:
            break
        for level, ctype, cdata in ancdata:
            if level == socket.SOL_SOCKET and ctype == socket.SCM_RIGHTS:
                received = array.array("i")
                received.frombytes(cdata[: len(cdata) - (len(cdata) % fd_size)])
                fds.extend(received)
        buf += data
    return buf, fds


class FakeInvenioHandler(socketserver.BaseRequestHandler):
    """Respond to the RPC protocol like the invenio RPC server."""

    def handle(self):
        """Answer one JSON-line request with one JSON-line response."""
        line, fds = _recv_request(self.request)
        if not line:
            return  # connect-only liveness probe
        request = json.loads(line)
        if request.get("argv") == ["slow"]:
            time.sleep(0.3)  # simulate a long-running command
        if fds:
            os.write(fds[0], b"streamed out\n")
            os.write(fds[1], b"streamed err\n")
            for fd in fds:
                os.close(fd)
            response = {"exit_code": 7}
        else:
            response = {
                "exit_code": 7,
                "stdout": " ".join(request["argv"]),
                "stderr": "warning\n",
            }
        self.request.sendall(json.dumps(response).encode("utf-8") + b"\n")


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


def test_call_forwards_output_to_our_descriptors(rpc_socket, capfd):
    """By default the command output streams to our stdout/stderr."""
    client = RPCClient(rpc_socket, start_command=None)
    response = client.call(["webpack", "build"])
    assert response.status_code == 7
    captured = capfd.readouterr()
    assert captured.out == "streamed out\n"
    assert captured.err == "streamed err\n"


def test_call_forwards_output_to_a_log_file(rpc_socket, short_tmp_path):
    """With a log file, the command output lands there instead."""
    log_file = short_tmp_path / "build.log"
    client = RPCClient(rpc_socket, start_command=None)
    response = client.call(["webpack", "build"], log_file=str(log_file))
    assert response.status_code == 7
    assert log_file.read_text() == "streamed out\nstreamed err\n"


def test_call_captures_output_on_request(rpc_socket):
    """With capture, output comes back on the ProcessResponse."""
    client = RPCClient(rpc_socket, start_command=None)
    response = client.call(["webpack", "build"], capture=True)
    assert response.output == "webpack build"
    assert response.error == "warning\n"
    assert response.status_code == 7


# A stand-in for "invenio rpc-server start": serves the captured-output
# protocol on the socket given as first argument until it is terminated.
# Echoes RPC_TEST_VAR so tests can check the environment it was spawned with.
SERVER_SCRIPT = """
import json, os, socketserver, sys

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        line = self.rfile.readline()
        if not line:
            return  # connect-only liveness probe
        response = {
            "exit_code": 0,
            "stdout": os.environ.get("RPC_TEST_VAR", "ok"),
            "stderr": "",
        }
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
    response = client.call(["collect"], capture=True)
    assert response.status_code == 0
    assert response.output == "ok"
    client.shutdown()
    assert client.server.poll() is not None


def test_call_passes_env_to_the_spawned_server(short_tmp_path):
    """env reaches the server's environment when this call spawns it."""
    socket_path = short_tmp_path / "rpc.sock"
    client = RPCClient(
        socket_path, [sys.executable, "-c", SERVER_SCRIPT, str(socket_path)]
    )
    response = client.call(["collect"], env={"RPC_TEST_VAR": "hello"}, capture=True)
    assert response.output == "hello"
    client.shutdown()


def test_call_reports_a_server_that_dies_during_startup(short_tmp_path):
    """A start command that exits early fails the call instead of hanging."""
    client = RPCClient(
        short_tmp_path / "rpc.sock", [sys.executable, "-c", "raise SystemExit(3)"]
    )
    response = client.call(["collect"])
    assert response.status_code == 1
    assert "exited with code 3" in response.error


def test_spawn_race_loser_uses_the_listening_server(rpc_socket):
    """A dead spawn is fine when another server owns the socket."""
    client = RPCClient(rpc_socket, ["sh", "-c", "exit 9"])
    assert client.ensure_running() is None


def test_concurrent_calls_queue_behind_a_busy_server(rpc_socket):
    """Calls connect directly and wait their turn instead of respawning."""
    client = RPCClient(rpc_socket, start_command=None)
    results = []

    def run():
        """Issue one slow captured call."""
        results.append(client.call(["slow"], capture=True).status_code)

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert results == [7, 7]


def test_invenio_command_builds_an_rpc_op(short_tmp_path):
    """With a socket path, invenio_command defers to the RPC server."""
    manager = UV(rpc_socket_path=short_tmp_path / "rpc.sock")
    op = manager.invenio_command("invenio", "webpack", "build")
    assert isinstance(op, RPCOp)
    assert op.argv == ["webpack", "build"]
    assert op.label == "build"


def test_invenio_command_without_rpc_builds_a_local_op():
    """Without a socket path, invenio_command wraps the plain command."""
    op = UV().invenio_command("invenio", "collect")
    assert isinstance(op, LocalOp)
    assert op.argv == ["uv", "run", "--no-sync", "invenio", "collect"]
    assert op.label == "collect"


def test_local_op_runs_a_subprocess():
    """LocalOp runs the argv and reports the real exit code."""
    assert LocalOp(["sh", "-c", "exit 3"])().status_code == 3
    assert LocalOp(["sh", "-c", "echo hi"])(capture=True).output == "hi\n"


def test_command_step_executes_an_op(rpc_socket, capfd):
    """CommandStep runs an op, with output forwarded and the exit code kept."""
    client = RPCClient(rpc_socket, start_command=None)
    step = CommandStep(cmd=RPCOp(client, ["db", "init", "create"]))
    response = step.execute()
    assert response.status_code == 7
    assert capfd.readouterr().out == "streamed out\n"


def test_command_step_skippable_turns_op_failure_into_warning(rpc_socket, capfd):
    """A skippable step reports a failed RPC command as a warning."""
    client = RPCClient(rpc_socket, start_command=None)
    step = CommandStep(cmd=RPCOp(client, ["db", "destroy"]), skippable=True)
    response = step.execute()
    assert response.status_code == 0
    assert response.warning is True
