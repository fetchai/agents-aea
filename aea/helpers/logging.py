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
"""Logging helpers."""
import logging
from logging import Logger, LoggerAdapter
from typing import Any, MutableMapping, Optional, Tuple, Union


class AgentLoggerAdapter(LoggerAdapter):
    """This class is a logger adapter that prepends the agent name to log messages."""

    def __init__(self, logger: Logger, agent_name: str):
        """
        Initialize the logger adapter.

        :param agent_name: the agent name.
        """
        super().__init__(logger, dict(agent_name=agent_name))

    def process(
        self, msg: Any, kwargs: MutableMapping[str, Any]
    ) -> Tuple[Any, MutableMapping[str, Any]]:
        """Prepend the agent name to every log message."""
        return f"[{self.extra['agent_name']}] {msg}", kwargs


class WithLogger:
    """Interface to endow subclasses with a logger."""

    def __init__(
        self,
        logger: Optional[Union[Logger, LoggerAdapter]] = None,
        default_logger_name: str = "aea",
    ):
        """
        Initialize the logger.

        :param logger: the logger object.
        :param default_logger_name: the default logger name, if a logger is not provided.
        """
        self._logger = logger
        self._default_logger_name = default_logger_name

    @property
    def logger(self) -> Union[Logger, LoggerAdapter]:
        """Get the component logger."""
        if self._logger is None:
            # if not set (e.g. programmatic instantiation)
            # return a default one with the default logger name.
            return logging.getLogger(self._default_logger_name)
        return self._logger

    @logger.setter
    def logger(self, logger: Union[Logger, LoggerAdapter]):
        """Set the logger."""
        self._logger = logger
