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

"""This module contains the default error handler class."""

from logging import Logger

from aea.error_handler.base import AbstractErrorHandler
from aea.mail.base import Envelope


class ErrorHandler(AbstractErrorHandler):
    """Error handler class for handling problematic envelopes."""

    unsupported_protocol_count = 0
    no_active_handler_count = 0
    decoding_error_count = 0

    @classmethod
    def send_unsupported_protocol(cls, envelope: Envelope, logger: Logger) -> None:
        """
        Handle the received envelope in case the protocol is not supported.

        :param envelope: the envelope
        :return: None
        """
        cls.unsupported_protocol_count += 1
        logger.warning(
            f"Unsupported protocol: protocol_specification_id={envelope.protocol_specification_id}. You might want to add a handler for a protocol implementing this specification. Sender={envelope.sender}, to={envelope.sender}."
        )

    @classmethod
    def send_decoding_error(
        cls, envelope: Envelope, exception: Exception, logger: Logger
    ) -> None:
        """
        Handle a decoding error.

        :param envelope: the envelope
        :param exception: the exception raised during decoding
        :param logger: the logger
        :return: None
        """
        cls.decoding_error_count += 1
        logger.warning(
            f"Decoding error for envelope: {envelope}. Protocol_specification_id='{envelope.protocol_specification_id}' and message are inconsistent. Sender={envelope.sender}, to={envelope.sender}. Exception={exception}."
        )

    @classmethod
    def send_no_active_handler(
        cls, envelope: Envelope, reason: str, logger: Logger
    ) -> None:
        """
        Handle the received envelope in case the handler is not supported.

        :param envelope: the envelope
        :param reason: the reason for the failure
        :return: None
        """
        cls.no_active_handler_count += 1
        logger.warning(
            f"Cannot handle envelope: {reason}. Sender={envelope.sender}, to={envelope.sender}."
        )
