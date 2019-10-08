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

"""This package contains a scaffold of a handler."""

import logging
from typing import Optional, cast, List

from aea.configurations.base import ProtocolId
from aea.mail.base import Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.serialization import OEFSerializer
from aea.protocols.oef.models import Description
from aea.skills.base import Handler

MAX_PRICE = 2
STARTING_MESSAGE_ID = 1
STARTING_TARGET_ID = 0

logger = logging.getLogger("aea.weather_client_skill")


class FIPAHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = FIPAMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initiliase the handler."""
        super().__init__(**kwargs)
        self.max_price = kwargs['max_price'] if 'max_price' in kwargs.keys() else MAX_PRICE

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Implement the reaction to an envelope.

        :param envelope: the envelope
        :return: None
        """
        msg = FIPASerializer().decode(envelope.message)
        msg_performative = FIPAMessage.Performative(msg.get('performative'))
        proposals = cast(List[Description], msg.get("proposal"))
        message_id = cast(int, msg.get("id"))
        dialogue_id = cast(int, msg.get("dialogue_id"))
        if msg_performative == FIPAMessage.Performative.PROPOSE:
            if proposals is not []:
                for item in proposals:
                    logger.info("[{}]: received proposal={} in dialogue={}".format(self.context.agent_name, item.values, dialogue_id))
                    if "Price" in item.values.keys():
                        if item.values["Price"] < self.max_price:
                            self.handle_accept(envelope.sender, message_id, dialogue_id)
                        else:
                            self.handle_decline(envelope.sender, message_id, dialogue_id)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def handle_accept(self, sender: str, message_id: int, dialogue_id: int):
        """
        Handle sending accept message.

        :param sender: the sender of the message
        :param message_id: the message id
        :param dialogue_id: the dialogue id
        """
        new_message_id = message_id + 1
        new_target_id = message_id
        logger.info("[{}]: accepting the proposal from sender={}".format(self.context.agent_name, sender))
        msg = FIPAMessage(message_id=new_message_id,
                          dialogue_id=dialogue_id,
                          target=new_target_id,
                          performative=FIPAMessage.Performative.ACCEPT)
        self.context.outbox.put_message(to=sender,
                                        sender=self.context.agent_public_key['default'],
                                        protocol_id=FIPAMessage.protocol_id,
                                        message=FIPASerializer().encode(msg))

    def handle_decline(self, sender: str, message_id: int, dialogue_id: int):
        """
        Handle sending decline message.

        :param sender: the sender of the message
        :param message_id: the message id
        :param dialogue_id: the dialogue id
        """
        new_message_id = message_id + 1
        new_target_id = message_id
        logger.info("[{}]: declinig the proposal from sender={}".format(self.context.agent_name, sender))
        msg = FIPAMessage(message_id=new_message_id,
                          dialogue_id=dialogue_id,
                          target=new_target_id,
                          performative=FIPAMessage.Performative.DECLINE)
        self.context.outbox.put_message(to=sender,
                                        sender=self.context.agent_public_key['default'],
                                        protocol_id=FIPAMessage.protocol_id,
                                        message=FIPASerializer().encode(msg))


class OEFHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = OEFMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialise the oef handler."""
        super().__init__(**kwargs)
        self.dialogue_id = 1

    def setup(self) -> None:
        """Call to setup the handler."""
        pass

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Implement the reaction to an envelope.

        :param envelope: the envelope
        :return: None
        """
        msg = OEFSerializer().decode(envelope.message)
        msg_type = OEFMessage.Type(msg.get("type"))

        if msg_type is OEFMessage.Type.SEARCH_RESULT:
            agents = cast(List[str], msg.get("agents"))
            logger.info("[{}]: found agents={}".format(self.context.agent_name, agents))
            for agent in agents:
                msg = FIPAMessage(message_id=STARTING_MESSAGE_ID,
                                  dialogue_id=self.dialogue_id,
                                  performative=FIPAMessage.Performative.CFP,
                                  target=STARTING_TARGET_ID,
                                  query=None
                                  )
                self.dialogue_id += 1
                self.context.outbox.put_message(to=agent,
                                                sender=self.context.agent_public_key['default'],
                                                protocol_id=FIPAMessage.protocol_id,
                                                message=FIPASerializer().encode(msg))

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass


class DefaultHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Call to setup the handler."""
        pass

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Implement the reaction to an envelope.

        :param envelope: the envelope
        :return: None
        """
        logger.info("[{}]: receiving data ...".format(self.context.agent_name))
        msg = DefaultSerializer().decode(envelope.message)
        json_data = msg.get("content")
        if json_data is not None:
            logger.info("[{}]: this is the data I got: {}".format(self.context.agent_name, json_data.decode()))
        else:
            logger.info("[{}]: there is no data in the message!".format(self.context.agent_name))

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
