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

"""This package contains a scaffold of a behaviour."""

from aea.skills.base import Behaviour
from .weather_station_dataModel import WEATHER_STATION_DATAMODEL
from aea.protocols.oef.models import Description
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.serialization import OEFSerializer, DEFAULT_OEF


class MyWeatherBehaviour(Behaviour):
    """This class scaffolds a behaviour."""

    def __init__(self, **kwargs):
        """Initialize the behaviour."""
        super().__init__(**kwargs)
        self.registered = False
        self.data_model = WEATHER_STATION_DATAMODEL()
        self.scheme = {}
        self.scheme['country'] = "UK"
        self.scheme['city'] = "Cambridge"

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        if not self.registered:
            desc = Description(self.scheme, data_model=self.data_model)
            msg = OEFMessage(oef_type=OEFMessage.Type.REGISTER_SERVICE,
                             id=1,
                             service_description=desc,
                             service_id="WeatherData")
            msg_bytes = OEFSerializer().encode(msg)
            self.context.outbox.put_message(to=DEFAULT_OEF,
                                            sender=self.context.agent_public_key,
                                            protocol_id=OEFMessage.protocol_id,
                                            message=msg_bytes)
            print("I am registered!")
            print("My public key is : {}".format(self.context.agent_public_key))
            self.registered = True

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass
