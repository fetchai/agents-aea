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
"""This module contains the tests of the handler classes of the ml_data_provider skill."""

import logging
import sys
import uuid
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from aea.helpers.search.models import Description
from aea.helpers.transaction.base import TransactionDigest, TransactionReceipt
from aea.protocols.dialogue.base import DialogueMessage, Dialogues
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.ml_trade.message import MlTradeMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.ml_data_provider.dialogues import (
    LedgerApiDialogue,
    LedgerApiDialogues,
    MlTradeDialogue,
    MlTradeDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.ml_data_provider.handlers import (
    LedgerApiHandler,
    MlTradeHandler,
    OefSearchHandler,
)
from packages.fetchai.skills.ml_data_provider.strategy import Strategy

from tests.conftest import ROOT_DIR


@pytest.mark.skipif(
    sys.version_info >= (3, 9),
    reason="These tests use tensorflow which, at the time of writing, does not yet support python version 3.9.",
)
class TestMlTradeHandler(BaseSkillTestCase):
    """Test ml handler of ml_data_provider."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_data_provider")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.ml_handler = cast(
            MlTradeHandler, cls._skill.skill_context.handlers.ml_trade
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.ml_dialogues = cast(
            MlTradeDialogues, cls._skill.skill_context.ml_trade_dialogues
        )
        cls.logger = cls._skill.skill_context.logger

        cls.batch_size = 32
        cls.price_per_data_batch = 10
        cls.seller_tx_fee = 0
        cls.buyer_tx_fee = 0
        cls.currency_id = "FET"
        cls.ledger_id = "FET"
        cls.service_id = "data_service"

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
            DialogueMessage(MlTradeMessage.Performative.TERMS, {"terms": cls.terms}),
            DialogueMessage(
                MlTradeMessage.Performative.ACCEPT,
                {"terms": cls.terms, "tx_digest": "some_tx_digest"},
            ),
        )

    def test_setup(self):
        """Test the setup method of the ml handler."""
        assert self.ml_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the ml handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=MlTradeMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=MlTradeMessage.Performative.ACCEPT,
            terms=self.terms,
            tx_digest="some_tx_digest",
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ml_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid ml_trade message={incoming_message}, unidentified dialogue.",
        )
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=DefaultMessage,
            performative=DefaultMessage.Performative.ERROR,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"ml_trade_message": incoming_message.encode()},
        )
        assert has_attributes, error_str

    def test_handle_cfp_is_matching_supply(self):
        """Test the _handle_cfp method of the ml handler where is_matching_supply is True."""
        # setup
        incoming_message = self.build_incoming_message(
            message_type=MlTradeMessage,
            performative=MlTradeMessage.Performative.CFP,
            dialogue_reference=Dialogues.new_self_initiated_dialogue_reference(),
            query="some_query",
        )

        # operation
        with patch.object(self.strategy, "is_matching_supply", return_value=True):
            with patch.object(self.strategy, "generate_terms", return_value=self.terms):
                with patch.object(self.logger, "log") as mock_logger:
                    self.ml_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"got a Call for Terms from {COUNTERPARTY_AGENT_ADDRESS[-5:]}.",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            f"sending to the address={COUNTERPARTY_AGENT_ADDRESS[-5:]} a Terms message: {self.terms.values}",
        )

        self.assert_quantity_in_outbox(1)

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=MlTradeMessage,
            performative=MlTradeMessage.Performative.TERMS,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            target=incoming_message.message_id,
            terms=self.terms,
        )
        assert has_attributes, error_str

    def test_handle_cfp_not_is_matching_supply(self):
        """Test the _handle_cfp method of the ml handler where is_matching_supply is False."""
        # setup
        incoming_message = self.build_incoming_message(
            message_type=MlTradeMessage,
            performative=MlTradeMessage.Performative.CFP,
            dialogue_reference=Dialogues.new_self_initiated_dialogue_reference(),
            query="some_query",
        )

        # operation
        with patch.object(self.strategy, "is_matching_supply", return_value=False):
            with patch.object(self.logger, "log") as mock_logger:
                self.ml_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO,
            f"got a Call for Terms from {COUNTERPARTY_AGENT_ADDRESS[-5:]}.",
        )
        mock_logger.assert_any_call(logging.INFO, "query does not match supply.")

    def test_handle_accept_i(self):
        """Test the _handle_accept method of the ml handler."""
        # setup
        mocked_tx_digest = "some_tx_digest"
        terms = self.strategy.generate_terms()
        expected_data = self.strategy.sample_data(terms.values["batch_size"])

        ml_dialogue = cast(
            MlTradeDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ml_dialogues, messages=self.list_of_messages[:2],
            ),
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ml_dialogue,
            performative=MlTradeMessage.Performative.ACCEPT,
            terms=terms,
            tx_digest=mocked_tx_digest,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ml_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"got an Accept from {COUNTERPARTY_AGENT_ADDRESS[-5:]}: {terms.values}",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            f"sending to address={COUNTERPARTY_AGENT_ADDRESS[-5:]} a Data message: shape={expected_data[0].shape}",
        )

        self.assert_quantity_in_outbox(1)
        message = cast(MlTradeMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=MlTradeMessage,
            performative=MlTradeMessage.Performative.DATA,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            terms=terms,
        )
        assert has_attributes, error_str
        assert type(message.payload) == bytes

    def test_handle_accept_ii(self):
        """Test the _handle_accept method of the ml handler where terms is NOT valid."""
        # setup
        mocked_tx_digest = "some_tx_digest"

        ml_dialogue = cast(
            MlTradeDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ml_dialogues, messages=self.list_of_messages[:2],
            ),
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ml_dialogue,
            performative=MlTradeMessage.Performative.ACCEPT,
            terms=self.terms,
            tx_digest=mocked_tx_digest,
        )

        # operation
        with patch.object(self.strategy, "is_valid_terms", return_value=False):
            with patch.object(self.logger, "log") as mock_logger:
                self.ml_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"got an Accept from {COUNTERPARTY_AGENT_ADDRESS[-5:]}: {self.terms.values}",
        )
        mock_logger.assert_any_call(logging.INFO, "terms are not valid.")

        self.assert_quantity_in_outbox(0)

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the ml handler."""
        # setup
        ml_dialogue = self.prepare_skill_dialogue(
            dialogues=self.ml_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ml_dialogue,
            performative=MlTradeMessage.Performative.TERMS,
            terms=self.terms,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ml_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle ml_trade message of performative={incoming_message.performative} in dialogue={ml_dialogue}.",
        )

    def test_teardown(self):
        """Test the teardown method of the ml handler."""
        assert self.ml_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


@pytest.mark.skipif(
    sys.version_info >= (3, 9),
    reason="These tests use tensorflow which, at the time of writing, does not yet support python version 3.9.",
)
class TestLedgerApiHandler(BaseSkillTestCase):
    """Test ledger_api handler of ml_data_provider."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_data_provider")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.ledger_api_handler = cast(
            LedgerApiHandler, cls._skill.skill_context.handlers.ledger_api
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.ml_dialogues = cast(
            MlTradeDialogues, cls._skill.skill_context.ml_trade_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.logger = cls._skill.skill_context.logger

        cls.ledger_id = "FET"
        cls.transaction_digest = TransactionDigest("some_ledger_id", "some_body")
        cls.transaction_receipt = TransactionReceipt(
            "some_ledger_id", {"some_key": "some_value"}, {"some_key": "some_value"}
        )
        cls.list_of_ledger_api_messages = (
            DialogueMessage(
                LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                {"transaction_digest": cls.transaction_digest},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                {"transaction_receipt": cls.transaction_receipt},
            ),
        )

    def test_setup(self):
        """Test the setup method of the ledger_api handler."""
        assert self.ledger_api_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the ledger_api handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=LedgerApiMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id="some_ledger_id",
            address="some_address",
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid ledger_api message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_balance(self):
        """Test the _handle_balance method of the ledger_api handler."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=(
                    DialogueMessage(
                        LedgerApiMessage.Performative.GET_BALANCE,
                        {"ledger_id": "some_ledger_id", "address": "some_address"},
                    ),
                ),
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.BALANCE,
                ledger_id=self.ledger_id,
                balance=10,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"starting balance on {self.ledger_id} ledger={incoming_message.balance}.",
        )

    def test_handle_error(self):
        """Test the _handle_error method of the ledger_api handler."""
        # setup
        ledger_api_dialogue = self.prepare_skill_dialogue(
            dialogues=self.ledger_api_dialogues,
            messages=self.list_of_ledger_api_messages[:1],
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.ERROR,
                code=1,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received ledger_api error message={incoming_message} in dialogue={ledger_api_dialogue}.",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the ledger_api handler."""
        # setup
        invalid_performative = LedgerApiMessage.Performative.GET_BALANCE
        incoming_message = self.build_incoming_message(
            message_type=LedgerApiMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            ledger_id="some_ledger_id",
            address="some_address",
            to=str(self.skill.skill_context.skill_id),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle ledger_api message of performative={invalid_performative} in dialogue={self.ledger_api_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the ledger_api handler."""
        assert self.ledger_api_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


@pytest.mark.skipif(
    sys.version_info >= (3, 9),
    reason="These tests use tensorflow which, at the time of writing, does not yet support python version 3.9.",
)
class TestOefSearchHandler(BaseSkillTestCase):
    """Test oef search handler of ml_data_provider."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_data_provider")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.oef_search_handler = cast(
            OefSearchHandler, cls._skill.skill_context.handlers.oef_search
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.oef_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )
        cls.list_of_messages = (
            DialogueMessage(
                OefSearchMessage.Performative.SEARCH_SERVICES, {"query": "some_query"}
            ),
        )

    def test_setup(self):
        """Test the setup method of the oef_search handler."""
        assert self.oef_search_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the oef_search handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid oef_search message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_error(self):
        """Test the _handle_error method of the oef_search handler."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.OEF_ERROR,
            oef_error_operation=OefSearchMessage.OefErrorOperation.SEARCH_SERVICES,
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search error message={incoming_message} in dialogue={oef_dialogue}.",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the oef_search handler."""
        # setup
        invalid_performative = OefSearchMessage.Performative.UNREGISTER_SERVICE
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            service_description="some_service_description",
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle oef_search message of performative={invalid_performative} in dialogue={self.oef_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the oef_search handler."""
        assert self.oef_search_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
