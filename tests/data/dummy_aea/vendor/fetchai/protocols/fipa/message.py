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

"""This module contains the FIPA message definition."""
from enum import Enum
from typing import Any, Dict, List, Tuple, Union, cast

from aea.helpers.search.models import Description, Query
from aea.protocols.base import Message


class FIPAMessage(Message):
    """The FIPA message class."""

    protocol_id = "fipa"

    STARTING_MESSAGE_ID = 1
    STARTING_TARGET = 0

    class Performative(Enum):
        """FIPA performatives."""

        CFP = "cfp"
        PROPOSE = "propose"
        ACCEPT = "accept"
        MATCH_ACCEPT = "match_accept"
        DECLINE = "decline"
        INFORM = "inform"
        ACCEPT_W_INFORM = "accept_w_inform"
        MATCH_ACCEPT_W_INFORM = "match_accept_w_inform"

        def __str__(self):
            """Get string representation."""
            return self.value

    def __init__(self, dialogue_reference: Tuple[str, str],
                 message_id: int,
                 target: int,
                 performative: Performative,
                 **kwargs):
        """
        Initialize.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(message_id=message_id,
                         dialogue_reference=dialogue_reference,
                         target=target,
                         performative=FIPAMessage.Performative(performative),
                         **kwargs)
        assert self._check_consistency(), "FIPAMessage initialization inconsistent."

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        assert self.is_set("dialogue_reference"), " dialogue_reference is not set"
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        assert self.is_set("message_id"), "message_id is not set"
        return cast(int, self.get("message_id"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

    @property
    def performative(self) -> Performative:  # noqa: F821
        """Get the performative of the message."""
        return FIPAMessage.Performative(self.get("performative"))

    @property
    def query(self) -> Union[Query, bytes, None]:
        """Get the query of the message."""
        assert self.is_set("query"), "query is not set."
        return cast(Union[Query, bytes, None], self.get("query"))

    @property
    def proposal(self) -> List[Description]:
        """Get the proposal list from the message."""
        assert self.is_set("proposal"), "proposal is not set."
        return cast(List[Description], self.get("proposal"))

    @property
    def info(self) -> Dict[str, Any]:
        """Get hte info from the message."""
        assert self.is_set("info"), "info is not set."
        return cast(Dict[str, Any], self.get("info"))

    def _check_consistency(self) -> bool:
        """Check that the data is consistent."""
        try:
            assert isinstance(self.performative, FIPAMessage.Performative)
            assert isinstance(self.dialogue_reference, tuple)
            assert isinstance(self.dialogue_reference[0], str) and isinstance(self.dialogue_reference[1], str)
            assert isinstance(self.message_id, int)
            assert isinstance(self.target, int)
            if self.performative == FIPAMessage.Performative.CFP:
                assert isinstance(self.query, Query) or isinstance(self.query, bytes) or self.query is None
                assert len(self.body) == 5
            elif self.performative == FIPAMessage.Performative.PROPOSE:
                assert isinstance(self.proposal, list) and all(isinstance(d, Description) for d in self.proposal)
                assert len(self.body) == 5
            elif self.performative == FIPAMessage.Performative.ACCEPT \
                    or self.performative == FIPAMessage.Performative.MATCH_ACCEPT \
                    or self.performative == FIPAMessage.Performative.DECLINE:
                assert len(self.body) == 4
            elif self.performative == FIPAMessage.Performative.ACCEPT_W_INFORM\
                    or self.performative == FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM\
                    or self.performative == FIPAMessage.Performative.INFORM:
                assert isinstance(self.info, dict)
                assert len(self.body) == 5
            else:
                raise ValueError("Performative not recognized.")

        except (AssertionError, ValueError, KeyError):
            return False

        return True


VALID_PREVIOUS_PERFORMATIVES = {
    FIPAMessage.Performative.CFP: [None],
    FIPAMessage.Performative.PROPOSE: [FIPAMessage.Performative.CFP],
    FIPAMessage.Performative.ACCEPT: [FIPAMessage.Performative.PROPOSE],
    FIPAMessage.Performative.ACCEPT_W_INFORM: [FIPAMessage.Performative.PROPOSE],
    FIPAMessage.Performative.MATCH_ACCEPT: [FIPAMessage.Performative.ACCEPT, FIPAMessage.Performative.ACCEPT_W_INFORM],
    FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM: [FIPAMessage.Performative.ACCEPT, FIPAMessage.Performative.ACCEPT_W_INFORM],
    FIPAMessage.Performative.INFORM: [FIPAMessage.Performative.MATCH_ACCEPT, FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM, FIPAMessage.Performative.INFORM],
    FIPAMessage.Performative.DECLINE: [FIPAMessage.Performative.CFP, FIPAMessage.Performative.PROPOSE, FIPAMessage.Performative.ACCEPT, FIPAMessage.Performative.ACCEPT_W_INFORM]
}  # type: Dict[FIPAMessage.Performative, List[Union[None, FIPAMessage.Performative]]]
