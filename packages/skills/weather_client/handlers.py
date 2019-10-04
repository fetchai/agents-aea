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

import pprint
from typing import Optional

from aea.configurations.base import ProtocolId
from aea.mail.base import Envelope
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.serialization import OEFSerializer
from aea.skills.base import Handler


class FIPAHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = 'fipa'  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initiliase the handler."""
        super().__init__(**kwargs)
        self.maxPrice = 2
        self.message_id = 1
        self.dialogue_id = 1
        self.target = 0

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

        if msg_performative == FIPAMessage.Performative.PROPOSE:
            print(len(msg.get("proposal")))
            if len(msg.get("proposal")) > 0:
                for item in msg.get("proposal"):
                    print(item.values)
                    if "Price" in item.values.keys():
                        if item.values["Price"] < self.maxPrice:
                            self.handle_accept(envelope.sender)
                        else:
                            self.handle_decline(envelope.sender)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def handle_accept(self, sender):
        """Handle accept message."""
        msg = FIPAMessage(message_id=self.message_id,
                          dialogue_id=self.dialogue_id,
                          target=self.target,
                          performative=FIPAMessage.Performative.ACCEPT)

        self.context.outbox.put_message(to=sender,
                                        sender=self.context.agent_public_key,
                                        protocol_id=FIPAMessage.protocol_id,
                                        message=FIPASerializer().encode(msg))

    def handle_decline(self, sender):
        """Handle decline message."""
        msg = FIPAMessage(message_id=self.message_id,
                          dialogue_id=self.dialogue_id,
                          target=self.target,
                          performative=FIPAMessage.Performative.DECLINE)

        self.context.outbox.put_message(to=sender,
                                        sender=self.context.agent_public_key,
                                        protocol_id=FIPAMessage.protocol_id,
                                        message=FIPASerializer().encode(msg))


class OEFHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = 'oef'  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialise the oef handler."""
        super().__init__(**kwargs)
        self.maxPrice = 2
        self.message_id = 1
        self.dialogue_id = 1
        self.target = 0
        self.agents = []

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
        mytype = OEFMessage.Type(msg.get("type"))
        if mytype is OEFMessage.Type.SEARCH_RESULT:
            self.agents = msg.get("agents")
            print(len(self.agents))
            for agent in self.agents:
                msg = FIPAMessage(message_id=self.message_id,
                                  dialogue_id=self.dialogue_id,
                                  performative=FIPAMessage.Performative.CFP,
                                  target=self.target,
                                  query=None
                                  )
                self.context.outbox.put_message(to=agent,
                                                sender=self.context.agent_public_key,
                                                protocol_id=FIPAMessage.protocol_id,
                                                message=FIPASerializer().encode(msg))
        pass

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass


class DefaultHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = 'default'  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Call to setup the handler."""
        pass

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Implement the reaction to an envelope.

        :param envelope: the envelope
        :return: None
        """
        print("I am receiving data !!!! ")
        msg = DefaultSerializer().decode(envelope.message)
        json_data = msg.get("content")
        if json_data is not None:
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(json_data.decode())
        else:
            print("He didn't send the data")

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
