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
"""This module contains the tests for the helpers/logging module."""
import logging
from unittest.mock import patch

from aea.helpers.logging import AgentLoggerAdapter, WithLogger, get_logger


def test_get_logger():
    """Test the get_logger function."""
    module_path = "some.dotted.module.path"
    agent_name = "agent_name"
    expected_name = "some.agent_name.dotted.module.path"
    logger = get_logger(module_path, agent_name)
    assert logger.name == expected_name


def test_agent_logger_adapter():
    """Test the agent logger adapter."""
    logger = logging.getLogger("some.logger")
    logger = AgentLoggerAdapter(logger, agent_name="some_agent")
    logger.setLevel("DEBUG")
    with patch.object(logger.logger, "log") as mock_logger:
        logger.debug("Some log message.")
        mock_logger.assert_any_call(logging.DEBUG, "[some_agent] Some log message.")


def test_with_logger_default_logger_name():
    """Test the WithLogger interface, default logger name."""

    class SomeClass(WithLogger):
        pass

    x = SomeClass()
    assert isinstance(x.logger, logging.Logger)
    with patch.object(x.logger, "debug") as mock_logger:
        x.logger.debug("Some log message.")
        mock_logger.assert_any_call("Some log message.")


def test_with_logger_custom_logger_name():
    """Test the WithLogger interface, custom logger name."""

    class SomeClass(WithLogger):
        pass

    x = SomeClass(default_logger_name="some.logger")
    assert isinstance(x.logger, logging.Logger)

    with patch.object(x.logger, "debug") as mock_logger:
        x.logger.debug("Some log message.")
        mock_logger.assert_any_call("Some log message.")


def test_with_logger_custom_logger():
    """Test the WithLogger interface, custom logger."""

    class SomeClass(WithLogger):
        pass

    logger = logging.getLogger("some.logger")
    x = SomeClass(logger=logger)
    assert isinstance(x.logger, logging.Logger)

    with patch.object(x.logger, "debug") as mock_logger:
        x.logger.debug("Some log message.")
        mock_logger.assert_any_call("Some log message.")


def test_with_logger_setter():
    """Test the WithLogger interface, logger setter."""

    class SomeClass(WithLogger):
        pass

    logger_1 = logging.getLogger("some.logger")
    x = SomeClass(logger=logger_1)
    assert isinstance(x.logger, logging.Logger)
    assert x.logger.name == "some.logger"
    logger_2 = logging.getLogger("another.logger")
    x.logger = logger_2
    assert x.logger.name == "another.logger"
