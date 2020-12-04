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
"""This module contains the abstract error handler class."""
from abc import ABC, abstractmethod
from logging import Logger

from aea.mail.base import Envelope


class AbstractErrorHandler(ABC):
    """Error handler class for handling problematic envelopes."""

    @classmethod
    @abstractmethod
    def send_unsupported_protocol(cls, envelope: Envelope, logger: Logger) -> None:
        """
        Handle the received envelope in case the protocol is not supported.

        :param envelope: the envelope
        :param logger: the logger
        :return: None
        """

    @classmethod
    @abstractmethod
    def send_decoding_error(cls, envelope: Envelope, logger: Logger) -> None:
        """
        Handle a decoding error.

        :param envelope: the envelope
        :return: None
        """

    @classmethod
    @abstractmethod
    def send_unsupported_skill(cls, envelope: Envelope, logger: Logger) -> None:
        """
        Handle the received envelope in case the skill is not supported.

        :param envelope: the envelope
        :return: None
        """
