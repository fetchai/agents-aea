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

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.contracts.oracle_client.contract import (
    PUBLIC_ID as CONTRACT_PUBLIC_ID,
)
from packages.fetchai.protocols.contract_api.custom_types import Kwargs
from packages.fetchai.protocols.contract_api.custom_types import (
    Kwargs as ContractApiKwargs,
)
from packages.fetchai.protocols.contract_api.custom_types import State
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.ledger_api.custom_types import (
    SignedTransaction,
    TransactionDigest,
    TransactionReceipt,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.signing.custom_types import RawTransaction
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.simple_oracle_client.behaviours import (
    SimpleOracleClientBehaviour,
)
from packages.fetchai.skills.simple_oracle_client.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.simple_oracle_client.handlers import (
    ContractApiHandler,
    LedgerApiHandler,
    SigningHandler,
)
from packages.fetchai.skills.simple_oracle_client.strategy import Strategy

from tests.conftest import ROOT_DIR


ETHEREUM_LEDGER_ID = "ethereum"
FETCHAI_LEDGER_ID = "fetchai"
DEFAULT_TX = {"some_tx_key": "some_tx_value"}
DEFAULT_TERMS = [
    ETHEREUM_LEDGER_ID,
    "sender_address",
    "counterparty_address",
    {},
    {},
    "some_nonce",
]
FETCHAI_DEPLOY_RECEIPT = {
    "logs": [
        {
            "events": [
                {
                    "attributes": [
                        {"key": "code_id", "value": "8888"},
                        {"key": "contract_address", "value": "some_contract_address"},
                    ]
                }
            ]
        }
    ]
}


class TestLedgerApiHandler(BaseSkillTestCase):
    """Test ledger_api handler of simple_oracle_client skill."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_oracle_client"
    )
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup(**kwargs)
        cls.ledger_api_handler = cast(
            LedgerApiHandler, cls._skill.skill_context.handlers.ledger_api
        )
        cls.logger = cls._skill.skill_context.logger
        cls.simple_oracle_client_behaviour = cast(
            SimpleOracleClientBehaviour,
            cls._skill.skill_context.behaviours.simple_oracle_client_behaviour,
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
                {"ledger_id": ETHEREUM_LEDGER_ID, "address": "some_eth_address"},
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
                {
                    "signed_transaction": SignedTransaction(
                        ETHEREUM_LEDGER_ID, DEFAULT_TX
                    )
                },
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                {
                    "transaction_digest": TransactionDigest(
                        ETHEREUM_LEDGER_ID, "some_digest"
                    )
                },
            ),
            DialogueMessage(
                LedgerApiMessage.Performative.GET_STATE,
                {
                    "ledger_id": ETHEREUM_LEDGER_ID,
                    "callable": "some_callable",
                    "args": (),
                    "kwargs": LedgerApiMessage.Kwargs({}),
                },
            ),
        )
        cls.list_of_contract_api_messages = (
            DialogueMessage(
                ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
                {
                    "ledger_id": ETHEREUM_LEDGER_ID,
                    "contract_id": "some_contract_id",
                    "callable": "some_callable",
                    "kwargs": ContractApiKwargs({"some_key": "some_value"}),
                },
            ),
            DialogueMessage(
                ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
                {
                    "ledger_id": FETCHAI_LEDGER_ID,
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
                    "raw_transaction": RawTransaction(ETHEREUM_LEDGER_ID, DEFAULT_TX),
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
            ledger_id=ETHEREUM_LEDGER_ID,
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
            ledger_id=ETHEREUM_LEDGER_ID,
            balance=balance,
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"starting balance on {ETHEREUM_LEDGER_ID} ledger={balance}.",
        )

        self.assert_quantity_in_outbox(0)

    def test__handle_transaction_digest(self):
        """Test handling a transaction digest"""
        # setup
        dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[1:2]
        )
        digest = "some_digest"
        transaction_digest = TransactionDigest(ETHEREUM_LEDGER_ID, digest)
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
            f"transaction was successfully submitted. Transaction digest=TransactionDigest: ledger_id={ETHEREUM_LEDGER_ID}, body={digest}",
        )

        self.assert_quantity_in_outbox(1)

    def test__handle_transaction_receipt_failed(self):
        """Test handling a transaction receipt"""
        # setup
        dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[2:3]
        )

        receipt = {"status": 0}
        transaction_receipt = TransactionReceipt(
            ETHEREUM_LEDGER_ID, receipt, DEFAULT_TX
        )
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

        ledger_id = ETHEREUM_LEDGER_ID
        strategy = cast(Strategy, self.simple_oracle_client_behaviour.context.strategy)
        strategy._ledger_id = ledger_id

        contract_api_dialogue.terms = strategy.get_deploy_terms()
        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        receipt = {"status": 1, "contractAddress": "some_contract_address"}
        transaction_receipt = TransactionReceipt(ledger_id, receipt, DEFAULT_TX)
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=ledger_api_dialogue,
            performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
            transaction_receipt=transaction_receipt,
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            with patch(
                "aea.crypto.ledger_apis.LedgerApis.get_contract_address",
                return_value="some_contract_address",
            ):
                self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction was successfully settled. Transaction receipt={transaction_receipt}",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            "Oracle client contract successfully deployed at address: some_contract_address",
        )

        assert (
            self.simple_oracle_client_behaviour.context.strategy.is_client_contract_deployed
        ), "Contract deployment status not set"
        self.assert_quantity_in_outbox(0)

    def test__handle_transaction_receipt_store(self):
        """Test handling a store contract code transaction receipt"""
        # setup
        ledger_api_dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[2:3]
        )
        contract_api_dialogue = self.prepare_skill_dialogue(
            self.contract_api_dialogues, self.list_of_contract_api_messages[1:2]
        )
        signing_dialogue = self.prepare_skill_dialogue(
            self.signing_dialogues, self.list_of_signing_messages[:1]
        )

        strategy = cast(Strategy, self.simple_oracle_client_behaviour.context.strategy)
        strategy._ledger_id = "fetchai"
        strategy.oracle_contract_address = "some_oracle_address"

        contract_api_dialogue.terms = strategy.get_deploy_terms()
        assert contract_api_dialogue.terms.kwargs["label"] == "store"

        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        transaction_receipt = TransactionReceipt(
            FETCHAI_LEDGER_ID, FETCHAI_DEPLOY_RECEIPT, DEFAULT_TX
        )
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
        self.assert_quantity_in_outbox(1)
        msg = cast(ContractApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            ledger_id="fetchai",
            contract_id=str(CONTRACT_PUBLIC_ID),
            callable="get_deploy_transaction",
            kwargs=ContractApiMessage.Kwargs(
                {
                    "label": "OracleContract",
                    "init_msg": {
                        "oracle_contract_address": strategy.oracle_contract_address
                    },
                    "gas": strategy.default_gas_deploy,
                    "amount": 0,
                    "code_id": 8888,
                    "deployer_address": "test_agent_address",
                }
            ),
        )
        assert has_attributes, error_str

    def test__handle_transaction_receipt_init(self):
        """Test handling a store contract code transaction receipt"""
        # setup
        ledger_api_dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[2:3]
        )
        contract_api_dialogue = self.prepare_skill_dialogue(
            self.contract_api_dialogues, self.list_of_contract_api_messages[1:2]
        )
        signing_dialogue = self.prepare_skill_dialogue(
            self.signing_dialogues, self.list_of_signing_messages[:1]
        )

        ledger_id = FETCHAI_LEDGER_ID
        strategy = cast(Strategy, self.simple_oracle_client_behaviour.context.strategy)
        strategy._ledger_id = ledger_id

        contract_api_dialogue.terms = strategy.get_deploy_terms(
            is_init_transaction=True
        )
        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        transaction_receipt = TransactionReceipt(
            ledger_id, FETCHAI_DEPLOY_RECEIPT, DEFAULT_TX
        )
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
            logging.INFO,
            "Oracle client contract successfully deployed at address: some_contract_address",
        )

        assert (
            self.simple_oracle_client_behaviour.context.strategy.is_client_contract_deployed
        ), "Contract deployment status not set"
        self.assert_quantity_in_outbox(0)

    def test__handle_transaction_receipt_approve(self):
        """Test handling an approve transaction receipt"""
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

        terms = Terms(*DEFAULT_TERMS, label="approve")

        strategy = cast(Strategy, self.simple_oracle_client_behaviour.context.strategy)
        strategy.is_client_contract_deployed = True

        contract_api_dialogue.terms = terms
        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        receipt = {"status": 1, "contractAddress": "some_contract_address"}
        transaction_receipt = TransactionReceipt(
            ETHEREUM_LEDGER_ID, receipt, DEFAULT_TX
        )
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
            logging.INFO, "Oracle client transactions approved!",
        )

        assert (
            self.simple_oracle_client_behaviour.context.strategy.is_oracle_transaction_approved
        ), "Contract deployment status not set"

        self.assert_quantity_in_outbox(0)

    def test__handle_transaction_receipt_query(self):
        """Test handling a query transaction receipt"""
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

        terms = Terms(*DEFAULT_TERMS, label="query")

        strategy = cast(Strategy, self.simple_oracle_client_behaviour.context.strategy)
        strategy.is_client_contract_deployed = True
        strategy.is_oracle_role_granted = True

        contract_api_dialogue.terms = terms
        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue

        receipt = {"status": 1, "contractAddress": "some_contract_address"}
        transaction_receipt = TransactionReceipt(
            ETHEREUM_LEDGER_ID, receipt, DEFAULT_TX
        )
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
            logging.INFO, "Oracle value successfully requested!",
        )

        self.assert_quantity_in_outbox(0)

    def test__handle_error(self):
        """Test handling an error message"""
        # setup
        dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[2:3]
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue, performative=LedgerApiMessage.Performative.ERROR, code=1,
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received ledger_api error message={incoming_message} in dialogue={dialogue}.",
        )

        self.assert_quantity_in_outbox(0)

    def test__handle_invalid(self):
        """Test handling an invalid performative"""
        # setup
        dialogue = self.prepare_skill_dialogue(
            self.ledger_api_dialogues, self.list_of_ledger_api_messages[3:4]
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue,
            performative=LedgerApiMessage.Performative.STATE,
            ledger_id=ETHEREUM_LEDGER_ID,
            state=LedgerApiMessage.State(ETHEREUM_LEDGER_ID, {}),
        )

        # operation
        with patch.object(self.ledger_api_handler.context.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle ledger_api message of performative={incoming_message.performative} in dialogue={dialogue}.",
        )

        self.assert_quantity_in_outbox(0)

    def test_teardown(self):
        """Test the teardown method of the ledger_api handler."""
        assert self.ledger_api_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestContractApiHandler(BaseSkillTestCase):
    """Test contract_api handler of simple oracle client."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_oracle_client"
    )
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.contract_api_handler = cast(
            ContractApiHandler, cls._skill.skill_context.handlers.contract_api
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.logger = cls.contract_api_handler.context.logger

        cls.contract_api_dialogues = cast(
            ContractApiDialogues, cls._skill.skill_context.contract_api_dialogues
        )

        cls.contract_id = "some_contract_id"
        cls.contract_address = "some_contract_address,"
        cls.callable = "some_callable"
        cls.kwargs = Kwargs({"some_key": "some_value"})

        cls.state = State("some_ledger_id", {"some_key": "some_value"})
        cls.terms = Terms(
            ledger_id="some_ledger_id",
            sender_address="some_sender_address",
            counterparty_address="some_counterparty",
            amount_by_currency_id={"1": -10},
            quantities_by_good_id={},
            is_sender_payable_tx_fee=True,
            nonce="some_none",
            fee_by_currency_id={"1": 100},
        )
        cls.list_of_contract_api_messages = (
            DialogueMessage(
                ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
                {
                    "ledger_id": ETHEREUM_LEDGER_ID,
                    "contract_id": cls.contract_id,
                    "callable": cls.callable,
                    "kwargs": cls.kwargs,
                },
            ),
        )
        cls.info = {"ethereum_address": "some_ethereum_address"}

    def test_setup(self):
        """Test the setup method of the contract_api handler."""
        assert self.contract_api_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the contract_api handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=ContractApiMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=ContractApiMessage.Performative.STATE,
            state=self.state,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid contract_api message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_raw_transaction(self):
        """Test the _handle_raw_transaction method of the contract_api handler."""
        # setup
        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:1],
            ),
        )
        contract_api_dialogue.terms = self.terms
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=contract_api_dialogue,
            performative=ContractApiMessage.Performative.RAW_TRANSACTION,
            raw_transaction=ContractApiMessage.RawTransaction(ETHEREUM_LEDGER_ID, {}),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"received raw transaction={incoming_message}",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
        )

        self.assert_quantity_in_decision_making_queue(1)

    def test_handle_error(self):
        """Test the _handle_error method of the contract_api handler."""
        # setup
        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:1],
            ),
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
            f"received ledger_api error message={incoming_message} in dialogue={contract_api_dialogue}.",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the contract_api handler."""
        # setup
        invalid_performative = ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION
        incoming_message = self.build_incoming_message(
            message_type=ContractApiMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            ledger_id=ETHEREUM_LEDGER_ID,
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
    """Test signing handler of simple oracle client."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_oracle_client"
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
            to=str(LEDGER_CONNECTION_PUBLIC_ID),
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
