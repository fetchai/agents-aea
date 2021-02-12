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
"""This module contains the tests of the handler classes of the simple_data_request skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.helpers.transaction.base import Terms
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.contract_api.custom_types import (
    Kwargs as ContractApiKwargs,
)
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.ledger_api.custom_types import (
    SignedTransaction,
    TransactionDigest,
    TransactionReceipt,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.prometheus.message import PrometheusMessage
from packages.fetchai.protocols.signing.custom_types import RawTransaction
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.simple_oracle.behaviours import SimpleOracleBehaviour
from packages.fetchai.skills.simple_oracle.dialogues import (
    ContractApiDialogues,
    LedgerApiDialogues,
    SigningDialogues,
)
from packages.fetchai.skills.simple_oracle.handlers import LedgerApiHandler
from packages.fetchai.skills.simple_oracle.strategy import Strategy

from tests.conftest import ROOT_DIR


LEDGER_ID = "ethereum"
DEFAULT_TX = {"some_tx_key": "some_tx_value"}
DEFAULT_TERMS = [
    LEDGER_ID,
    "sender_address",
    "counterparty_address",
    {},
    {},
    "some_nonce",
]


class TestLedgerApiHandler(BaseSkillTestCase):
    """Test ledger_api handler of simple_oracle skill."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "simple_oracle")

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup(**kwargs)
        cls.ledger_api_handler = cast(
            LedgerApiHandler, cls._skill.skill_context.handlers.ledger_api
        )
        cls.logger = cls._skill.skill_context.logger
        cls.simple_oracle_behaviour = cast(
            SimpleOracleBehaviour,
            cls._skill.skill_context.behaviours.simple_oracle_behaviour,
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.contract_api_dialogues = cast(
            ContractApiDialogues, cls._skill.skill_context.contract_api_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )

        cls.list_of_ledger_api_messages = (
            DialogueMessage(
                LedgerApiMessage.Performative.GET_BALANCE,
                {"ledger_id": LEDGER_ID, "address": "some_eth_address"},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
                {"signed_transaction": SignedTransaction(LEDGER_ID, DEFAULT_TX)},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                {"transaction_digest": TransactionDigest(LEDGER_ID, "some_digest")},
            ),
        )
        cls.list_of_contract_api_messages = (
            DialogueMessage(
                ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
                {
                    "ledger_id": LEDGER_ID,
                    "contract_id": "some_contract_id",
                    "callable": "some_callable",
                    "kwargs": ContractApiKwargs({"some_key": "some_value"}),
                },
            ),
        )
        cls.list_of_signing_messages = (
            DialogueMessage(
                SigningMessage.Performative.SIGN_TRANSACTION,
                {
                    "terms": Terms(*DEFAULT_TERMS),
                    "raw_transaction": RawTransaction(LEDGER_ID, DEFAULT_TX),
                },
            ),
        )

    def test_setup(self):
        """Test the setup method of the ledger_api handler."""
        assert self.ledger_api_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle__handle_unidentified_dialogue(self):
        """Test handling an unidentified dialogoue"""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=LedgerApiMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id=LEDGER_ID,
            address="some_eth_address",
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid ledger_api message={incoming_message}, unidentified dialogue.",
        )

        self.assert_quantity_in_outbox(0)

    def test__handle_balance(self):
        """Test handling a balance"""
        # setup
        balance = 0
        dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[:1]
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue,
            performative=LedgerApiMessage.Performative.BALANCE,
            ledger_id=LEDGER_ID,
            balance=balance,
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"Balance on {LEDGER_ID} ledger={balance}.",
        )

        self.assert_quantity_in_outbox(1)

    def test__handle_transaction_digest(self):
        """Test handling a transaction digest"""
        # setup
        dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[1:2]
        )
        digest = "some_digest"
        transaction_digest = TransactionDigest(LEDGER_ID, digest)
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue,
            performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
            transaction_digest=transaction_digest,
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction was successfully submitted. Transaction digest=TransactionDigest: ledger_id={LEDGER_ID}, body={digest}",
        )

        self.assert_quantity_in_outbox(1)

    def test__handle_transaction_receipt_failed(self):
        """Test handling a transaction receipt"""
        # setup
        dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[2:3]
        )

        receipt = {"status": 0}
        transaction_receipt = TransactionReceipt(LEDGER_ID, receipt, DEFAULT_TX)
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue,
            performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
            transaction_receipt=transaction_receipt,
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.ERROR,
            f"transaction failed. Transaction receipt={transaction_receipt}",
        )

        self.assert_quantity_in_outbox(0)

    def test__handle_transaction_receipt_deploy(self):
        """Test handling a deploy transaction receipt"""
        # setup
        ledger_api_dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[2:3]
        )
        contract_api_dialogue = self.prepare_skill_dialogue(
            self.contract_api_dialogues, self.list_of_contract_api_messages[:1]
        )
        signing_dialogue = self.prepare_skill_dialogue(
            self.signing_dialogues, self.list_of_signing_messages[:1]
        )

        terms = Terms(*DEFAULT_TERMS, label="deploy")

        contract_api_dialogue.terms = terms
        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        ledger_id = LEDGER_ID
        receipt = {"status": 1, "contractAddress": "some_contract_address"}
        transaction_receipt = TransactionReceipt(ledger_id, receipt, DEFAULT_TX)
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ledger_api_dialogue,
            performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
            transaction_receipt=transaction_receipt,
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction was successfully settled. Transaction receipt={transaction_receipt}",
        )
        mock_logger.assert_any_call(
            logging.INFO, "Oracle contract successfully deployed!",
        )

        assert (
            self.simple_oracle_behaviour.context.strategy.is_contract_deployed
        ), "Contract deployment status not set"
        self.assert_quantity_in_outbox(0)

    def test__handle_transaction_receipt_grant_role(self):
        """Test handling a grant_role transaction receipt"""
        # setup
        ledger_api_dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[2:3]
        )
        contract_api_dialogue = self.prepare_skill_dialogue(
            self.contract_api_dialogues, self.list_of_contract_api_messages[:1]
        )
        signing_dialogue = self.prepare_skill_dialogue(
            self.signing_dialogues, self.list_of_signing_messages[:1]
        )

        terms = Terms(*DEFAULT_TERMS, label="grant_role")

        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.is_contract_deployed = True

        contract_api_dialogue.terms = terms
        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        receipt = {"status": 1, "contractAddress": "some_contract_address"}
        transaction_receipt = TransactionReceipt(LEDGER_ID, receipt, DEFAULT_TX)
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ledger_api_dialogue,
            performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
            transaction_receipt=transaction_receipt,
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction was successfully settled. Transaction receipt={transaction_receipt}",
        )
        mock_logger.assert_any_call(
            logging.INFO, "Oracle role successfully granted!",
        )

        assert (
            self.simple_oracle_behaviour.context.strategy.is_oracle_role_granted
        ), "Oracle role status not set"

        self.assert_quantity_in_outbox(0)

    def test__handle_transaction_receipt_update(self):
        """Test handling an update transaction receipt"""
        # setup
        ledger_api_dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[2:3]
        )
        contract_api_dialogue = self.prepare_skill_dialogue(
            self.contract_api_dialogues, self.list_of_contract_api_messages[:1]
        )
        signing_dialogue = self.prepare_skill_dialogue(
            self.signing_dialogues, self.list_of_signing_messages[:1]
        )

        terms = Terms(*DEFAULT_TERMS, label="update")

        strategy = cast(Strategy, self.simple_oracle_behaviour.context.strategy)
        strategy.is_contract_deployed = True
        strategy.is_oracle_role_granted = True

        contract_api_dialogue.terms = terms
        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        receipt = {"status": 1, "contractAddress": "some_contract_address"}
        transaction_receipt = TransactionReceipt(LEDGER_ID, receipt, DEFAULT_TX)
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ledger_api_dialogue,
            performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
            transaction_receipt=transaction_receipt,
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction was successfully settled. Transaction receipt={transaction_receipt}",
        )
        mock_logger.assert_any_call(
            logging.INFO, "Oracle value successfully updated!",
        )

        self.assert_quantity_in_outbox(1)
        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=PrometheusMessage,
            performative=PrometheusMessage.Performative.UPDATE_METRIC,
            callable="inc",
            title="num_oracle_updates",
            value=1.0,
            labels={},
        )
        assert has_attributes, error_str

    def test_teardown(self):
        """Test the teardown method of the ledger_api handler."""
        assert self.ledger_api_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
