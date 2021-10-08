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
"""This module contains the tests of the handler classes of the tac control skill."""

import logging
from pathlib import Path
from typing import Dict, cast
from unittest.mock import patch

from aea_ledger_fetchai import FetchAIApi

from aea.crypto.ledger_apis import LedgerApis
from aea.helpers.transaction.base import (
    RawTransaction,
    SignedTransaction,
    State,
    Terms,
    TransactionDigest,
    TransactionReceipt,
)
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.contract_api.custom_types import Kwargs
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.tac_control_contract.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.tac_control_contract.game import Game, Phase
from packages.fetchai.skills.tac_control_contract.handlers import (
    ContractApiHandler,
    LEDGER_API_ADDRESS,
    LedgerApiHandler,
    SigningHandler,
)
from packages.fetchai.skills.tac_control_contract.parameters import Parameters

from tests.conftest import ROOT_DIR


class TestContractApiHandler(BaseSkillTestCase):
    """Test contract_api handler of tac control contract."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "tac_control_contract"
    )
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.contract_api_handler = cast(
            ContractApiHandler, cls._skill.skill_context.handlers.contract_api
        )
        cls.contract_api_dialogues = cast(
            ContractApiDialogues, cls._skill.skill_context.contract_api_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )
        cls.logger = cls.contract_api_handler.context.logger

        cls.ledger_id = "some_ledger_id"
        cls.contract_id = "some_contract_id"
        cls.callable = "some_callable"
        cls.kwargs = Kwargs({"some_key": "some_value"})

        cls.list_of_contract_api_messages = (
            DialogueMessage(
                ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
                {
                    "ledger_id": cls.ledger_id,
                    "contract_id": cls.contract_id,
                    "callable": cls.callable,
                    "kwargs": cls.kwargs,
                },
            ),
        )

    def test_setup(self):
        """Test the setup method of the contract_api handler."""
        assert self.contract_api_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the signing handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=ContractApiMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=ContractApiMessage.Performative.STATE,
            state=State("some_ledger_id", {"some_key": "some_value"}),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid contract_api message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_raw_transaction(self,):
        """Test the _handle_signed_transaction method of the signing handler."""
        # setup
        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:1],
            ),
        )
        contract_api_dialogue.terms = Terms(
            "some_ledger_id",
            self.skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=contract_api_dialogue,
            performative=ContractApiMessage.Performative.RAW_TRANSACTION,
            raw_transaction=ContractApiMessage.RawTransaction(
                "some_ledger_id", {"some_key": "some_value"}
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"received raw transaction={incoming_message}"
        )

        self.assert_quantity_in_decision_making_queue(1)
        message = self.get_message_from_decision_maker_inbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=SigningMessage,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            terms=contract_api_dialogue.terms,
        )
        assert has_attributes, error_str

        assert (
            cast(
                SigningDialogue, self.signing_dialogues.get_dialogue(message)
            ).associated_contract_api_dialogue
            == contract_api_dialogue
        )

        mock_logger.assert_any_call(
            logging.INFO,
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
        )

    def test_handle_error(self):
        """Test the _handle_error method of the signing handler."""
        # setup
        contract_api_dialogue = self.prepare_skill_dialogue(
            dialogues=self.contract_api_dialogues,
            messages=self.list_of_contract_api_messages[:1],
        )
        incoming_message = cast(
            ContractApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=contract_api_dialogue,
                performative=ContractApiMessage.Performative.ERROR,
                data=b"some_data",
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received contract_api error message={incoming_message} in dialogue={contract_api_dialogue}.",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the signing handler."""
        # setup
        invalid_performative = ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION
        incoming_message = self.build_incoming_message(
            message_type=ContractApiMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            ledger_id=self.ledger_id,
            contract_id=self.contract_id,
            callable=self.callable,
            kwargs=self.kwargs,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle contract_api message of performative={invalid_performative} in dialogue={self.contract_api_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the contract_api handler."""
        assert self.contract_api_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestSigningHandler(BaseSkillTestCase):
    """Test signing handler of tac control contract."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "tac_control_contract"
    )
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.signing_handler = cast(
            SigningHandler, cls._skill.skill_context.handlers.signing
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )
        cls.logger = cls.signing_handler.context.logger

        cls.terms = Terms(
            "some_ledger_id",
            cls._skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        cls.list_of_signing_messages = (
            DialogueMessage(
                SigningMessage.Performative.SIGN_TRANSACTION,
                {
                    "terms": cls.terms,
                    "raw_transaction": SigningMessage.RawTransaction(
                        "some_ledger_id", {"some_key": "some_value"}
                    ),
                },
            ),
        )

    def test_setup(self):
        """Test the setup method of the signing handler."""
        assert self.signing_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the signing handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=SigningMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=SigningMessage.Performative.ERROR,
            error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
            to=str(self.skill.skill_context.skill_id),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid signing message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_signed_transaction(self,):
        """Test the _handle_signed_transaction method of the signing handler."""
        # setup
        signing_counterparty = self.skill.skill_context.decision_maker_address
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:1],
                counterparty=signing_counterparty,
            ),
        )
        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=SigningMessage.SignedTransaction(
                    "some_ledger_id", {"some_key": "some_value"}
                ),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.INFO, "transaction signing was successful.")

        self.assert_quantity_in_outbox(1)
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            signed_transaction=incoming_message.signed_transaction,
        )
        assert has_attributes, error_str

        assert (
            cast(
                LedgerApiDialogue, self.ledger_api_dialogues.get_dialogue(message)
            ).associated_signing_dialogue
            == signing_dialogue
        )

        mock_logger.assert_any_call(logging.INFO, "sending transaction to ledger.")

    def test_handle_error(self):
        """Test the _handle_error method of the signing handler."""
        # setup
        signing_counterparty = self.skill.skill_context.decision_maker_address
        signing_dialogue = self.prepare_skill_dialogue(
            dialogues=self.signing_dialogues,
            messages=self.list_of_signing_messages[:1],
            counterparty=signing_counterparty,
        )
        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.ERROR,
                error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_TRANSACTION_SIGNING,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction signing was not successful. Error_code={incoming_message.error_code} in dialogue={signing_dialogue}",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the signing handler."""
        # setup
        invalid_performative = SigningMessage.Performative.SIGN_TRANSACTION
        incoming_message = self.build_incoming_message(
            message_type=SigningMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            terms=self.terms,
            raw_transaction=SigningMessage.RawTransaction(
                "some_ledger_id", {"some_key": "some_value"}
            ),
            to=str(self.skill.skill_context.skill_id),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle signing message of performative={invalid_performative} in dialogue={self.signing_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the signing handler."""
        assert self.signing_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestLedgerApiHandler(BaseSkillTestCase):
    """Test ledger_api handler of tac control contract."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "tac_control_contract"
    )
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.ledger_api_handler = cast(
            LedgerApiHandler, cls._skill.skill_context.handlers.ledger_api
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )
        cls.contract_api_dialogues = cast(
            ContractApiDialogues, cls._skill.skill_context.contract_api_dialogues
        )
        cls.parameters = cast(Parameters, cls._skill.skill_context.parameters)
        cls.game = cast(Game, cls._skill.skill_context.game)

        cls.logger = cls.ledger_api_handler.context.logger

        cls.ledger_id = "some_ledger_id"
        cls.contract_id = "some_contract_id"
        cls.callable = "some_callable"
        cls.kwargs = Kwargs({"some_key": "some_value"})

        cls.body = {"some_key": "some_value"}
        cls.body_str = "some_body"
        cls.contract_address = "some_contract_address"

        cls.raw_transaction = RawTransaction(cls.ledger_id, cls.body)
        cls.signed_transaction = SignedTransaction(cls.ledger_id, cls.body)
        cls.transaction_digest = TransactionDigest(cls.ledger_id, cls.body_str)
        cls.receipt = {"contractAddress": cls.contract_address}
        cls.code_id = 8888
        cls.fetch_deploy_receipt = {
            "logs": [
                {
                    "events": [
                        {
                            "attributes": [
                                {"key": "code_id", "value": cls.code_id},
                                {
                                    "key": "contract_address",
                                    "value": "some_contract_address",
                                },
                            ]
                        }
                    ]
                }
            ]
        }
        cls.fetch_deploy_receipt_no_code_id = {
            "logs": [
                {
                    "events": [
                        {
                            "attributes": [
                                {"key": "not_a_code_id", "value": "something"},
                                {
                                    "key": "contract_address",
                                    "value": "some_contract_address",
                                },
                            ]
                        }
                    ]
                }
            ]
        }
        cls.fetch_init_receipt = {"status": 1, "contractAddress": cls.contract_address}
        cls.transaction_receipt = TransactionReceipt(
            cls.ledger_id, cls.receipt, {"transaction_key": "transaction_value"}
        )

        cls.terms_dict = {
            "ledger_id": cls.ledger_id,
            "sender_address": cls._skill.skill_context.agent_address,
            "counterparty_address": "counterprty",
            "amount_by_currency_id": {"currency_id": 50},
            "quantities_by_good_id": {"good_id": -10},
            "nonce": "some_nonce",
        }

        cls.list_of_signing_messages = (
            DialogueMessage(
                SigningMessage.Performative.SIGN_TRANSACTION,
                {
                    "terms": Terms(**cls.terms_dict),
                    "raw_transaction": SigningMessage.RawTransaction(
                        cls.ledger_id, cls.body
                    ),
                },
            ),
        )
        cls.list_of_contract_api_messages = (
            DialogueMessage(
                ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
                {
                    "ledger_id": cls.ledger_id,
                    "contract_id": cls.contract_id,
                    "callable": cls.callable,
                    "kwargs": cls.kwargs,
                },
            ),
        )
        cls.list_of_ledger_api_messages = (
            DialogueMessage(
                LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
                {"terms": Terms(**cls.terms_dict)},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.RAW_TRANSACTION,
                {"raw_transaction": cls.raw_transaction},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
                {"signed_transaction": cls.signed_transaction},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                {"transaction_digest": cls.transaction_digest},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                {"transaction_digest": cls.transaction_digest},
            ),
        )

    @staticmethod
    def _terms(terms_dict: Dict, label: str) -> Terms:
        """
        Provides Terms with the specified label.

        :param label: the label
        :return: Terms
        """
        terms_dict["label"] = label
        return Terms(**terms_dict)

    @staticmethod
    def _transaction_receipt_builder(ledger_id: str, receipt) -> TransactionReceipt:
        """
        Provides Terms with the specified label.

        :param ledger_id: the ledger_id
        :param receipt: the transaction receipt
        :return: Terms
        """
        transaction_receipt = TransactionReceipt(
            ledger_id, receipt, {"transaction_key": "transaction_value"}
        )
        return transaction_receipt

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
            performative=LedgerApiMessage.Performative.BALANCE,
            ledger_id="some_ledger_id",
            balance=10,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid ledger_api message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_balance(self):
        """Test the _handle_balance method of the ledger_api handler."""
        # setup
        balance = 10
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=(
                    DialogueMessage(
                        LedgerApiMessage.Performative.GET_BALANCE,
                        {"ledger_id": self.ledger_id, "address": "some_address"},
                    ),
                ),
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.BALANCE,
                ledger_id=self.ledger_id,
                balance=balance,
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

    def test_handle_transaction_digest(self):
        """Test the _handle_transaction_digest method of the ledger_api handler."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:3],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                transaction_digest=self.transaction_digest,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction was successfully submitted. Transaction digest={incoming_message.transaction_digest}",
        )

        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            transaction_digest=incoming_message.transaction_digest,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(logging.INFO, "requesting transaction receipt.")

    def test_handle_transaction_receipt_failed(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where the transaction is NOT settled."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:4],
            ),
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:4],
            ),
        )

        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(LedgerApis, "is_transaction_settled", return_value=False):
                self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.ERROR,
            f"transaction failed. Transaction receipt={incoming_message.transaction_receipt}",
        )

    def test_handle_transaction_receipt_callable_get_deploy_transaction_label_store(
        self,
    ):
        """Test the _handle_transaction_receipt method of the ledger_api handler where contract_api callable is GET_DEPLOY_TRANSACTION and terms label is 'store'."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:4],
            ),
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:4],
            ),
        )

        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        contract_api_dialogue.callable = (
            ContractApiDialogue.Callable.GET_DEPLOY_TRANSACTION
        )
        contract_api_dialogue.terms = self._terms(self.terms_dict, "store")

        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self._transaction_receipt_builder(
                    FetchAIApi.identifier, self.fetch_deploy_receipt
                ),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                self.ledger_api_handler.handle(incoming_message)

        # after
        # _request_init_transaction
        self.assert_quantity_in_outbox(1)
        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            ledger_id=self.parameters.ledger_id,
            contract_id=self.parameters.contract_id,
            callable=ContractApiDialogue.Callable.GET_DEPLOY_TRANSACTION.value,
            kwargs=ContractApiMessage.Kwargs(
                {
                    "label": "TACERC1155",
                    "init_msg": {},
                    "gas": self.parameters.gas,
                    "amount": 0,
                    "code_id": self.code_id,
                    "deployer_address": self.skill.skill_context.agent_address,
                    "tx_fee": 0,
                }
            ),
        )
        assert has_attributes, error_str

        assert contract_api_dialogue.terms == self.parameters.get_deploy_terms(
            is_init_transaction=True
        )
        assert (
            contract_api_dialogue.callable
            == ContractApiDialogue.Callable.GET_DEPLOY_TRANSACTION
        )

        mock_logger.assert_any_call(
            logging.INFO, "requesting contract initialisation transaction...",
        )

    def test_handle_transaction_receipt_callable_get_deploy_transaction_label_store_no_code_id(
        self,
    ):
        """Test the _handle_transaction_receipt method of the ledger_api handler where contract_api callable is GET_DEPLOY_TRANSACTION and terms label is 'store' and no code_id."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:4],
            ),
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:4],
            ),
        )

        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        contract_api_dialogue.callable = (
            ContractApiDialogue.Callable.GET_DEPLOY_TRANSACTION
        )
        contract_api_dialogue.terms = self._terms(self.terms_dict, "store")

        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self._transaction_receipt_builder(
                    FetchAIApi.identifier, self.fetch_deploy_receipt_no_code_id
                ),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                self.ledger_api_handler.handle(incoming_message)

        # after
        # _request_init_transaction
        self.assert_quantity_in_outbox(0)
        mock_logger.assert_any_call(
            logging.INFO, "Failed to initialise contract: code_id not found",
        )

    def test_handle_transaction_receipt_callable_get_deploy_transaction_label_init(
        self,
    ):
        """Test the _handle_transaction_receipt method of the ledger_api handler where contract_api callable is GET_DEPLOY_TRANSACTION and terms label is 'init'."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:4],
            ),
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:4],
            ),
        )

        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        contract_api_dialogue.callable = (
            ContractApiDialogue.Callable.GET_DEPLOY_TRANSACTION
        )
        contract_api_dialogue.terms = self._terms(self.terms_dict, "init")

        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self._transaction_receipt_builder(
                    FetchAIApi.identifier, self.fetch_init_receipt
                ),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                with patch.object(
                    LedgerApis,
                    "get_contract_address",
                    return_value=self.contract_address,
                ):
                    self.ledger_api_handler.handle(incoming_message)

        # after
        assert self.parameters.contract_address == self.contract_address
        assert self.game.phase == Phase.CONTRACT_DEPLOYED

        mock_logger.assert_any_call(logging.INFO, "contract deployed.")

    def test_handle_transaction_receipt_callable_get_deploy_transaction_label_deploy(
        self,
    ):
        """Test the _handle_transaction_receipt method of the ledger_api handler where contract_api callable is GET_DEPLOY_TRANSACTION and terms label is 'deploy'."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:4],
            ),
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:4],
            ),
        )

        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        contract_api_dialogue.callable = (
            ContractApiDialogue.Callable.GET_DEPLOY_TRANSACTION
        )
        contract_api_dialogue.terms = self._terms(self.terms_dict, "deploy")

        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self._transaction_receipt_builder(
                    FetchAIApi.identifier, self.fetch_init_receipt
                ),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                with patch.object(
                    LedgerApis,
                    "get_contract_address",
                    return_value=self.contract_address,
                ):
                    self.ledger_api_handler.handle(incoming_message)

        # after
        assert self.parameters.contract_address == self.contract_address
        assert self.game.phase == Phase.CONTRACT_DEPLOYED

        mock_logger.assert_any_call(logging.INFO, "contract deployed.")

    def test_handle_transaction_receipt_callable_get_create_batch_transaction(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where contract_api callable is GET_CREATE_BATCH_TRANSACTION."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:4],
            ),
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:4],
            ),
        )

        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        contract_api_dialogue.callable = (
            ContractApiDialogue.Callable.GET_CREATE_BATCH_TRANSACTION
        )

        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                self.ledger_api_handler.handle(incoming_message)

        # after
        assert self.game.phase == Phase.TOKENS_CREATED

        mock_logger.assert_any_call(logging.INFO, "tokens created.")

    def test_handle_transaction_receipt_callable_get_mint_batch_transaction_i(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where contract_api callable is GET_MINT_BATCH_TRANSACTION and all tokens are NOT minted."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:4],
            ),
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:4],
            ),
        )

        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        contract_api_dialogue.callable = (
            ContractApiDialogue.Callable.GET_MINT_BATCH_TRANSACTION
        )

        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        self.parameters.nb_completed_minting = 0
        self.game._registration._agent_addr_to_name = {
            "some_address_1": "some_name_1",
            "some_address_2": "some_name_2",
        }

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.INFO, "tokens minted.")
        assert self.parameters.nb_completed_minting == 1
        assert self.game.is_allowed_to_mint is True
        assert self.game.phase != Phase.TOKENS_MINTED

    def test_handle_transaction_receipt_callable_get_mint_batch_transaction_ii(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where contract_api callable is GET_MINT_BATCH_TRANSACTION and all tokens are minted."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:4],
            ),
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:4],
            ),
        )

        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        contract_api_dialogue.callable = (
            ContractApiDialogue.Callable.GET_MINT_BATCH_TRANSACTION
        )

        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        self.parameters.nb_completed_minting = 0
        self.game._registration._agent_addr_to_name = {"some_address": "some_name"}

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.INFO, "tokens minted.")
        assert self.parameters.nb_completed_minting == 1
        assert self.game.is_allowed_to_mint is True
        assert self.game.phase == Phase.TOKENS_MINTED
        mock_logger.assert_any_call(logging.INFO, "all tokens minted.")

    def test_handle_transaction_receipt_incorrect_callable(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where contract_api callable is incorrect."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:4],
            ),
        )
        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:4],
            ),
        )

        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        contract_api_dialogue.callable = "some_incorrect_callable"

        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.ERROR, "unexpected transaction receipt!")

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
