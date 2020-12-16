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
import os
import platform
import re
import signal
import time
from copy import copy
from pathlib import Path
from subprocess import Popen  # nosec
from tempfile import TemporaryDirectory
from typing import Dict, Set
from unittest.mock import patch

import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.base import (
    MaxRetriesError,
    RegexConstrainedString,
    ensure_dir,
    exception_log_and_reraise,
    find_topological_order,
    load_env_file,
    load_module,
    locate,
    reachable_nodes,
    recursive_update,
    retry_decorator,
    send_control_c,
    try_decorator,
    win_popen_kwargs,
)

from packages.fetchai.connections.oef.connection import OEFConnection

from tests.conftest import CUR_PATH, ROOT_DIR, skip_test_windows


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


@skip_test_windows
def test_send_control_c_group():
    """Test send control c to process group."""
    # Can't test process group id kill directly,
    # because o/w pytest would be stopped.
    process = Popen(["sleep", "1"])  # nosec
    pgid = os.getpgid(process.pid)
    time.sleep(0.1)
    with patch("os.killpg") as mock_killpg:
        send_control_c(process, kill_group=True)
        process.communicate(timeout=3)
        mock_killpg.assert_called_with(pgid, signal.SIGINT)


def test_send_control_c():
    """Test send control c to process."""
    # Can't test process group id kill directly,
    # because o/w pytest would be stopped.
    process = Popen(  # nosec
        ["timeout" if platform.system() == "Windows" else "sleep", "5"],
        **win_popen_kwargs(),
    )
    time.sleep(0.001)
    send_control_c(process)
    process.communicate(timeout=3)
    assert process.returncode != 0


@skip_test_windows
def test_send_control_c_windows():
    """Test send control c on Windows."""
    process = Popen(  # nosec
        ["timeout" if platform.system() == "Windows" else "sleep", "5"]
    )
    time.sleep(0.001)
    pid = process.pid
    with patch("aea.helpers.base.signal") as mock_signal:
        mock_signal.CTRL_C_EVENT = "mock"
        with patch("platform.system", return_value="Windows"):
            with patch("os.kill") as mock_kill:
                send_control_c(process)
                mock_kill.assert_called_with(pid, mock_signal.CTRL_C_EVENT)


def test_recursive_update_no_recursion():
    """Test the 'recursive update' utility, in the case there's no recursion."""
    to_update = dict(not_updated=0, an_integer=1, a_list=[1, 2, 3], a_tuple=(1, 2, 3))

    new_integer, new_list, new_tuple = 2, [3], (3,)
    new_values = dict(an_integer=new_integer, a_list=new_list, a_tuple=new_tuple)
    recursive_update(to_update, new_values)
    assert to_update == dict(
        not_updated=0, an_integer=new_integer, a_list=new_list, a_tuple=new_tuple
    )


def test_recursive_update_with_recursion():
    """Test the 'recursive update' utility with recursion."""
    # here we try to update an integer and add a new value
    to_update = dict(subdict=dict(to_update=1))
    new_values = dict(subdict=dict(to_update=2))

    recursive_update(to_update, new_values)
    assert to_update == dict(subdict=dict(to_update=2))


def test_recursive_update_negative_different_type():
    """Test the 'recursive update' utility, when the types are different."""
    # here we try to update an integer with a boolean - it raises error.
    to_update = dict(subdict=dict(to_update=1))
    new_values = dict(subdict=dict(to_update=False))

    with pytest.raises(
        ValueError,
        match="Trying to replace value '1' with value 'False' which is of different type.",
    ):
        recursive_update(to_update, new_values)


def test_recursive_update_negative_unknown_field():
    """Test the 'recursive update' utility, when there are unknown fields."""
    # here we try to update an integer with a boolean - it raises error.
    to_update = dict(subdict=dict(field=1))
    new_values = dict(subdict=dict(new_field=False))

    with pytest.raises(
        ValueError,
        match="Key 'new_field' is not contained in the dictionary to update.",
    ):
        recursive_update(to_update, new_values)


class TestTopologicalOrder:
    """Test the computation of topological order."""

    def test_empty_graph(self):
        """Test the function with empty input."""
        order = find_topological_order({})
        assert order == []

    def test_one_node(self):
        """Test the function with only one node."""
        order = find_topological_order({0: set()})
        assert order == [0]

    def test_one_node_with_cycle(self):
        """Test the function with only one node and a loop."""
        with pytest.raises(ValueError, match="Graph has at least one cycle."):
            find_topological_order({0: {0}})

    def test_two_nodes_no_edges(self):
        """Test the function with two nodes, but no edges."""
        order = find_topological_order({0: set(), 1: set()})
        assert order == [0, 1]

    def test_two_nodes_no_cycle(self):
        """Test the function with two nodes, but no cycles."""
        order = find_topological_order({0: {1}})
        assert order == [0, 1]

    def test_two_nodes_with_cycle(self):
        """Test the function with two nodes and a cycle between them."""
        with pytest.raises(ValueError, match="Graph has at least one cycle."):
            find_topological_order({0: {1}, 1: {0}})

    def test_two_nodes_clique(self):
        """Test the function with a clique of two nodes."""
        with pytest.raises(ValueError, match="Graph has at least one cycle."):
            find_topological_order({0: {1, 0}, 1: {0, 1}})

    @pytest.mark.parametrize("chain_length", [3, 5, 10, 100])
    def test_chain(self, chain_length):
        """Test the function with a chain."""
        adj_list: Dict[int, Set[int]] = {}
        for i in range(chain_length - 1):
            adj_list[i] = {i + 1}
        adj_list[chain_length - 1] = set()

        order = find_topological_order(adj_list)
        assert order == list(range(chain_length))


class TestReachableNodes:
    """Test reachable_nodes utility."""

    def test_empty_graph(self):
        """Test empty graph."""
        result = reachable_nodes({}, set())
        assert result == {}

    def test_starting_node_not_in_the_graph(self):
        """Test error when starting node not in the graph."""
        with pytest.raises(
            AEAEnforceError,
            match="These starting nodes are not in the set of nodes: {1}",
        ):
            reachable_nodes({}, {1})

    def test_one_node(self):
        """Test one node."""
        result = reachable_nodes({1: set()}, {1})
        assert result == {1: set()}

    def test_one_node_loop(self):
        """Test one node, loop."""
        g = {1: {1}}
        result = reachable_nodes(g, {1})
        assert result == g

    def test_two_nodes(self):
        """Test two nodes."""
        g = {1: {2}}
        result = reachable_nodes(g, {1})
        assert result == g

        result = reachable_nodes(g, {2})
        assert result == {2: set()}

    def test_two_nodes_cycle(self):
        """Test two nodes in a cycle"""
        g = {1: {2}, 2: {1}}
        result = reachable_nodes(g, {1})
        assert result == g

        result = reachable_nodes(g, {2})
        assert result == g

    def test_chain(self):
        """Test chain"""
        g = {1: {2}, 2: {3}, 3: set()}
        result = reachable_nodes(g, {1})
        assert result == g

        result = reachable_nodes(g, {2})
        expected = copy(g)
        expected.pop(1)
        assert result == expected

        result = reachable_nodes(g, {3})
        assert result == {3: set()}


def test_ensure_dir():
    """Test ensure_dir."""
    dir_name = "test"
    with TemporaryDirectory() as tmpdirname:
        full_path = os.path.join(tmpdirname, dir_name)
        assert not os.path.exists(full_path)
        ensure_dir(full_path)
        assert os.path.exists(full_path)
        file_path = os.path.join(full_path, "file_name")
        with open(file_path, "w"):
            pass

        with pytest.raises(AEAEnforceError):
            ensure_dir(file_path)
