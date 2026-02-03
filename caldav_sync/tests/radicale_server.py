"""Radicale CalDAV server for integration testing.

This module provides a Radicale server that can be started and stopped
programmatically for use in integration tests. This mirrors how the
caldav library runs integration tests.
"""

import logging
import os
import shutil
import tempfile
import threading
import time
from wsgiref.simple_server import make_server

from radicale import config
from radicale.app import Application

# Suppress Radicale warnings that are expected during testing
# (e.g., "No user authentication is selected" and "Storage location does not exist")
# These warnings cause OCA CI to fail as it treats warnings as errors
logging.getLogger("radicale").setLevel(logging.ERROR)


class RadicaleTestServer:
    """A Radicale CalDAV server for testing purposes.

    Usage:
        server = RadicaleTestServer()
        server.start()
        # ... run tests against server.url ...
        server.stop()

    Or as a context manager:
        with RadicaleTestServer() as server:
            # ... run tests against server.url ...
    """

    def __init__(self, host="127.0.0.1", port=15232):
        self.host = host
        self.port = port
        self._server = None
        self._thread = None
        self._tmpdir = None
        self._storage_dir = None

    @property
    def url(self):
        """Base URL of the CalDAV server."""
        return f"http://{self.host}:{self.port}"

    def start(self):
        """Start the Radicale server in a background thread."""
        # Create temp directory for storage and config
        self._tmpdir = tempfile.mkdtemp(prefix="radicale_test_")
        self._storage_dir = os.path.join(self._tmpdir, "collections")

        # Create config file
        cfg_path = os.path.join(self._tmpdir, "config")
        with open(cfg_path, "w") as f:
            f.write(
                f"""
[server]
hosts = {self.host}:{self.port}

[storage]
filesystem_folder = {self._tmpdir}

[auth]
type = none

[rights]
type = owner_only
"""
            )

        # Load config and create application
        configuration = config.load([(cfg_path, True)])
        app = Application(configuration)

        # Create and start server
        self._server = make_server(self.host, self.port, app)

        def serve():
            self._server.serve_forever()

        self._thread = threading.Thread(target=serve, daemon=True)
        self._thread.start()

        # Wait for server to be ready
        self._wait_for_ready()

    def _wait_for_ready(self, timeout=5):
        """Wait for the server to be ready to accept connections."""
        import requests

        start = time.time()
        while time.time() - start < timeout:
            resp = requests.get(
                f"{self.url}/.well-known/caldav",
                timeout=1,
                allow_redirects=False,
            )
            if resp.status_code in (200, 301, 302):
                return

    def stop(self):
        """Stop the Radicale server and clean up."""
        if self._server is not None:
            self._server.shutdown()
            self._server = None

        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

        if self._tmpdir is not None:
            shutil.rmtree(self._tmpdir, ignore_errors=True)
            self._tmpdir = None
            self._storage_dir = None

    def create_calendar(self, username, calendar_name="calendar"):
        """Create a calendar for a user and return its URL.

        Args:
            username: The username (used as path component)
            calendar_name: Name of the calendar (default: "calendar")

        Returns:
            The URL of the created calendar
        """
        import requests

        # First create the user collection with MKCOL
        user_url = f"{self.url}/{username}/"
        requests.request("MKCOL", user_url, timeout=5)

        # Then create calendar with MKCALENDAR
        calendar_url = f"{self.url}/{username}/{calendar_name}/"
        requests.request("MKCALENDAR", calendar_url, timeout=5)

        return calendar_url
