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
from typing import Dict, List, Optional, Tuple, Union, cast

from aea.protocols.base import Message
from aea.protocols.oef.models import Description, Query


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

    def __init__(self, dialogue_reference: Tuple[str, str] = None,
                 message_id: Optional[int] = None,
                 target: Optional[int] = None,
                 performative: Optional[Union[str, Performative]] = None,
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
        assert self.check_consistency(), "FIPAMessage initialization inconsistent."

    def check_consistency(self) -> bool:
        """Check that the data is consistent."""
        try:
            assert self.is_set("dialogue_reference")
            dialogue_reference = self.get("dialogue_reference")
            assert type(dialogue_reference) == tuple
            dialogue_reference = cast(Tuple, dialogue_reference)
            assert type(dialogue_reference[0]) == str and type(dialogue_reference[0]) == str
            assert self.is_set("message_id")
            assert type(self.get("message_id")) == int
            assert self.is_set("target")
            assert type(self.get("target")) == int
            performative = FIPAMessage.Performative(self.get("performative"))
            if performative == FIPAMessage.Performative.CFP:
                assert self.is_set("query")
                query = self.get("query")
                assert isinstance(query, Query) or isinstance(query, bytes) or query is None
                assert len(self.body) == 5
            elif performative == FIPAMessage.Performative.PROPOSE:
                assert self.is_set("proposal")
                proposal = self.get("proposal")
                assert type(proposal) == list and all(isinstance(d, Description) or type(d) == bytes for d in proposal)  # type: ignore
                assert len(self.body) == 5
            elif performative == FIPAMessage.Performative.ACCEPT \
                    or performative == FIPAMessage.Performative.MATCH_ACCEPT \
                    or performative == FIPAMessage.Performative.DECLINE:
                assert len(self.body) == 4
            elif performative == FIPAMessage.Performative.ACCEPT_W_INFORM\
                    or performative == FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM\
                    or performative == FIPAMessage.Performative.INFORM:
                assert self.is_set("info")
                json_data = self.get("info")
                assert isinstance(json_data, dict)
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
