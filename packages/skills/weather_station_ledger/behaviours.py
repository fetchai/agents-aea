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

import logging
from typing import cast, TYPE_CHECKING

from aea.skills.base import Behaviour
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.serialization import OEFSerializer, DEFAULT_OEF

if TYPE_CHECKING:
    from packages.skills.weather_station_ledger.strategy import Strategy
else:
    from weather_station_ledger_skill.strategy import Strategy

logger = logging.getLogger("aea.weather_station_ledger_skill")

REGISTER_ID = 1
UNREGISTER_ID = 2
SERVICE_ID = ''


class ServiceRegistrationBehaviour(Behaviour):
    """This class implements a behaviour."""

    def __init__(self, **kwargs):
        """Initialise the behaviour."""
        super().__init__(**kwargs)
        self._registered = False

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        balance = self.context.ledger_apis.token_balance('fetchai', cast(str, self.context.agent_addresses.get('fetchai')))
        logger.info("[{}]: starting balance on fetchai ledger={}.".format(self.context.agent_name, balance))
        if not self._registered:
            strategy = cast(Strategy, self.context.strategy)
            desc = strategy.get_service_description()
            msg = OEFMessage(oef_type=OEFMessage.Type.REGISTER_SERVICE,
                             id=REGISTER_ID,
                             service_description=desc,
                             service_id=SERVICE_ID)
            self.context.outbox.put_message(to=DEFAULT_OEF,
                                            sender=self.context.agent_public_key,
                                            protocol_id=OEFMessage.protocol_id,
                                            message=OEFSerializer().encode(msg))
            logger.info("[{}]: registering weather station services on OEF.".format(self.context.agent_name))
            self._registered = True

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        pass

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        balance = self.context.ledger_apis.token_balance('fetchai', cast(str, self.context.agent_addresses.get('fetchai')))
        logger.info("[{}]: ending balance on fetchai ledger={}.".format(self.context.agent_name, balance))
        if self._registered:
            strategy = cast(Strategy, self.context.strategy)
            desc = strategy.get_service_description()
            msg = OEFMessage(oef_type=OEFMessage.Type.UNREGISTER_SERVICE,
                             id=UNREGISTER_ID,
                             service_description=desc,
                             service_id=SERVICE_ID)
            self.context.outbox.put_message(to=DEFAULT_OEF,
                                            sender=self.context.agent_public_key,
                                            protocol_id=OEFMessage.protocol_id,
                                            message=OEFSerializer().encode(msg))
            logger.info("[{}]: unregistering weather station services from OEF.".format(self.context.agent_name))
            self._registered = False
