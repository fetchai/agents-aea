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
import pickle  # nosec
from unittest import mock

import numpy as np

from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
    Query,
)

from packages.fetchai.protocols.ml_trade.message import MlTradeMessage

logger = logging.getLogger(__name__)


def test_perfomrative_str():
    """Test the str value of each performative."""
    assert str(MlTradeMessage.Performative.CFP) == "cfp"
    assert str(MlTradeMessage.Performative.TERMS) == "terms"
    assert str(MlTradeMessage.Performative.ACCEPT) == "accept"
    assert str(MlTradeMessage.Performative.DATA) == "data"


def test_ml_wrong_message_creation():
    """Test the creation of a ml message."""
    msg = MlTradeMessage(performative=MlTradeMessage.Performative.CFP, query="")
    assert not msg._is_consistent()


def test_ml_messge_consistency():
    """Test the consistency of the message."""
    dm = DataModel("ml_datamodel", [Attribute("dataset_id", str, True)])
    query = Query([Constraint("dataset_id", ConstraintType("==", "fmnist"))], model=dm)
    msg = MlTradeMessage(performative=MlTradeMessage.Performative.CFP, query=query)
    with mock.patch.object(MlTradeMessage.Performative, "__eq__", return_value=False):
        assert not msg._is_consistent()


def test_ml_message_creation():
    """Test the creation of a ml message."""
    dm = DataModel("ml_datamodel", [Attribute("dataset_id", str, True)])
    query = Query([Constraint("dataset_id", ConstraintType("==", "fmnist"))], model=dm)
    msg = MlTradeMessage(performative=MlTradeMessage.Performative.CFP, query=query)
    msg_bytes = MlTradeMessage.serializer.encode(msg)
    recovered_msg = MlTradeMessage.serializer.decode(msg_bytes)
    assert recovered_msg == msg

    terms = Description(
        {
            "batch_size": 5,
            "price": 10,
            "seller_tx_fee": 5,
            "buyer_tx_fee": 2,
            "currency_id": "FET",
            "ledger_id": "fetch",
            "address": "agent1",
        }
    )

    msg = MlTradeMessage(performative=MlTradeMessage.Performative.TERMS, terms=terms)
    msg_bytes = MlTradeMessage.serializer.encode(msg)
    recovered_msg = MlTradeMessage.serializer.decode(msg_bytes)
    assert recovered_msg == msg

    tx_digest = "This is the transaction digest."
    msg = MlTradeMessage(
        performative=MlTradeMessage.Performative.ACCEPT,
        terms=terms,
        tx_digest=tx_digest,
    )
    msg_bytes = MlTradeMessage.serializer.encode(msg)
    recovered_msg = MlTradeMessage.serializer.decode(msg_bytes)
    assert recovered_msg == msg

    data = np.zeros((5, 2)), np.zeros((5, 2))
    payload = pickle.dumps(data)  # nosec
    msg = MlTradeMessage(
        performative=MlTradeMessage.Performative.DATA, terms=terms, payload=payload
    )
    msg_bytes = MlTradeMessage.serializer.encode(msg)
    recovered_msg = MlTradeMessage.serializer.decode(msg_bytes)
    assert recovered_msg == msg
    recovered_data = pickle.loads(recovered_msg.payload)  # nosec
    assert np.array_equal(recovered_data, data)
