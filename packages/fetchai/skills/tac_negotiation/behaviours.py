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

from typing import cast

from aea.mail.base import EnvelopeContext
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.tac_negotiation.dialogues import (
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.skills.tac_negotiation.strategy import Strategy
from packages.fetchai.skills.tac_negotiation.transactions import Transactions


DEFAULT_REGISTER_AND_SEARCH_INTERVAL = 5.0


class GoodsRegisterAndSearchBehaviour(TickerBehaviour):
    """This class implements the goods register and search behaviour."""

    def __init__(self, **kwargs):
        """Initialize the search behaviour."""
        search_interval = cast(
            float, kwargs.pop("search_interval", DEFAULT_REGISTER_AND_SEARCH_INTERVAL)
        )
        super().__init__(tick_interval=search_interval, **kwargs)
        self.is_registered = False

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        # the flag "is_game_finished" is set by the 'tac_participation'
        # skill to notify the other skill that the TAC game is finished.
        if self.context.shared_state.get("is_game_finished", False):
            self.context.is_active = False
            return

        if (
            not self.context.decision_maker_handler_context.goal_pursuit_readiness.is_ready
        ):  # pragma: no cover
            return

        if not self.is_registered:  # pragma: no cover
            self._register_agent()
            self._register_service()
            self.is_registered = True
        self._search_services()  # pragma: no cover

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        if self.is_registered:
            self._unregister_service()
            self._unregister_agent()
            self.is_registered = False

    def _register_agent(self) -> None:
        """
        Register the agent's location.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_location_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=description,
        )
        envelope_context = EnvelopeContext(skill_id=self.context.skill_id)
        self.context.outbox.put_message(
            message=oef_search_msg, context=envelope_context
        )
        self.context.logger.info("registering agent on SOEF.")

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
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        self.context.logger.debug(
            "updating service directory as {}.".format(strategy.registering_as)
        )
        description = strategy.get_register_service_description()
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=description,
        )
        envelope_context = EnvelopeContext(skill_id=self.context.skill_id)
        self.context.outbox.put_message(
            message=oef_search_msg, context=envelope_context
        )

    def _unregister_service(self) -> None:
        """
        Unregister service from OEF Service Directory.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        self.context.logger.debug(
            "unregistering from service directory as {}.".format(
                strategy.registering_as
            )
        )
        description = strategy.get_unregister_service_description()
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=description,
        )
        envelope_context = EnvelopeContext(skill_id=self.context.skill_id)
        self.context.outbox.put_message(
            message=oef_search_msg, context=envelope_context
        )

    def _unregister_agent(self) -> None:
        """
        Unregister agent from the SOEF.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_location_description()
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg, _ = oef_search_dialogues.create(
            counterparty=self.context.search_service_address,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            service_description=description,
        )
        envelope_context = EnvelopeContext(skill_id=self.context.skill_id)
        self.context.outbox.put_message(
            message=oef_search_msg, context=envelope_context
        )
        self.context.logger.info("unregistering agent from SOEF.")

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
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        query = strategy.get_location_and_service_query()
        for (is_seller_search, searching_for) in strategy.searching_for_types:
            oef_search_msg, oef_search_dialogue = oef_search_dialogues.create(
                counterparty=self.context.search_service_address,
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                query=query,
            )
            oef_search_dialogue = cast(OefSearchDialogue, oef_search_dialogue)
            oef_search_dialogue.is_seller_search = is_seller_search
            envelope_context = EnvelopeContext(skill_id=self.context.skill_id)
            self.context.outbox.put_message(
                message=oef_search_msg, context=envelope_context
            )
            self.context.logger.info(
                "searching for {}, search_id={}.".format(
                    searching_for, oef_search_msg.dialogue_reference
                )
            )


class TransactionCleanUpBehaviour(TickerBehaviour):
    """This class implements the cleanup of the transactions class."""

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def act(self) -> None:
        """
        Implement the task execution.

        :return: None
        """
        transactions = cast(Transactions, self.context.transactions)
        transactions.update_confirmed_transactions()
        transactions.cleanup_pending_transactions()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass
