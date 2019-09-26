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

"""This package contains the implementation of the handler for the 'default' protocol."""
import base64
import logging
from typing import Optional

from aea.configurations.base import ProtocolId
from aea.mail.base import Envelope
from aea.protocols.base import Protocol
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Handler

logger = logging.getLogger(__name__)


class ErrorHandler(Handler):
    """This class implements the error handler."""

    SUPPORTED_PROTOCOL = 'default'  # type: Optional[ProtocolId]

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Implement the reaction to an envelope.

        :param envelope: the envelope
        :return: None
        """
        pass

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def send_unsupported_protocol(self, envelope: Envelope) -> None:
        """
        Handle the received envelope in case the protocol is not supported.

        :param envelope: the envelope
        :return: None
        """
        logger.warning("Unsupported protocol: {}".format(envelope.protocol_id))
        reply = DefaultMessage(type=DefaultMessage.Type.ERROR,
                               error_code=DefaultMessage.ErrorCode.UNSUPPORTED_PROTOCOL.value,
                               error_msg="Unsupported protocol.",
                               error_data={"protocol_id": envelope.protocol_id})
        self.context.outbox.put_message(to=envelope.sender, sender=self.context.agent_public_key,
                                        protocol_id=DefaultMessage.protocol_idl,
                                        message=DefaultSerializer().encode(reply))

    def send_decoding_error(self, envelope: Envelope) -> None:
        """
        Handle a decoding error.

        :param envelope: the envelope
        :return: None
        """
        logger.warning("Decoding error: {}.".format(envelope))
        encoded_envelope = base64.b85encode(envelope.encode()).decode("utf-8")
        reply = DefaultMessage(type=DefaultMessage.Type.ERROR,
                               error_code=DefaultMessage.ErrorCode.DECODING_ERROR.value,
                               error_msg="Decoding error.",
                               error_data={"envelope": encoded_envelope})
        self.context.outbox.put_message(to=envelope.sender, sender=self.context.agent_public_key,
                                        protocol_id="error",
                                        message=DefaultSerializer().encode(reply))

    def send_invalid_message(self, envelope: Envelope) -> None:
        """
        Handle an message that is invalid wrt a protocol.

        :param envelope: the envelope
        :return: None
        """
        logger.warning("Invalid message wrt protocol: {}.".format(envelope.protocol_id))
        encoded_envelope = base64.b85encode(envelope.encode()).decode("utf-8")
        reply = DefaultMessage(type=DefaultMessage.Type.ERROR,
                               error_code=DefaultMessage.ErrorCode.INVALID_MESSAGE.value,
                               error_msg="Invalid message.",
                               error_data={"envelope": encoded_envelope})
        self.context.outbox.put_message(to=envelope.sender, sender=self.context.agent_public_key,
                                        protocol_id="error",
                                        message=DefaultSerializer().encode(reply))

    def send_unsupported_skill(self, envelope: Envelope, protocol: Protocol) -> None:
        """
        Handle the received envelope in case the skill is not supported.

        :param envelope: the envelope
        :param protocol: the protocol
        :return: None
        """
        logger.warning("Cannot handle envelope: no handler registered for the protocol '{}'.".format(protocol.id))
        encoded_envelope = base64.b85encode(envelope.encode()).decode("utf-8")
        reply = DefaultMessage(type=DefaultMessage.Type.ERROR,
                               error_code=DefaultMessage.ErrorCode.UNSUPPORTED_SKILL.value,
                               error_msg="Unsupported skill.",
                               error_data={"envelope": encoded_envelope})
        self.context.outbox.put_message(to=envelope.sender, sender=self.context.agent_public_key,
                                        protocol_id="error",
                                        message=DefaultSerializer().encode(reply))
