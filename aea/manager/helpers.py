# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Project helper tools."""

import os
import pprint
import shutil
import subprocess  # nosec
import sys
import tempfile
from typing import Any, Optional

from aea.exceptions import enforce


class AEAProject:
    """A context manager class to create and delete an AEA project."""

    old_cwd: str
    temp_dir: str

    def __init__(self, name: str = "my_aea", parent_dir: Optional[str] = None):
        """
        Initialize an AEA project.

        :param name: the name of the AEA project.
        :param parent_dir: the parent directory.
        """
        self.name = name
        self.parent_dir = parent_dir

    def __enter__(self) -> None:
        """Create and enter into the project."""
        self.old_cwd = os.getcwd()
        self.temp_dir = tempfile.mkdtemp(dir=self.parent_dir)
        os.chdir(self.temp_dir)

        self.run_aea("create", "--local", "--empty", self.name, "--author", "fetchai")
        os.chdir(self.name)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Exit the context manager."""
        os.chdir(self.old_cwd)
        shutil.rmtree(self.temp_dir)

    @staticmethod
    def run_cli(*args: Any, **kwargs: Any) -> None:
        """Run a CLI command."""
        print(f"Calling command {args} with kwargs {kwargs}")
        return_code = subprocess.check_call(args, **kwargs)  # nosec
        enforce(
            return_code == 0,
            f"Return code of {pprint.pformat(args)} is {return_code} != 0.",
        )

    @classmethod
    def run_aea(cls, *args: Any, **kwargs: Any) -> None:
        """
        Run an AEA command.

        :param args: the AEA command
        :param kwargs: keyword arguments to subprocess function
        """
        cls.run_cli(sys.executable, "-m", "aea.cli", *args, **kwargs)
