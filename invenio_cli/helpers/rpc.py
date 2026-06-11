# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Client for the invenio RPC server.

The server (``invenio rpc-server start``) listens on a Unix domain socket
and runs invenio CLI commands in a long-lived process, so each command
skips the Python startup and app creation cost. The protocol is one JSON
line per request (``{"argv": [...]}``) answered by one JSON line
(``{"exit_code": ..., "stdout": ..., "stderr": ...}``).
"""

import atexit
import json
import socket
import time
from subprocess import Popen, TimeoutExpired

import click

from .process import ProcessResponse

CONNECT_TIMEOUT = 5
PING_TIMEOUT = 2
STARTUP_TIMEOUT = 120  # starting the server includes a full app creation


def echo_output(response, log_file=None):
    """Surface buffered RPC output like a locally run command would."""
    if log_file:
        with open(log_file, "a") as f:
            f.write(response.output or "")
            f.write(response.error or "")
    else:
        if response.output:
            click.echo(response.output, nl=False)
        if response.error:
            click.echo(response.error, nl=False, err=True)


class RPCClient:
    """Talks to the invenio RPC server over its Unix domain socket.

    If no server is listening, one is spawned on first use and terminated
    again when invenio-cli exits; a server the user started themselves is
    used but never owned.
    """

    def __init__(self, socket_path, start_command):
        """Construct."""
        self.socket_path = str(socket_path)
        self.start_command = start_command
        self.server = None
        self.available = False

    def request(self, payload, read_timeout=None):
        """Send one JSON line and read back one JSON-line response."""
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(CONNECT_TIMEOUT)
            s.connect(self.socket_path)
            s.sendall(json.dumps(payload).encode("utf-8") + b"\n")
            # commands may run for a long time (e.g. webpack builds)
            s.settimeout(read_timeout)
            with s.makefile("rb") as f:
                return json.loads(f.readline())

    def ping(self):
        """Return whether a server answers on the socket."""
        try:
            response = self.request({"ping": True}, read_timeout=PING_TIMEOUT)
        except (OSError, ValueError):
            return False
        return response.get("pong") is True

    def ensure_running(self):
        """Start a server if none answers; return an error message or None."""
        if self.available:
            return None
        if self.ping():
            self.available = True
            return None

        self.server = Popen(self.start_command)
        atexit.register(self.shutdown)
        deadline = time.monotonic() + STARTUP_TIMEOUT
        while time.monotonic() < deadline:
            if self.server.poll() is not None:
                return (
                    "RPC server exited with code "
                    f"{self.server.returncode} during startup."
                )
            if self.ping():
                self.available = True
                return None
            time.sleep(0.2)

        self.shutdown()
        return f"RPC server did not start within {STARTUP_TIMEOUT} seconds."

    def call(self, argv):
        """Run an invenio CLI command on the server."""
        error = self.ensure_running()
        if error:
            return ProcessResponse(error=error, status_code=1)

        try:
            response = self.request({"argv": list(argv)})
        except (OSError, ValueError) as e:
            return ProcessResponse(error=f"RPC request failed: {e}", status_code=1)

        return ProcessResponse(
            output=response["stdout"],
            error=response["stderr"],
            status_code=response["exit_code"],
        )

    def shutdown(self):
        """Terminate the server if this process spawned it."""
        if self.server is None or self.server.poll() is not None:
            return
        self.server.terminate()
        try:
            self.server.wait(timeout=10)
        except TimeoutExpired:
            self.server.kill()


class RPCCall:
    """Deferred RPC command that can be executed like a function step."""

    def __init__(self, client, argv):
        """Construct."""
        self.client = client
        self.argv = list(argv)

    @property
    def label(self):
        """Subcommand name, used for progress messages."""
        return self.argv[-1]

    def __call__(self):
        """Execute the command on the RPC server."""
        return self.client.call(self.argv)
