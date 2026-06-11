# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Client for the invenio RPC server.

The server (``invenio rpc-server start``) listens on a Unix domain socket
and runs invenio CLI commands in a long-lived process, so each command
skips the Python startup and app creation cost. The protocol is one JSON
line per request (``{"argv": [...]}``) answered by one JSON line. By
default the client passes its stdout/stderr file descriptors with the
request (SCM_RIGHTS), the server streams the command output straight to
them, and the response carries only the exit code; without descriptors
the response carries the captured output instead.
"""

import array
import atexit
import json
import socket
import sys
import time
from subprocess import Popen, TimeoutExpired

from .process import ProcessResponse

CONNECT_TIMEOUT = 5
PING_TIMEOUT = 2
STARTUP_TIMEOUT = 120  # starting the server includes a full app creation


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

    def request(self, payload, fds=None, read_timeout=None):
        """Send one JSON line (and fds) and read back one JSON-line response."""
        line = json.dumps(payload).encode("utf-8") + b"\n"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(CONNECT_TIMEOUT)
            s.connect(self.socket_path)
            if fds:
                s.sendmsg(
                    [line],
                    [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", fds))],
                )
            else:
                s.sendall(line)
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

    def call(self, argv, log_file=None, capture=False):
        """Run an invenio CLI command on the server.

        By default the command's output streams live to this process'
        stdout/stderr (or into ``log_file``) via the passed descriptors.
        With ``capture`` the output is returned on the response instead.
        """
        error = self.ensure_running()
        if error:
            return ProcessResponse(error=error, status_code=1)

        payload = {"argv": list(argv)}
        try:
            if capture:
                response = self.request(payload)
                return ProcessResponse(
                    output=response["stdout"],
                    error=response["stderr"],
                    status_code=response["exit_code"],
                )

            # flush so our own pending output stays ordered with the
            # command output the server writes to the same descriptors
            sys.stdout.flush()
            sys.stderr.flush()
            if log_file:
                with open(log_file, "ab") as f:
                    response = self.request(payload, fds=[f.fileno(), f.fileno()])
            else:
                response = self.request(
                    payload, fds=[sys.stdout.fileno(), sys.stderr.fileno()]
                )
            return ProcessResponse(
                error=response.get("stderr"),
                status_code=response["exit_code"],
            )
        except (OSError, ValueError) as e:
            return ProcessResponse(error=f"RPC request failed: {e}", status_code=1)

    def shutdown(self):
        """Terminate the server if this process spawned it."""
        if self.server is None or self.server.poll() is not None:
            return
        self.server.terminate()
        try:
            self.server.wait(timeout=10)
        except TimeoutExpired:
            self.server.kill()


class RPCOp:
    """Executable invenio command op that runs on the RPC server.

    Has the same call shape as ``LocalOp`` so callers never branch on
    which one they got.
    """

    def __init__(self, client, argv):
        """Construct."""
        self.client = client
        self.argv = list(argv)

    @property
    def label(self):
        """Subcommand name, used for progress messages."""
        return self.argv[-1]

    def __call__(self, env=None, log_file=None, capture=False):
        """Execute on the RPC server; ``env`` is ignored (the server's applies)."""
        return self.client.call(self.argv, log_file=log_file, capture=capture)
