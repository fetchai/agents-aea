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

"""This test module contains the tests for the `aea` sub-commands."""
import subprocess
import sys

import pytest
from click.testing import CliRunner

import aea
from aea.cli import cli


def test_no_argument():
    """Test that if we run the cli tool without arguments, it exits gracefully."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0


def test_flag_version():
    """Test that the flag '--version' works correctly."""
    result = subprocess.Popen([sys.executable, "-m", "aea.cli", "--version"], stdout=subprocess.PIPE)
    try:
        result.wait(timeout=5.0)
    except TimeoutError:
        pytest.fail("The command didn't terminate in a reasonable amount of time.")

    stdout, stderr = result.communicate()
    assert stdout == "aea, version {}\n".format(aea.__version__).encode("utf-8")


def test_flag_help():
    """Test that the flag '--help' works correctly."""
    result = subprocess.Popen([sys.executable, "-m", "aea.cli", "--help"], stdout=subprocess.PIPE)
    try:
        result.wait(timeout=5.0)
    except TimeoutError:
        pytest.fail("The command didn't terminate in a reasonable amount of time.")

    stdout, stderr = result.communicate()
    assert stdout == b'Usage: aea [OPTIONS] COMMAND [ARGS]...\n\n  Command-line tool for setting up an Autonomous Economic Agent.\n\nOptions:\n  --version            Show the version and exit.\n  -v, --verbosity LVL  One of NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL,\n                       OFF\n  --help               Show this message and exit.\n\nCommands:\n  add       Add a resource to the agent.\n  create    Create an agent.\n  delete    Delete an agent.\n  freeze    Get the dependencies.\n  gui       Run the CLI GUI.\n  install   Install the dependencies.\n  list      List the installed resources.\n  remove    Remove a resource from the agent.\n  run       Run the agent.\n  scaffold  Scaffold a resource for the agent.\n  search    Search for components in the registry.\n'
