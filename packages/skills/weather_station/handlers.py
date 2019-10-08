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
import json
import time
from typing import Any, Dict, List, Optional, Union, cast, TYPE_CHECKING

from aea.configurations.base import ProtocolId
from aea.mail.base import Envelope
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.models import Description
from aea.skills.base import Handler

if TYPE_CHECKING:
    from packages.skills.weather_station.db_communication import DBCommunication
else:
    from weather_station_skill.db_communication import DBCommunication

logger = logging.getLogger("aea.weather_station_skill")

DATE_ONE = "3/10/2019"
DATE_TWO = "15/10/2019"


class MyWeatherHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = FIPAMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialise the behaviour."""
        super().__init__(**kwargs)
        self.fet_price = 0.002
        self.db = DBCommunication()
        self.fetched_data = []

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
        msg = cast(FIPAMessage, msg)
        msg_performative = FIPAMessage.Performative(msg.get('performative'))
        message_id = cast(int, msg.get('id'))
        dialogue_id = cast(int, msg.get('dialogue_id'))

        if msg_performative == FIPAMessage.Performative.CFP:
            self.handle_cfp(msg, envelope.sender, message_id, dialogue_id)
        elif msg_performative == FIPAMessage.Performative.ACCEPT:
            self.handle_accept(envelope.sender)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def handle_cfp(self, msg: FIPAMessage, sender: str, message_id: int, dialogue_id: int) -> None:
        """
        Handle the CFP calls.

        :param msg: the message
        :param sender: the sender
        :param message_id: the message id
        :param dialogue_id: the dialogue id
        :return: None
        """
        new_message_id = message_id + 1
        new_target = message_id
        fetched_data = self.db.get_data_for_specific_dates(DATE_ONE, DATE_TWO)

        if len(fetched_data) >= 1:
            self.fetched_data = fetched_data
            total_price = self.fet_price * len(fetched_data)
            proposal = [Description({"Rows": len(fetched_data),
                                     "Price": total_price})]
            logger.info("[{}]: sending sender={} a proposal at price={}".format(self.context.agent_name, sender, total_price))
            proposal_msg = FIPAMessage(message_id=new_message_id,
                                       dialogue_id=dialogue_id,
                                       target=new_target,
                                       performative=FIPAMessage.Performative.PROPOSE,
                                       proposal=proposal)
            self.context.outbox.put_message(to=sender,
                                            sender=self.context.agent_public_key['default'],
                                            protocol_id=FIPAMessage.protocol_id,
                                            message=FIPASerializer().encode(proposal_msg))
        else:
            logger.info("[{}]: declined the CFP from sender={}".format(self.context.agent_name, sender))
            decline_msg = FIPAMessage(message_id=new_message_id,
                                      dialogue_id=dialogue_id,
                                      target=new_target,
                                      performative=FIPAMessage.Performative.DECLINE)
            self.context.outbox.put_message(to=sender,
                                            sender=self.context.agent_public_key['default'],
                                            protocol_id=FIPAMessage.protocol_id,
                                            message=FIPASerializer().encode(decline_msg))

    def handle_accept(self, sender: str) -> None:
        """
        Handle the Accept Calls.

        :param sender: the sender
        :return: None
        """
        command = {}  # type: Dict[str, Union[str, List[Any]]]
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
            command['fetched_data'].append(dict_of_data)  # type: ignore
            counter += 1
            if counter == 10:
                break
        json_data = json.dumps(command)
        json_bytes = json_data.encode("utf-8")
        logger.info("[{}]: handling accept and sending weather data to sender={}".format(self.context.agent_name, sender))
        data_msg = DefaultMessage(
            type=DefaultMessage.Type.BYTES, content=json_bytes)
        self.context.outbox.put_message(to=sender,
                                        sender=self.context.agent_public_key['default'],
                                        protocol_id=DefaultMessage.protocol_id,
                                        message=DefaultSerializer().encode(data_msg))
