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

"""This package contains the behaviours for the oracle aggregation skill."""

from time import time
from typing import Any, cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.aggregation.message import AggregationMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.simple_aggregation.dialogues import (
    AggregationDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.simple_aggregation.strategy import AggregationStrategy


DEFAULT_SEARCH_INTERVAL = 30.0
DEFAULT_AGGREGATION_INTERVAL = 5.0
DEFAULT_SOURCE = ""
DEFAULT_SIGNATURE = ""


class SearchBehaviour(TickerBehaviour):
    """This class implements the service registration behaviour for the simple aggregation skill"""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the search behaviour."""
        search_interval = cast(
            float, kwargs.pop("search_interval", DEFAULT_SEARCH_INTERVAL)
        )
        super().__init__(tick_interval=search_interval, **kwargs)

    def setup(self) -> None:
        """Implement the setup for the behaviour."""
        self._register_agent()
        self._register_service_personality_classification()

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        strategy = cast(AggregationStrategy, self.context.strategy)
        query = strategy.get_location_and_service_query()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=query,
        )
        self.context.outbox.put_message(message=oef_search_msg)

    def _register_agent(self) -> None:
        """
        Register the agent's location.

        :return: None
        """
        strategy = cast(AggregationStrategy, self.context.strategy)
        description = strategy.get_location_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("registering agent on SOEF.")

    def _register_service_personality_classification(self) -> None:
        """
        Register the agent's service, personality and classification.

        :return: None
        """
        strategy = cast(AggregationStrategy, self.context.strategy)
        descriptions = [
            strategy.get_register_service_description(),
            strategy.get_register_personality_description(),
            strategy.get_register_classification_description(),
        ]
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        for description in descriptions:
            oef_search_msg, _ = oef_search_dialogues.create(
                counterparty=self.context.search_service_address,
                performative=OefSearchMessage.Performative.REGISTER_SERVICE,
                service_description=description,
            )
            self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("registering service on SOEF.")

    def _unregister_service(self) -> None:
        """
        Unregister service from the SOEF.

        :return: None
        """
        strategy = cast(AggregationStrategy, self.context.strategy)
        description = strategy.get_unregister_service_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("unregistering service from SOEF.")

    def _unregister_agent(self) -> None:
        """
        Unregister agent from the SOEF.

        :return: None
        """
        strategy = cast(AggregationStrategy, self.context.strategy)
        description = strategy.get_location_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=description,
        )
        self.context.outbox.put_message(message=oef_search_msg)
        self.context.logger.info("unregistering agent from SOEF.")


class AggregationBehaviour(TickerBehaviour):
    """This class implements an aggregation behaviour."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the aggregation behaviour."""
        aggregation_interval = cast(
            float, kwargs.pop("aggregation_interval", DEFAULT_AGGREGATION_INTERVAL)
        )
        super().__init__(tick_interval=aggregation_interval, **kwargs)

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        strategy = cast(AggregationStrategy, self.context.strategy)
        obs = self.context.shared_state.get("observation", {})
        quantity = obs.get(strategy.quantity_name, {})
        value = quantity.get("value", None)
        if value:
            strategy.make_observation(
                value, str(time()), source=DEFAULT_SOURCE, signature=DEFAULT_SIGNATURE,
            )
        self.broadcast_observation()

    def broadcast_observation(self) -> None:
        """
        Send latest observation to current list of peers

        :return: None
        """
        strategy = cast(AggregationStrategy, self.context.strategy)
        obs = strategy.observation
        if obs is None:
            self.context.logger.info("No observation to send")
            return
        aggregation_dialogues = cast(
            AggregationDialogues, self.context.aggregation_dialogues
        )
        for counterparty in strategy.peers:
            obs_msg, _ = aggregation_dialogues.create(
                counterparty=counterparty,
                performative=AggregationMessage.Performative.OBSERVATION,
                **obs,
            )
            self.context.outbox.put_message(message=obs_msg)
            self.context.logger.info(
                "sending observation to peer={}".format(counterparty[-5:])
            )
