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

"""This package contains the behaviours of the agent."""

from typing import Any, cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.skills.carpark_client.strategy import Strategy
from packages.fetchai.skills.generic_buyer.behaviours import (
    GenericSearchBehaviour,
    GenericTransactionBehaviour,
)
from packages.fetchai.skills.generic_buyer.dialogues import FipaDialogue, FipaDialogues


SearchBehaviour = GenericSearchBehaviour
TransactionBehaviour = GenericTransactionBehaviour


class ProposalCheckBehaviour(TickerBehaviour):
    """
    Controls the timer to check if proposals have been received.

    :param TickerBehaviour: generic ticker behaviour to be inherited from
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the proposal check behaviour."""
        super().__init__(**kwargs)
        self.counter = 1

    def setup(self) -> None:
        """Set up the behaviour."""

    def act(self) -> None:
        """Act according to the behaviour."""
        strategy = cast(Strategy, self.context.strategy)
        if not strategy.waiting_for_proposals:
            return

        # check if every agent has sent at least one proposal
        if set(strategy.sent_cfps).issubset(
            list(map(lambda x: x["sender"], strategy.received_proposals))
        ):
            self.context.logger.info(
                f"received {len(strategy.received_proposals)} proposals, making decision..."
            )
        elif self.counter > strategy.proposal_check_timeout:
            self.context.logger.info(
                f"waiting for proposals timed out, making decision with {len(strategy.received_proposals)} proposals..."
            )
        else:
            self.counter += 1
            return
        self._handle_all_proposals_received(strategy)

    def teardown(self) -> None:
        """Teardown the behaviour."""

    def _handle_all_proposals_received(self, strategy: Strategy) -> None:
        """Prepare the accept/decline messages"""
        undecided_proposals = list(
            filter(lambda x: x["decision"] is None, strategy.received_proposals)
        )
        if undecided_proposals:
            cheapest_proposal = strategy.get_cheapest_proposal(undecided_proposals)
            for proposal in undecided_proposals:
                cheapest = cheapest_proposal["sender"] == proposal["sender"]
                proposal["decision"] = (
                    FipaMessage.Performative.ACCEPT
                    if cheapest
                    else FipaMessage.Performative.DECLINE
                )
        self._answer_proposals()

    def _answer_proposals(self) -> None:
        """The actual sending of the accept/decline messages."""
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        strategy = cast(Strategy, self.context.strategy)
        for proposal in strategy.received_proposals:
            fipa_dialogue = cast(
                FipaDialogue, fipa_dialogues.get_dialogue(proposal["message"])
            )
            self.context.logger.info(
                f"{proposal['decision']} the proposal from sender={proposal['sender'][-5:]}"
            )
            if proposal["decision"] == FipaMessage.Performative.ACCEPT:
                terms = strategy.terms_from_proposal(
                    proposal["message"].proposal, proposal["sender"]
                )
                fipa_dialogue.terms = terms
            msg = fipa_dialogue.reply(
                performative=proposal["decision"],
                target_message=proposal["message"],
            )
            self.context.outbox.put_message(message=msg)
        strategy.received_proposals = []
        strategy.sent_cfps = []
        strategy.waiting_for_proposals = False
        self.counter = 1
