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
from typing import Optional, Union

from aea.protocols.base import Message
from aea.protocols.oef.models import Description, Query


class FIPAMessage(Message):
    """The FIPA message class."""

    protocol_id = "fipa"

    class Performative(Enum):
        """FIPA performatives."""

        CFP = "cfp"
        PROPOSE = "propose"
        ACCEPT = "accept"
        MATCH_ACCEPT = "match_accept"
        DECLINE = "decline"
        ACCEPT_W_ADDRESS = "accept_w_address"
        MATCH_ACCEPT_W_ADDRESS = "match_accept_w_address"

        def __str__(self):
            """Get string representation."""
            return self.value

    def __init__(self, message_id: Optional[int] = None,
                 dialogue_id: Optional[int] = None,
                 target: Optional[int] = None,
                 performative: Optional[Union[str, Performative]] = None,
                 **kwargs):
        """
        Initialize.

        :param message_id: the message id.
        :param dialogue_id: the dialogue id.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(id=message_id,
                         dialogue_id=dialogue_id,
                         target=target,
                         performative=FIPAMessage.Performative(performative),
                         **kwargs)
        assert self.check_consistency(), "FIPAMessage initialization inconsistent."

    def check_consistency(self) -> bool:
        """Check that the data is consistent."""
        try:
            assert self.is_set("target")
            performative = FIPAMessage.Performative(self.get("performative"))
            if performative == FIPAMessage.Performative.CFP:
                query = self.get("query")
                assert isinstance(query, Query) or isinstance(query, bytes) or query is None
            elif performative == FIPAMessage.Performative.PROPOSE:
                proposal = self.get("proposal")
                assert type(proposal) == list and all(isinstance(d, Description) or type(d) == bytes for d in proposal)  # type: ignore
            elif performative == FIPAMessage.Performative.ACCEPT \
                    or performative == FIPAMessage.Performative.MATCH_ACCEPT \
                    or performative == FIPAMessage.Performative.DECLINE\
                    or performative == FIPAMessage.Performative.ACCEPT_W_ADDRESS\
                    or performative == FIPAMessage.Performative.MATCH_ACCEPT_W_ADDRESS:
                pass  # pragma: no cover
            else:
                raise ValueError("Performative not recognized.")

        except (AssertionError, ValueError, KeyError):
            return False

        return True
