# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI Logging class and functions."""

import logging
import os
import threading

logging.basicConfig(filename='invenio-cli.log',
                    format='%(message)s', level=logging.INFO)


class LogPipe(threading.Thread):
    """Logging pipe object to support forwarding subprocess and Popen logs.

    Based on https://codereview.stackexchange.com/questions/6567
    """

    def __init__(self, level):
        """Setup the object with a logger and a level and start the thread."""
        threading.Thread.__init__(self)
        self.daemon = False
        self.level = level
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)
        self.start()

    def fileno(self):
        """Return the write file descriptor of the pipe."""
        return self.fdWrite

    def run(self):
        """Run the thread, logging everything."""
        for line in iter(self.pipeReader.readline, ''):
            logging.log(self.level, line.strip('\n'))

        self.pipeReader.close()

    def close(self):
        """Close the write end of the pipe."""
        os.close(self.fdWrite)
