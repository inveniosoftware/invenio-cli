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


class LogPipe(threading.Thread):
    """Logging pipe object to support forwarding subprocess and Popen logs.

    Based on https://codereview.stackexchange.com/questions/6567
    """

    def __init__(self, log_config):
        """Setup the object with a logger and start the thread."""
        # Set as INFO to allow all logs to be sent
        logging.basicConfig(filename=log_config.logfile, level=logging.INFO)
        threading.Thread.__init__(self)
        self.daemon = False
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)
        self.start()

    def fileno(self):
        """Return the write file descriptor of the pipe."""
        return self.fdWrite

    def run(self):
        """Run the thread, logging everything."""
        for line in iter(self.pipeReader.readline, ''):
            logging.info(line.strip('\n'))

        self.pipeReader.close()

    def close(self):
        """Close the write end of the pipe."""
        os.close(self.fdWrite)


class LoggingConfig(object):
    """Class to encapsulate the logging configuration."""

    def __init__(self, logfile='invenio-cli.log', verbose=False):
        """Constructor for the LoggingConfig helper."""
        super(LoggingConfig, self).__init__()
        self.logfile = logfile
        self.verbose = verbose
