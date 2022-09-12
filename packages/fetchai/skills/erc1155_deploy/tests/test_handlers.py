# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""This module contains the tests of the handler classes of the erc1155_deploy skill."""
# pylint: skip-file

import logging
from typing import cast
from unittest.mock import patch

from aea.crypto.ledger_apis import LedgerApis
from aea.helpers.transaction.base import State
from aea.protocols.dialogue.base import Dialogues
from aea.test_tools.test_skill import COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.erc1155_deploy.dialogues import (
    ContractApiDialogue,
    FipaDialogue,
    LedgerApiDialogue,
    OefSearchDialogue,
    SigningDialogue,
)
from packages.fetchai.skills.erc1155_deploy.handlers import LEDGER_API_ADDRESS
from packages.fetchai.skills.erc1155_deploy.tests.intermediate_class import (
    ERC1155DeployTestCase,
)
from packages.open_aea.protocols.signing.message import SigningMessage


class TestFipaHandler(ERC1155DeployTestCase):
    """Test fipa handler of erc1155_deploy."""

    def test_setup(self):
        """Test the setup method of the fipa handler."""
        assert self.fipa_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the fipa handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = cast(
            FipaMessage,
            self.build_incoming_message(
                message_type=FipaMessage,
                dialogue_reference=incorrect_dialogue_reference,
                performative=FipaMessage.Performative.ACCEPT,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"unidentified dialogue for message={incoming_message}.",
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
            error_data={"fipa_message": incoming_message.encode()},
        )
        assert has_attributes, error_str

    def test_handle_cfp_i(self):
        """Test the _handle_cfp method of the fipa handler where is_tokens_minted is True."""
        # setup
        self.strategy._is_tokens_minted = True
        incoming_message = cast(
            FipaMessage,
            self.build_incoming_message(
                message_type=FipaMessage,
                performative=FipaMessage.Performative.CFP,
                dialogue_reference=Dialogues.new_self_initiated_dialogue_reference(),
                query=self.mocked_query,
            ),
        )

        # operation
        with patch.object(
            self.strategy, "get_proposal", return_value=self.mocked_proposal
        ) as mock_prop:
            with patch.object(self.logger, "log") as mock_logger:
                self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received CFP from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )

        mock_prop.assert_called_once()

        self.assert_quantity_in_outbox(1)
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=FipaMessage,
            performative=FipaMessage.Performative.PROPOSE,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            proposal=self.mocked_proposal,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"sending PROPOSE to agent={COUNTERPARTY_AGENT_ADDRESS[-5:]}: proposal={self.mocked_proposal.values}",
        )

    def test_handle_cfp_ii(self):
        """Test the _handle_cfp method of the fipa handler where is_tokens_minted is False."""
        # setup
        self.strategy._is_tokens_minted = False
        incoming_message = cast(
            FipaMessage,
            self.build_incoming_message(
                message_type=FipaMessage,
                performative=FipaMessage.Performative.CFP,
                dialogue_reference=Dialogues.new_self_initiated_dialogue_reference(),
                query=self.mocked_query,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received CFP from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}",
        )

        mock_logger.assert_any_call(
            logging.INFO,
            "Contract items not minted yet. Try again later.",
        )

        self.assert_quantity_in_outbox(0)

    def test_handle_accept_w_inform_i(self):
        """Test the _handle_accept_w_inform method of the fipa handler where tx_signature is NOT None."""
        # setup
        tx_signature = "some_tx_signature"
        self.strategy.contract_address = self.contract_address
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:2],
            ),
        )
        fipa_dialogue.proposal = self.mocked_proposal
        incoming_message = cast(
            FipaMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=fipa_dialogue,
                performative=FipaMessage.Performative.ACCEPT_W_INFORM,
                info={"tx_signature": tx_signature},
            ),
        )

        # operation
        with patch.object(
            self.strategy, "get_single_swap_terms", return_value=self.mocked_terms
        ) as mock_swap:
            with patch.object(self.logger, "log") as mock_logger:
                self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received ACCEPT_W_INFORM from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}: tx_signature={tx_signature}",
        )

        self.assert_quantity_in_outbox(1)
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=self.strategy.ledger_id,
            contract_id=self.strategy.contract_id,
            contract_address=self.strategy.contract_address,
            callable="get_atomic_swap_single_transaction",
            kwargs=ContractApiMessage.Kwargs(
                {
                    "from_address": self.skill.skill_context.agent_address,
                    "to_address": incoming_message.sender,
                    "token_id": int(fipa_dialogue.proposal.values["token_id"]),
                    "from_supply": int(fipa_dialogue.proposal.values["from_supply"]),
                    "to_supply": int(fipa_dialogue.proposal.values["to_supply"]),
                    "value": int(fipa_dialogue.proposal.values["value"]),
                    "trade_nonce": int(fipa_dialogue.proposal.values["trade_nonce"]),
                    "signature": tx_signature,
                }
            ),
        )
        assert has_attributes, error_str

        mock_swap.assert_called_once()
        contract_api_dialogue = cast(
            ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
        )
        assert contract_api_dialogue.terms == self.mocked_terms

        mock_logger.assert_any_call(
            logging.INFO,
            "requesting single atomic swap transaction...",
        )

    def test_handle_accept_w_inform_ii(self):
        """Test the _handle_accept_w_inform method of the fipa handler where tx_signature is NOT None."""
        # setup
        tx_signature = "some_tx_signature"
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:2],
            ),
        )
        fipa_dialogue.proposal = self.mocked_proposal
        incoming_message = cast(
            FipaMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=fipa_dialogue,
                performative=FipaMessage.Performative.ACCEPT_W_INFORM,
                info={"something": tx_signature},
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received ACCEPT_W_INFORM from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]} with no signature.",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the fipa handler."""
        # setup
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:2],
            ),
        )
        incoming_message = cast(
            FipaMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=fipa_dialogue,
                performative=FipaMessage.Performative.ACCEPT,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle fipa message of performative={incoming_message.performative} in dialogue={fipa_dialogue}.",
        )

    def test_teardown(self):
        """Test the teardown method of the fipa handler."""
        assert self.fipa_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestLedgerApiHandler(ERC1155DeployTestCase):
    """Test ledger_api handler of erc1155_deploy."""

    is_agent_to_agent_messages = False

    def test_setup(self):
        """Test the setup method of the ledger_api handler."""
        assert self.ledger_api_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the ledger_api handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message(
                message_type=LedgerApiMessage,
                dialogue_reference=incorrect_dialogue_reference,
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
                messages=self.list_of_ledger_api_balance_messages[:1],
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
                transaction_digest=self.mocked_tx_digest,
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
            to=incoming_message.sender,
            sender=str(self.skill.skill_context.skill_id),
            transaction_digest=self.mocked_tx_digest,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            "requesting transaction receipt.",
        )

    def test_handle_transaction_receipt_i(self):
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
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.mocked_tx_receipt,
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

    def test_handle_transaction_receipt_ii(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where is_contract_deployed is False."""
        # setup
        self.strategy._is_contract_deployed = False

        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.mocked_tx_receipt,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction was successfully settled. Transaction receipt={self.mocked_tx_receipt}",
        )

        assert self.strategy.contract_address == self.contract_address
        assert self.strategy.is_contract_deployed is True
        assert self.strategy.is_behaviour_active is True

    def test_handle_transaction_receipt_iii(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where is_tokens_created is False."""
        # setup
        self.strategy._is_contract_deployed = True
        self.strategy._is_tokens_created = False

        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.mocked_tx_receipt,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction was successfully settled. Transaction receipt={self.mocked_tx_receipt}",
        )

        assert self.strategy.is_tokens_created is True
        assert self.strategy.is_behaviour_active is True

    def test_handle_transaction_receipt_iv(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where is_tokens_minted is False."""
        # setup
        self.strategy._is_contract_deployed = True
        self.strategy._is_tokens_created = True
        self.strategy._is_tokens_minted = False

        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.mocked_tx_receipt,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction was successfully settled. Transaction receipt={self.mocked_tx_receipt}",
        )

        assert self.strategy.is_tokens_minted is True
        assert self.strategy.is_behaviour_active is True

    def test_handle_transaction_receipt_v(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where is_tokens_minted is True."""
        # setup
        self.strategy._is_contract_deployed = True
        self.strategy._is_tokens_created = True
        self.strategy._is_tokens_minted = True

        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.mocked_tx_receipt,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(LedgerApis, "is_transaction_settled", return_value=True):
                self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction was successfully settled. Transaction receipt={self.mocked_tx_receipt}",
        )

        assert self.skill.skill_context.is_active is False
        mock_logger.assert_any_call(logging.INFO, "demo finished!")

    def test_handle_error(self):
        """Test the _handle_error method of the ledger_api handler."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_balance_messages[:1],
            ),
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
        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message(
                message_type=LedgerApiMessage,
                dialogue_reference=("1", ""),
                performative=invalid_performative,
                ledger_id=self.ledger_id,
                address=self.address,
                to=str(self.skill.skill_context.skill_id),
            ),
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


class TestContractApiHandler(ERC1155DeployTestCase):
    """Test contract_api handler of erc1155_deploy."""

    is_agent_to_agent_messages = False

    def test_setup(self):
        """Test the setup method of the contract_api handler."""
        assert self.contract_api_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the signing handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = cast(
            ContractApiMessage,
            self.build_incoming_message(
                message_type=ContractApiMessage,
                dialogue_reference=incorrect_dialogue_reference,
                performative=ContractApiMessage.Performative.STATE,
                state=State(self.ledger_id, self.body_dict),
            ),
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
        """Test the _handle_raw_transaction method of the signing handler."""
        # setup
        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:1],
            ),
        )
        contract_api_dialogue.terms = self.mocked_terms
        incoming_message = cast(
            ContractApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=contract_api_dialogue,
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                raw_transaction=self.mocked_raw_tx,
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
            raw_transaction=self.mocked_raw_tx,
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
            f"received contract_api error message={incoming_message} in dialogue={contract_api_dialogue}.",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the signing handler."""
        # setup
        invalid_performative = ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION
        incoming_message = cast(
            ContractApiMessage,
            self.build_incoming_message(
                message_type=ContractApiMessage,
                dialogue_reference=("1", ""),
                performative=invalid_performative,
                ledger_id=self.ledger_id,
                contract_id=self.contract_id,
                callable=self.callable,
                kwargs=self.kwargs,
            ),
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


class TestSigningHandler(ERC1155DeployTestCase):
    """Test signing handler of erc1155_deploy."""

    is_agent_to_agent_messages = False

    def test_setup(self):
        """Test the setup method of the signing handler."""
        assert self.signing_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the signing handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message(
                message_type=SigningMessage,
                dialogue_reference=incorrect_dialogue_reference,
                performative=SigningMessage.Performative.ERROR,
                error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
                to=str(self.skill.skill_context.skill_id),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid signing message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_signed_transaction(
        self,
    ):
        """Test the _handle_signed_transaction method of the signing handler."""
        # setup
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )
        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                signed_transaction=self.mocked_signed_tx,
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
            signed_transaction=self.mocked_signed_tx,
        )
        assert has_attributes, error_str

        ledger_api_dialogue = cast(
            LedgerApiDialogue, self.ledger_api_dialogues.get_dialogue(message)
        )
        assert ledger_api_dialogue.associated_signing_dialogue == signing_dialogue

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
            terms=self.mocked_terms,
            raw_transaction=SigningMessage.RawTransaction(
                self.ledger_id, {"some_key": "some_value"}
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


class TestOefSearchHandler(ERC1155DeployTestCase):
    """Test oef_search handler of erc1155_deploy."""

    is_agent_to_agent_messages = False

    def test_setup(self):
        """Test the setup method of the oef_search handler."""
        assert self.oef_search_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the oef_search handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message(
                message_type=OefSearchMessage,
                dialogue_reference=incorrect_dialogue_reference,
                performative=OefSearchMessage.Performative.OEF_ERROR,
                oef_error_operation=OefSearchMessage.OefErrorOperation.REGISTER_SERVICE,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid oef_search message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_error(self):
        """Test the _handle_error method of the oef_search handler."""
        # setup
        oef_search_dialogue = cast(
            OefSearchDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.oef_search_dialogues,
                messages=self.list_of_messages_register_location[:1],
            ),
        )
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_search_dialogue,
                performative=OefSearchMessage.Performative.OEF_ERROR,
                oef_error_operation=OefSearchMessage.OefErrorOperation.REGISTER_SERVICE,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search error message={incoming_message} in dialogue={oef_search_dialogue}.",
        )

    def test_handle_success_i(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH location_agent data model description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_search_dialogues,
            messages=self.list_of_messages_register_location[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(
                self.registration_behaviour,
                "register_service",
            ) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()

    def test_handle_success_ii(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH set_service_key data model description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_search_dialogues,
            messages=self.list_of_messages_register_service[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(
                self.registration_behaviour,
                "register_genus",
            ) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()

    def test_handle_success_iii(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH personality_agent data model and genus value description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_search_dialogues,
            messages=self.list_of_messages_register_genus[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(
                self.registration_behaviour,
                "register_classification",
            ) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()

    def test_handle_success_iv(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH personality_agent data model and classification value description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_search_dialogues,
            messages=self.list_of_messages_register_classification[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )

        assert self.registration_behaviour.is_registered is True
        assert self.registration_behaviour.registration_in_progress is False

        mock_logger.assert_any_call(
            logging.INFO,
            "the agent, with its genus and classification, and its service are successfully registered on the SOEF.",
        )

    def test_handle_success_v(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets unregister_service."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_search_dialogues,
            messages=self.list_of_messages_register_invalid[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_logger.assert_any_call(
            logging.WARNING,
            f"received soef SUCCESS message as a reply to the following unexpected message: {oef_dialogue.get_message_by_id(incoming_message.target)}",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the oef_search handler."""
        # setup
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message(
                message_type=OefSearchMessage,
                performative=OefSearchMessage.Performative.REGISTER_SERVICE,
                service_description=self.mocked_proposal,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle oef_search message of performative={incoming_message.performative} in dialogue={self.oef_search_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the oef_search handler."""
        assert self.oef_search_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
