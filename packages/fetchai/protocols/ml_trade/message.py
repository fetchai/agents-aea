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
from typing import Tuple, cast

import numpy as np

from aea.configurations.base import PublicId
from aea.helpers.search.models import Description, Query
from aea.protocols.base import Message


class MLTradeMessage(Message):
    """The ML trade message class."""

    protocol_id = PublicId("fetchai", "ml_trade", "0.1.0")

    class Performative(Enum):
        """ML trade performatives."""

        CFT = "cft"
        TERMS = "terms"
        ACCEPT = "accept"
        DATA = "data"

        def __str__(self):
            """Get string representation."""
            return self.value

    def __init__(self, performative: Performative, **kwargs):
        """
        Initialize.

        :param type: the type.
        """
        super().__init__(performative=performative, **kwargs)
        assert self._is_consistent(), "MLTradeMessage initialization inconsistent."

    @property
    def performative(self) -> Performative:  # noqa: F821
        """Get the performative of the message."""
        assert self.is_set("performative"), "performative is not set."
        return MLTradeMessage.Performative(self.get("performative"))

    @property
    def query(self) -> Query:
        """Get the query of the message."""
        assert self.is_set("query"), "query is not set."
        return cast(Query, self.get("query"))

    @property
    def terms(self) -> Description:
        """Get the terms of the message."""
        assert self.is_set("terms"), "Terms are not set."
        return cast(Description, self.get("terms"))

    @property
    def tx_digest(self) -> str:
        """Get the transaction digest from the message."""
        assert self.is_set("tx_digest"), "tx_digest is not set."
        return cast(str, self.get("tx_digest"))

    @property
    def data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get the data from the message."""
        assert self.is_set("data"), "Data is not set."
        return cast(Tuple[np.ndarray, np.ndarray], self.get("data"))

    def _is_consistent(self) -> bool:
        """Check that the data is consistent."""
        try:
            assert isinstance(
                self.performative, MLTradeMessage.Performative
            ), "Performative is invalid type."
            if self.performative == MLTradeMessage.Performative.CFT:
                assert isinstance(self.query, Query)
                assert len(self.body) == 2
            elif self.performative == MLTradeMessage.Performative.TERMS:
                assert isinstance(self.terms, Description)
                assert len(self.body) == 2
            elif self.performative == MLTradeMessage.Performative.ACCEPT:
                assert isinstance(self.terms, Description)
                assert isinstance(self.tx_digest, str)
                assert len(self.body) == 3
            elif self.performative == MLTradeMessage.Performative.DATA:
                assert isinstance(self.terms, Description)
                assert isinstance(self.data, tuple)
                assert len(self.data) == 2
                assert isinstance(self.data[0], np.ndarray)
                assert isinstance(self.data[1], np.ndarray)
                assert self.data[0].shape[0] == self.data[1].shape[0]
                assert len(self.body) == 3
            else:
                raise ValueError("Performative not recognized.")

        except (AssertionError, ValueError, KeyError):
            return False

        return True
