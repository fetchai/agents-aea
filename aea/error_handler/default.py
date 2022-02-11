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

"""This module contains the default error handler class."""

from logging import Logger
from typing import Any

from aea.error_handler.base import AbstractErrorHandler
from aea.mail.base import Envelope


class ErrorHandler(AbstractErrorHandler):
    """Error handler class for handling problematic envelopes."""

    __slots__ = (
        "unsupported_protocol_count",
        "no_active_handler_count",
        "decoding_error_count",
    )

    def __init__(self, **kwargs: Any):
        """Instantiate error handler."""
        super().__init__(**kwargs)
        self.unsupported_protocol_count = 0
        self.no_active_handler_count = 0
        self.decoding_error_count = 0

    def send_unsupported_protocol(self, envelope: Envelope, logger: Logger) -> None:
        """
        Handle the received envelope in case the protocol is not supported.

        :param envelope: the envelope
        :param logger: the logger
        """
        self.unsupported_protocol_count += 1
        logger.warning(
            f"Unsupported protocol: protocol_specification_id={envelope.protocol_specification_id}. You might want to add a handler for a protocol implementing this specification. Sender={envelope.sender}, to={envelope.sender}."
        )

    def send_decoding_error(
        self, envelope: Envelope, exception: Exception, logger: Logger
    ) -> None:
        """
        Handle a decoding error.

        :param envelope: the envelope
        :param exception: the exception raised during decoding
        :param logger: the logger
        """
        self.decoding_error_count += 1
        logger.warning(
            f"Decoding error for envelope: {envelope}. Protocol_specification_id='{envelope.protocol_specification_id}' and message are inconsistent. Sender={envelope.sender}, to={envelope.sender}. Exception={exception}."
        )

    def send_no_active_handler(
        self, envelope: Envelope, reason: str, logger: Logger
    ) -> None:
        """
        Handle the received envelope in case the handler is not supported.

        :param envelope: the envelope
        :param reason: the reason for the failure
        :param logger: the logger
        """
        self.no_active_handler_count += 1
        logger.warning(
            f"Cannot handle envelope: {reason}. Sender={envelope.sender}, to={envelope.sender}."
        )
