# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This test module contains the tests for the `aea gui` sub-commands."""
import io
import os
import shutil
import tempfile

import aea.cli_gui


def create_app():
    """Create a debug version of the flask app for testing against."""
    app = aea.cli_gui.run_test()
    app.debug = True
    app.testing = True
    return app


class DummyPID:
    """Mimics the behaviour of a process id."""

    def __init__(self, return_code, stdout_str, stderr_str):
        """Initialise the class."""
        self.return_code = return_code
        self.stdout = io.BytesIO(stdout_str.encode(encoding="UTF-8"))
        self.stderr = io.BytesIO(stderr_str.encode(encoding="UTF-8"))

    def poll(self):
        """Mimic the process id poll function."""
        return self.return_code


class TempCWD:
    """Create a temporary current working directory."""

    def __init__(self):
        """Initialise the class."""
        self.temp_dir = tempfile.mkdtemp()
        self.cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def __enter__(self):
        """Create the empty directory in a context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore the initial conditions."""
        self.destroy()

    def destroy(self):
        """Destroy the cwd and restore the old one."""
        os.chdir(self.cwd)
        try:
            shutil.rmtree(self.temp_dir)
        except (OSError, IOError):
            pass
