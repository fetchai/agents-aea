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

import json
import time
from typing import Optional

from aea.configurations.base import ProtocolId
from aea.mail.base import Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.models import Description
from aea.skills.base import Handler
from .db_communication import Db_communication


class MyWeatherHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = 'fipa'  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialise the behaviour."""
        super().__init__(**kwargs)
        self.fet_price = 0.002
        self.db = Db_communication("fake")
        self.fetched_data = []
        self.message_id = 1
        self.target = 0
        self.dialogue_id = 1

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Implement the reaction to an envelope.

        :param envelope: the envelope
        :return: None
        """
        msg = FIPASerializer().decode(envelope.message)
        msg_performative = FIPAMessage.Performative(msg.get('performative'))

        if msg_performative == FIPAMessage.Performative.CFP:
            self.handle_CFP(msg, envelope.sender)
        elif msg_performative == FIPAMessage.Performative.ACCEPT:
            self.handle_ACCEPT(envelope.sender)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def handle_CFP(self, msg, sender):
        """Handle the CFP calls."""
        fetched_data = self.db.specific_dates("3/10/2019", "4/10/2019")

        if len(fetched_data) >= 1:
            self.fetched_data = fetched_data
            totalPrice = self.fet_price * len(fetched_data)
            proposal = [Description({"Rows": len(fetched_data),
                                     "Price": totalPrice})]
            print("[{}]: Sending propose at price: {}".format(
                sender, totalPrice))
            proposal_msg = FIPAMessage(message_id=self.message_id,
                                       dialogue_id=self.dialogue_id,
                                       target=self.target,
                                       performative=FIPAMessage.Performative.PROPOSE,
                                       proposal=proposal)
            self.context.outbox.put_message(to=sender,
                                            sender=self.context.agent_public_key,
                                            protocol_id=FIPAMessage.protocol_id,
                                            message=FIPASerializer().encode(proposal_msg))
        else:
            decline_msg = FIPAMessage(message_id=1,
                                      dialogue_id=0,
                                      target=0,
                                      performative=FIPAMessage.Performative.DECLINE)
            self.context.outbox.put_message(to=sender,
                                            sender=self.context.agent_public_key,
                                            protocol_id=FIPAMessage.protocol_id,
                                            message=FIPASerializer().encode(decline_msg))

    def handle_ACCEPT(self, sender):
        """Handle the Accept Calls."""
        command = {}
        command['Command'] = "success"
        command['fetched_data'] = []
        counter = 0
        for items in self.fetched_data:
            dict_of_data = {}
            dict_of_data['abs_pressure'] = items[0]
            dict_of_data['delay'] = items[1]
            dict_of_data['hum_in'] = items[2]
            dict_of_data['hum_out'] = items[3]
            dict_of_data['idx'] = time.ctime(int(items[4]))
            dict_of_data['rain'] = items[5]
            dict_of_data['temp_in'] = items[6]
            dict_of_data['temp_out'] = items[7]
            dict_of_data['wind_ave'] = items[8]
            dict_of_data['wind_dir'] = items[9]
            dict_of_data['wind_gust'] = items[10]
            command['fetched_data'].append(dict_of_data)
            counter += 1
            if counter == 10:
                break
        json_data = json.dumps(command)
        json_bytes = json_data.encode("utf-8")
        data_msg = DefaultMessage(
            type=DefaultMessage.Type.BYTES, content=json_bytes)
        self.context.outbox.put_message(to=sender,
                                        sender=self.context.agent_public_key,
                                        protocol_id=DefaultMessage.protocol_id,
                                        message=DefaultSerializer().encode(data_msg))
