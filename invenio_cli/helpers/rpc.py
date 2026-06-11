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
import os
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

    def listening(self):
        """Return whether something accepts connections on the socket.

        Unlike ``ping`` this does not need the server to respond, so it
        also recognizes a server that is busy running a long command.
        """
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(CONNECT_TIMEOUT)
                s.connect(self.socket_path)
            return True
        except OSError:
            return False

    def ensure_running(self, env=None):
        """Spawn a server and wait until its socket accepts connections.

        Returns an error message, or None on success. The server binds the
        socket only after its app is fully created, so accepting
        connections means ready. ``env`` is added to the spawned server's
        environment, so it lands in the app config the server builds at
        startup (e.g. ``INVENIO_*`` variables).
        """
        self.server = Popen(self.start_command, env={**os.environ, **(env or {})})
        atexit.register(self.shutdown)
        deadline = time.monotonic() + STARTUP_TIMEOUT
        while time.monotonic() < deadline:
            if self.listening():
                return None
            if self.server.poll() is not None:
                # our spawn may have lost a race against another invenio-cli
                # whose server now owns the socket — that is still a success
                if self.listening():
                    return None
                return (
                    "RPC server exited with code "
                    f"{self.server.returncode} during startup."
                )
            time.sleep(0.2)

        self.shutdown()
        return f"RPC server did not start within {STARTUP_TIMEOUT} seconds."

    def call(self, argv, env=None, log_file=None, capture=False):
        """Run an invenio CLI command on the server.

        The request is sent directly: a busy single-threaded server queues
        the connection until it is free, and only a refused or missing
        socket makes the client spawn a server (with ``env`` applied to it)
        and retry once. By default the command's output streams live to
        this process' stdout/stderr (or into ``log_file``) via the passed
        descriptors; with ``capture`` it is returned on the response.
        """
        try:
            try:
                return self.request_command(argv, log_file, capture)
            except (FileNotFoundError, ConnectionRefusedError):
                # nothing is listening on the socket
                error = self.ensure_running(env=env)
                if error:
                    return ProcessResponse(error=error, status_code=1)
                return self.request_command(argv, log_file, capture)
        except (OSError, ValueError) as e:
            return ProcessResponse(error=f"RPC request failed: {e}", status_code=1)

    def request_command(self, argv, log_file=None, capture=False):
        """Send one command request to a listening server."""
        payload = {"argv": list(argv)}
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
        """Execute on the RPC server.

        ``env`` reaches the server's environment (and thus its app config)
        only when this call is the one that spawns it; a server that is
        already running keeps the environment it was started with.
        """
        return self.client.call(self.argv, env=env, log_file=log_file, capture=capture)
