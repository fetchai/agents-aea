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
import numpy as np

from aea.protocols.base import Message
from aea.protocols.oef.models import Description, Query


class MLTradeMessage(Message):
    """The ML trade message class."""

    protocol_id = "ml_trade"

    class Performative(Enum):
        """ML trade performatives."""

        CFT = 'cft'
        TERMS = 'terms'
        ACCEPT = 'accept'
        DATA = 'data'

        def __str__(self):
            """Get string representation."""
            return self.value

    def __init__(self, performative: Optional[Union[str, Performative]] = None, **kwargs):
        """
        Initialize.

        :param type: the type.
        """
        super().__init__(performative=MLTradeMessage.Performative(performative), **kwargs)
        assert self.check_consistency(), "MLTradeMessage initialization inconsistent."

    def check_consistency(self) -> bool:
        """Check that the data is consistent."""
        try:
            assert self.is_set("performative")
            performative = MLTradeMessage.Performative(self.get("performative"))
            if performative == MLTradeMessage.Performative.CFT:
                assert self.is_set("query")
                query = self.get("query")
                assert isinstance(query, Query)
                assert len(self.body) == 2
            elif performative == MLTradeMessage.Performative.TERMS:
                assert self.is_set("terms")
                terms = self.get("terms")
                assert isinstance(terms, Description)
                assert len(self.body) == 2
            elif performative == MLTradeMessage.Performative.ACCEPT:
                assert self.is_set("terms")
                terms = self.get("terms")
                assert isinstance(terms, Description)
                assert self.is_set("tx_digest")
                tx_digest = self.get("tx_digest")
                assert isinstance(tx_digest, str)
                assert len(self.body) == 3
            elif performative == MLTradeMessage.Performative.DATA:
                assert self.is_set("terms")
                terms = self.get("terms")
                assert isinstance(terms, Description)
                assert self.is_set("data")
                # expect data = (X, y)
                data = self.get("data")
                assert isinstance(data, tuple)
                assert len(data) == 2
                assert isinstance(data[0], np.ndarray)
                assert isinstance(data[1], np.ndarray)
                assert data[0].shape[0] == data[1].shape[0]
                assert len(self.body) == 3
            else:
                raise ValueError("Performative not recognized.")

        except (AssertionError, ValueError, KeyError):  # pragma: no cover
            return False

        return True
