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

"""This module contains the strategy class."""

from typing import Any, List, cast

from aea.exceptions import enforce

from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy


DEFAULT_PROPOSAL_CHECK_TIMEOUT = 30.0


class Strategy(GenericStrategy):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the strategy of the agent."""
        self.proposal_check_timeout = kwargs.pop(
            "proposal_check_timeout", DEFAULT_PROPOSAL_CHECK_TIMEOUT
        )  # type: int
        super().__init__(**kwargs)
        self._received_proposals = cast(List, [])
        self._sent_proposals = cast(List, [])
        self._waiting_for_proposals = False

    def get_cheapest_proposal(self, agents: List) -> dict:
        """
        Get the cheapest proposal from a given list.

        e.g. agents = [
                {'sender': 'agent_1', 'message': {'price': 10, ...}},
                {'sender': 'agent_2', 'message': {'price': 5, ...}}
            ]
        """
        return sorted(
            agents,
            key=lambda agent: agent["message"].proposal.values["price"],
            reverse=False,
        )[0]

    @property
    def received_proposals(self) -> List:
        """Get all received proposals."""
        return self._received_proposals

    @received_proposals.setter
    def received_proposals(self, proposals: List) -> None:
        """
        Set the received proposals.

        proposals = [
            {
            "sender": FipaMessage.Sender,
            "message": FipaMessage,
            "decision": FipaMessage.Performative.DECLINE or ACCEPT
            },
        ]
        """
        self._received_proposals = proposals

    @property
    def sent_proposals(self) -> List:
        """Get all sent proposals."""
        return self._sent_proposals

    @sent_proposals.setter
    def sent_proposals(self, proposals: List) -> None:
        """
        Set proposals that were sent.

        proposals = [
            'agent_wallet_address_1',
        ]
        """
        self._sent_proposals = proposals

    @property
    def waiting_for_proposals(self) -> bool:
        """Check if the agent started to listen for proposals."""
        return self._waiting_for_proposals

    @waiting_for_proposals.setter
    def waiting_for_proposals(self, waiting_for_proposals: bool) -> None:
        """Set whether the agent should start to listen for proposals"""
        enforce(
            isinstance(waiting_for_proposals, bool),
            "Can only set bool on waiting_for_proposals!",
        )
        self._waiting_for_proposals = waiting_for_proposals
