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
    result = subprocess.Popen(["aea", "--version"], stdout=subprocess.PIPE)
    try:
        result.wait(timeout=2.0)
    except TimeoutError:
        pytest.fail("The command didn't terminate in a reasonable amount of time.")

    stdout, stderr = result.communicate()
    assert stdout == "aea, version {}\n".format(aea.__version__).encode("utf-8")
