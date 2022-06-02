# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

"""This module contains a scaffold of the error handler class."""
from logging import Logger

from aea.error_handler.base import AbstractErrorHandler
from aea.mail.base import Envelope


class ErrorHandler(AbstractErrorHandler):
    """This class implements the error handler."""

    def send_unsupported_protocol(self, envelope: Envelope, logger: Logger) -> None:
        """
        Handle the received envelope in case the protocol is not supported.

        :param envelope: the envelope
        :param logger: the logger
        """
        raise NotImplementedError

    def send_decoding_error(
        self, envelope: Envelope, exception: Exception, logger: Logger
    ) -> None:
        """
        Handle a decoding error.

        :param envelope: the envelope
        :param exception: the exception raised during decoding
        :param logger: the logger
        """
        raise NotImplementedError

    def send_no_active_handler(
        self, envelope: Envelope, reason: str, logger: Logger
    ) -> None:
        """
        Handle the received envelope in case the handler is not supported.

        :param envelope: the envelope
        :param reason: the reason for the failure
        :param logger: the logger
        """
        raise NotImplementedError
