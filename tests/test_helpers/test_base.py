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
"""This module contains the tests for the helper module."""

import io
import os
import re
from collections import OrderedDict
from pathlib import Path

import pytest


from aea.configurations.base import ConnectionConfig
from aea.helpers.base import (
    MaxRetriesError,
    RegexConstrainedString,
    exception_log_and_reraise,
    load_aea_package,
    load_env_file,
    load_module,
    locate,
    retry_decorator,
    try_decorator,
    yaml_dump,
    yaml_load,
)

from packages.fetchai.connections.oef.connection import OEFConnection

from tests.conftest import CUR_PATH, ROOT_DIR


class TestHelpersBase:
    """Test the helper functions."""

    def test_locate(self):
        """Test the locate function to locate modules."""
        cwd = os.getcwd()
        os.chdir(os.path.join(CUR_PATH, ".."))
        gym_package = locate(
            "packages.fetchai.connections.gym.connection.GymConnection"
        )
        non_existing_package = locate(
            "packages.fetchai.connections.non_existing_connection"
        )
        os.chdir(cwd)
        assert gym_package is not None
        assert non_existing_package is None

    def test_locate_class(self):
        """Test the locate function to locate classes."""
        cwd = os.getcwd()
        os.chdir(os.path.join(CUR_PATH, ".."))
        expected_class = OEFConnection
        actual_class = locate(
            "packages.fetchai.connections.oef.connection.OEFConnection"
        )
        os.chdir(cwd)
        # although they are the same class, they are different instances in memory
        # and the build-in default "__eq__" method does not compare the attributes.
        # so compare the names
        assert actual_class is not None
        assert expected_class.__name__ == actual_class.__name__

    def test_locate_with_builtins(self):
        """Test that locate function returns the built-in."""
        result = locate("int.bit_length")
        assert int.bit_length == result

    def test_locate_when_path_does_not_exist(self):
        """Test that locate function returns None when the dotted path does not exist."""
        result = locate("aea.not.existing.path")
        assert result is None

        result = locate("ThisClassDoesNotExist")
        assert result is None


def test_regex_constrained_string_initialization():
    """Test we can initialize a regex constrained with the default regex."""
    RegexConstrainedString("")
    RegexConstrainedString("abcde")
    RegexConstrainedString(b"")
    RegexConstrainedString(b"abcde")
    RegexConstrainedString(RegexConstrainedString(""))
    RegexConstrainedString(RegexConstrainedString("abcde"))


def test_yaml_dump_load():
    """Test yaml dump/load works."""
    data = OrderedDict({"a": 12, "b": None})
    stream = io.StringIO()
    yaml_dump(data, stream)
    stream.seek(0)
    loaded_data = yaml_load(stream)
    assert loaded_data == data


def test_load_aea_package():
    """Test aea package load."""
    config = ConnectionConfig("http_client", "fetchai", "0.5.0")
    config.directory = Path(ROOT_DIR) / "packages"
    load_aea_package(config)


def test_load_module():
    """Test load module from filepath and dotted notation."""
    load_module(
        "packages.fetchai.connections.gym.connection",
        Path(ROOT_DIR)
        / "packages"
        / "fetchai"
        / "connections"
        / "gym"
        / "connection.py",
    )


def test_load_env_file():
    """Test load env file updates process environment variables."""
    load_env_file(Path(ROOT_DIR) / "tests" / "data" / "dot_env_file")
    assert os.getenv("TEST") == "yes"


def test_reg_exp_not_match():
    """Test regexp checks."""
    # for pydocstyle
    class MyReString(RegexConstrainedString):
        REGEX = re.compile(r"[0-9]+")

    with pytest.raises(ValueError):
        MyReString("anystring")


def test_try_decorator():
    """Test try and log decorator."""
    # for pydocstyle
    @try_decorator("oops", default_return="failed")
    def fn():
        raise Exception("expected")

    assert fn() == "failed"


def test_retry_decorator():
    """Test auto retry decorator."""
    num_calls = 0
    retries = 3

    @retry_decorator(retries, "oops. expected")
    def fn():
        nonlocal num_calls
        num_calls += 1
        raise Exception("expected")

    with pytest.raises(MaxRetriesError):
        fn()
    assert num_calls == retries


def test_log_and_reraise():
    """Test log and reraise context manager."""
    log_msg = None

    def fn(msg):
        nonlocal log_msg
        log_msg = msg

    with pytest.raises(ValueError):
        with exception_log_and_reraise(fn, "oops"):
            raise ValueError()

    assert log_msg == "oops"
