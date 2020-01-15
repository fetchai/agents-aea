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

"""This module contains the tests of the ml_messages module."""
import logging

import pytest

from aea.helpers.search.models import DataModel, Attribute, Constraint, Query, ConstraintType, Description
from packages.fetchai.protocols.ml_trade.message import MLTradeMessage
from packages.fetchai.protocols.ml_trade.serialization import MLTradeSerializer

import numpy as np

logger = logging.getLogger(__name__)


def test_perfomrative_str():
    """Test the str value of each performative."""
    assert str(MLTradeMessage.Performative.CFT) == 'cft'
    assert str(MLTradeMessage.Performative.TERMS) == 'terms'
    assert str(MLTradeMessage.Performative.ACCEPT) == 'accept'
    assert str(MLTradeMessage.Performative.DATA) == 'data'


def test_ml_wrong_message_creation():
    """Test the creation of a ml message."""
    with pytest.raises(AssertionError):
        MLTradeMessage(performative=MLTradeMessage.Performative.CFT, query="")


def test_ml_message_creation():
    """Test the creation of a ml message."""
    dm = DataModel("ml_datamodel", [Attribute("dataset_id", str, True)])
    query = Query([Constraint("dataset_id", ConstraintType("==", "fmnist"))], model=dm)
    msg = MLTradeMessage(performative=MLTradeMessage.Performative.CFT, query=query)
    msg_bytes = MLTradeSerializer().encode(msg)
    recovered_msg = MLTradeSerializer().decode(msg_bytes)
    assert recovered_msg == msg

    terms = Description({"batch_size": 5,
                         "price": 10,
                         "seller_tx_fee": 5,
                         "buyer_tx_fee": 2,
                         "currency_id": "FET",
                         "ledger_id": "fetch",
                         "address": "agent1"})

    msg = MLTradeMessage(performative=MLTradeMessage.Performative.TERMS, terms=terms)
    msg_bytes = MLTradeSerializer().encode(msg)
    recovered_msg = MLTradeSerializer().decode(msg_bytes)
    assert recovered_msg == msg

    tx_digest = "This is the transaction digest."
    msg = MLTradeMessage(performative=MLTradeMessage.Performative.ACCEPT, terms=terms, tx_digest=tx_digest)
    msg_bytes = MLTradeSerializer().encode(msg)
    recovered_msg = MLTradeSerializer().decode(msg_bytes)
    assert recovered_msg == msg

    data = np.zeros((5, 2)), np.zeros((5, 2))
    msg = MLTradeMessage(performative=MLTradeMessage.Performative.DATA, terms=terms, data=data)
    msg_bytes = MLTradeSerializer().encode(msg)
    with pytest.raises(ValueError):
        recovered_msg = MLTradeSerializer().decode(msg_bytes)
        assert recovered_msg == msg
    assert np.array_equal(recovered_msg.data, msg.data)
