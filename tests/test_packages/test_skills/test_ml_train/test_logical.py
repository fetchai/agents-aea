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
"""This module contains tests for the logical behaviour of the tac ml_train skill."""

import logging
import pickle  # nosec
import uuid
from pathlib import Path
from typing import Tuple, cast
from unittest.mock import patch

import numpy as np

from aea.helpers.search.models import Description
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.ml_trade.message import MlTradeMessage
from packages.fetchai.skills.ml_train.dialogues import MlTradeDialogues
from packages.fetchai.skills.ml_train.handlers import MlTradeHandler

from tests.conftest import ROOT_DIR


class TestLogical(BaseSkillTestCase):
    """Logical Tests for ml_train."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_train")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.batch_size = 32
        cls.price_per_data_batch = 10
        cls.seller_tx_fee = 0
        cls.buyer_tx_fee = 0
        cls.currency_id = "FET"
        cls.ledger_id = "FET"
        cls.service_id = "data_service"

        cls.ml_trade_handler = cast(
            MlTradeHandler, cls._skill.skill_context.handlers.ml_trade
        )
        cls.logger = cls._skill.skill_context.logger

        cls.ml_dialogues = cast(
            MlTradeDialogues, cls._skill.skill_context.ml_trade_dialogues
        )

        cls.terms = Description(
            {
                "batch_size": cls.batch_size,
                "price": cls.price_per_data_batch,
                "seller_tx_fee": cls.seller_tx_fee,
                "buyer_tx_fee": cls.buyer_tx_fee,
                "currency_id": cls.currency_id,
                "ledger_id": cls.ledger_id,
                "address": cls._skill.skill_context.agent_address,
                "service_id": cls.service_id,
                "nonce": uuid.uuid4().hex,
            }
        )

        cls.list_of_messages = (
            DialogueMessage(MlTradeMessage.Performative.CFP, {"query": "some_query"}),
            DialogueMessage(
                MlTradeMessage.Performative.TERMS, {"terms": cls.terms}
            ),
            DialogueMessage(
                MlTradeMessage.Performative.ACCEPT, {"terms": cls.terms, "tx_digest": "some_tx_digest"}
            ),
        )

    def produce_data(self) -> Tuple:
        from tensorflow import keras  # pylint: disable=import-outside-toplevel

        ((train_x, train_y), _) = keras.datasets.fashion_mnist.load_data()

        idx = np.arange(train_x.shape[0])
        mask = np.zeros_like(idx, dtype=bool)

        selected = np.random.choice(idx, self.batch_size, replace=False)
        mask[selected] = True

        x_sample = train_x[mask]
        y_sample = train_y[mask]
        return x_sample, y_sample

    def test_ml(self):
        """Test ml."""
        # setup
        payload = pickle.dumps(self.produce_data())

        ml_dialogue = self.prepare_skill_dialogue(
            dialogues=self.ml_dialogues, messages=self.list_of_messages[:3],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ml_dialogue,
            performative=MlTradeMessage.Performative.DATA,
            terms=self.terms,
            payload=payload,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ml_trade_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"got an Accept from {COUNTERPARTY_AGENT_ADDRESS[-5:]}: {self.terms.values}",
        )
