# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2023 Fetch.AI Limited
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

"""This package contains the handlers of the agent."""
from typing import cast

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.carpark_client.strategy import Strategy
from packages.fetchai.skills.generic_buyer.dialogues import (
    FipaDialogue,
    FipaDialogues,
    OefSearchDialogue,
)
from packages.fetchai.skills.generic_buyer.handlers import (
    GenericFipaHandler,
    GenericLedgerApiHandler,
    GenericOefSearchHandler,
    GenericSigningHandler,
)


LedgerApiHandler = GenericLedgerApiHandler
SigningHandler = GenericSigningHandler


class FipaHandler(GenericFipaHandler):
    """This class handles fipa messages."""

    def _handle_propose(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Add received proposals to the current search stack.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        """
        sender = fipa_msg.sender[-5:]
        self.context.logger.info(
            f"received proposal={fipa_msg.proposal.values} from sender={sender}"
        )
        strategy = cast(Strategy, self.context.strategy)
        strategy.received_proposals.append(
            {
                "sender": fipa_msg.sender,
                "message": fipa_msg,
                "decision": FipaMessage.Performative.DECLINE
                if not strategy.is_acceptable_proposal(fipa_msg.proposal)
                or not strategy.is_affordable_proposal(fipa_msg.proposal)
                else None,
            }
        )


class OefSearchHandler(GenericOefSearchHandler):
    """This class handles oef search messages."""

    def _handle_search(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle the search response.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        if len(oef_search_msg.agents) == 0:
            self.context.logger.info(
                f"found no agents in dialogue={oef_search_dialogue}, continue searching."
            )
            return
        strategy = cast(Strategy, self.context.strategy)
        agents = list(map(lambda x: x[-5:], oef_search_msg.agents))
        if strategy.is_stop_searching_on_result:
            self.context.logger.info(f"found agents={agents}, stopping search.")
            strategy.is_searching = False  # stopping search
        else:
            self.context.logger.info(f"found agents={agents}.")
        query = strategy.get_service_query()
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        counterparties = strategy.get_acceptable_counterparties(oef_search_msg.agents)
        for counterparty in counterparties:
            cfp_msg, _ = fipa_dialogues.create(
                counterparty=counterparty,
                performative=FipaMessage.Performative.CFP,
                query=query,
            )
            strategy.sent_proposals.append(counterparty)
            self.context.outbox.put_message(message=cfp_msg)
            self.context.logger.info(f"sending CFP to agent={counterparty[-5:]}")
        self.context.logger.info(f"CFPs sent to {len(counterparties)} agents")
        strategy.waiting_for_proposals = True  # start timer
