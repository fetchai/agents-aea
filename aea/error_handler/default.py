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
    unsupported_skill_count = 0
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
            f"Unsupported protocol: {envelope.protocol_id}. You might want to add a handler for this protocol. Sender={envelope.sender}, to={envelope.sender}."
        )

    @classmethod
    def send_decoding_error(cls, envelope: Envelope, logger: Logger) -> None:
        """
        Handle a decoding error.

        :param envelope: the envelope
        :return: None
        """
        cls.decoding_error_count += 1
        logger.warning(
            f"Decoding error for envelope: {envelope}. Protocol_id='{envelope.protocol_id}' and message are inconsistent. Sender={envelope.sender}, to={envelope.sender}."
        )

    @classmethod
    def send_unsupported_skill(cls, envelope: Envelope, logger: Logger) -> None:
        """
        Handle the received envelope in case the skill is not supported.

        :param envelope: the envelope
        :return: None
        """
        cls.unsupported_skill_count += 1
        if envelope.skill_id is None:
            logger.warning(
                f"Cannot handle envelope: no active handler registered for the protocol_id='{envelope.protocol_id}'. Sender={envelope.sender}, to={envelope.sender}."
            )
        else:
            logger.warning(
                f"Cannot handle envelope: no active handler registered for the protocol_id='{envelope.protocol_id}' and skill_id='{envelope.skill_id}'. Sender={envelope.sender}, to={envelope.sender}."
            )
