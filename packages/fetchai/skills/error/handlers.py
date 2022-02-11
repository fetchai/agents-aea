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

"""This package contains the implementation of the handler for the 'default' protocol."""

import base64
from typing import Optional

from aea.configurations.base import PublicId
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.default.message import DefaultMessage


class ErrorHandler(Handler):
    """This class implements the error handler."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def send_unsupported_protocol(self, envelope: Envelope) -> None:
        """
        Handle the received envelope in case the protocol is not supported.

        :param envelope: the envelope
        """
        self.context.logger.warning(
            "Unsupported protocol: {}. You might want to add a handler for this protocol.".format(
                envelope.protocol_specification_id
            )
        )
        encoded_protocol_specification_id = base64.b85encode(
            str.encode(str(envelope.protocol_specification_id))
        )
        encoded_envelope = base64.b85encode(envelope.encode())
        reply = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.UNSUPPORTED_PROTOCOL,
            error_msg="Unsupported protocol.",
            error_data={
                "protocol_id": encoded_protocol_specification_id,
                "envelope": encoded_envelope,
            },
        )
        reply.sender = self.context.agent_address
        reply.to = envelope.sender
        self.context.outbox.put_message(message=reply)

    def send_decoding_error(self, envelope: Envelope) -> None:
        """
        Handle a decoding error.

        :param envelope: the envelope
        """
        self.context.logger.warning(
            "Decoding error for envelope: {}. protocol_specification_id='{}' and message='{!r}' are inconsistent.".format(
                envelope, envelope.protocol_specification_id, envelope.message
            )
        )
        encoded_envelope = base64.b85encode(envelope.encode())
        reply = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.DECODING_ERROR,
            error_msg="Decoding error.",
            error_data={"envelope": encoded_envelope},
        )
        reply.sender = self.context.agent_address
        reply.to = envelope.sender
        self.context.outbox.put_message(message=reply)

    def send_unsupported_skill(self, envelope: Envelope) -> None:
        """
        Handle the received envelope in case the skill is not supported.

        :param envelope: the envelope
        """
        self.context.logger.warning(
            "Cannot handle envelope: no active handler registered for the protocol_specification_id='{}'.".format(
                envelope.protocol_specification_id
            )
        )
        encoded_envelope = base64.b85encode(envelope.encode())
        reply = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.UNSUPPORTED_SKILL,
            error_msg="Unsupported skill.",
            error_data={"envelope": encoded_envelope},
        )
        reply.sender = self.context.agent_address
        reply.to = envelope.sender
        self.context.outbox.put_message(message=reply)
