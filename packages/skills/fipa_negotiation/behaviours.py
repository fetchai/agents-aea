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
import datetime
import logging
from typing import Optional, cast, TYPE_CHECKING

from aea.skills.base import Behaviour
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Description
from aea.protocols.oef.serialization import OEFSerializer, DEFAULT_OEF

if TYPE_CHECKING:
    from packages.skills.fipa_negotiation.search import Search
    from packages.skills.fipa_negotiation.strategy import Strategy
    from packages.skills.fipa_negotiation.transactions import Transactions
else:
    from fipa_negotiation_skill.search import Search
    from fipa_negotiation_skill.strategy import Strategy
    from fipa_negotiation_skill.transactions import Transactions

DEFAULT_MSG_ID = 1

logger = logging.getLogger(__name__)


class GoodsRegisterAndSearchBehaviour(Behaviour):
    """This class implements the goods register and search behaviour."""

    def __init__(self, **kwargs):
        """Initialize the behaviour."""
        self._services_interval = kwargs.pop('services_interval', 5)  # type: int
        super().__init__(**kwargs)
        self._last_update_time = datetime.datetime.now()  # type: datetime.datetime
        self._last_search_time = datetime.datetime.now()  # type: datetime.datetime
        self._registered_goods_demanded_description = None  # type: Optional[Description]
        self._registered_goods_supplied_description = None  # type: Optional[Description]

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        if self.context.agent_is_ready_to_pursuit_goals:
            if self._is_time_to_update_services():
                self._unregister_service()
                self._register_service()
            if self._is_time_to_search_services():
                self._search_services()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        self._unregister_service()

    def _unregister_service(self) -> None:
        """
        Unregister service from OEF Service Directory.

        :return: None
        """
        if self._registered_goods_demanded_description is not None:
            msg = OEFMessage(oef_type=OEFMessage.Type.UNREGISTER_SERVICE, id=DEFAULT_MSG_ID, service_description=self._registered_goods_demanded_description, service_id="")
            msg_bytes = OEFSerializer().encode(msg)
            self.context.outbox.put_message(to=DEFAULT_OEF, sender=self.context.agent_public_key, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
            self._registered_goods_demanded_description = None
        if self._registered_goods_supplied_description is not None:
            msg = OEFMessage(oef_type=OEFMessage.Type.UNREGISTER_SERVICE, id=DEFAULT_MSG_ID, service_description=self._registered_goods_supplied_description, service_id="")
            msg_bytes = OEFSerializer().encode(msg)
            self.context.outbox.put_message(to=DEFAULT_OEF, sender=self.context.agent_public_key, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
            self._registered_goods_supplied_description = None

    def _register_service(self) -> None:
        """
        Register to the OEF Service Directory.

        In particular, register
            - as a seller, listing the goods supplied, or
            - as a buyer, listing the goods demanded, or
            - as both.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        transactions = cast(Transactions, self.context.transactions)
        if strategy.is_registering_as_seller:
            logger.debug("[{}]: Updating service directory as seller with goods supplied.".format(self.context.agent_name))
            ownership_state_after_locks = transactions.ownership_state_after_locks(self.context.ownership_state, is_seller=True)
            goods_supplied_description = strategy.get_own_service_description(ownership_state_after_locks, is_supply=True)
            self._registered_goods_supplied_description = goods_supplied_description
            msg = OEFMessage(oef_type=OEFMessage.Type.REGISTER_SERVICE, id=DEFAULT_MSG_ID, service_description=goods_supplied_description, service_id="")
            msg_bytes = OEFSerializer().encode(msg)
            self.context.outbox.put_message(to=DEFAULT_OEF, sender=self.context.agent_public_key, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        if strategy.is_registering_as_buyer:
            logger.debug("[{}]: Updating service directory as buyer with goods demanded.".format(self.context.agent_name))
            ownership_state_after_locks = transactions.ownership_state_after_locks(self.context.ownership_state, is_seller=False)
            goods_demanded_description = strategy.get_own_service_description(ownership_state_after_locks, is_supply=False)
            self._registered_goods_demanded_description = goods_demanded_description
            msg = OEFMessage(oef_type=OEFMessage.Type.REGISTER_SERVICE, id=DEFAULT_MSG_ID, service_description=goods_demanded_description, service_id="")
            msg_bytes = OEFSerializer().encode(msg)
            self.context.outbox.put_message(to=DEFAULT_OEF, sender=self.context.agent_public_key, protocol_id=OEFMessage.protocol_id, message=msg_bytes)

    def _search_services(self) -> None:
        """
        Search on OEF Service Directory.

        In particular, search
            - for sellers and their supply, or
            - for buyers and their demand, or
            - for both.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        transactions = cast(Transactions, self.context.transactions)
        if strategy.is_searching_for_sellers:
            ownership_state_after_locks = transactions.ownership_state_after_locks(self.context.ownership_state, is_seller=False)
            query = strategy.get_own_services_query(ownership_state_after_locks, is_searching_for_sellers=True)
            if query is None:
                logger.warning("[{}]: Not searching the OEF for sellers because the agent demands no goods.".format(self.context.agent_name))
                return None
            else:
                logger.debug("[{}]: Searching for sellers which match the demand of the agent.".format(self.context.agent_name))
                search = cast(Search, self.context.search)
                search_id = search.get_next_id(is_searching_for_sellers=True)

                msg = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES, id=search_id, query=query)
                msg_bytes = OEFSerializer().encode(msg)
                self.context.outbox.put_message(to=DEFAULT_OEF, sender=self.context.agent_public_key, protocol_id=OEFMessage.protocol_id, message=msg_bytes)
        if strategy.is_searching_for_buyers:
            ownership_state_after_locks = transactions.ownership_state_after_locks(self.context.ownership_state, is_seller=True)
            query = strategy.get_own_services_query(ownership_state_after_locks, is_searching_for_sellers=False)
            if query is None:
                logger.warning("[{}]: Not searching the OEF for buyers because the agent supplies no goods.".format(self.context.agent_name))
                return None
            else:
                logger.debug("[{}]: Searching for buyers which match the supply of the agent.".format(self.context.agent_name))
                search = cast(Search, self.context.search)
                search_id = search.get_next_id(is_searching_for_sellers=False)

                msg = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES, id=search_id, query=query)
                msg_bytes = OEFSerializer().encode(msg)
                self.context.outbox.put_message(to=DEFAULT_OEF, sender=self.context.agent_public_key, protocol_id=OEFMessage.protocol_id, message=msg_bytes)

    def _is_time_to_update_services(self) -> bool:
        """
        Check if the agent should update the service directory.

        :return: bool indicating the action
        """
        now = datetime.datetime.now()
        diff = now - self._last_update_time
        result = diff.total_seconds() > self._services_interval
        if result:
            self._last_update_time = now
        return result

    def _is_time_to_search_services(self) -> bool:
        """
        Check if the agent should search the service directory.

        :return: bool indicating the action
        """
        now = datetime.datetime.now()
        diff = now - self._last_search_time
        result = diff.total_seconds() > self._services_interval
        if result:
            self._last_search_time = now
        return result
