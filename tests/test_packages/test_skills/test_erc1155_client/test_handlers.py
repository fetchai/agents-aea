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
"""This module contains the tests of the handler classes of the erc1155_client skill."""

import logging
from typing import cast
from unittest.mock import patch

from aea.helpers.search.models import Description
from aea.helpers.transaction.base import RawMessage, State, Terms
from aea.test_tools.test_skill import COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.erc1155_client.dialogues import (
    ContractApiDialogue,
    FipaDialogue,
    LedgerApiDialogue,
    OefSearchDialogue,
    SigningDialogue,
)
from packages.fetchai.skills.erc1155_client.handlers import LEDGER_API_ADDRESS

from tests.test_packages.test_skills.test_erc1155_client.intermediate_class import (
    ERC1155ClientTestCase,
)


class TestFipaHandler(ERC1155ClientTestCase):
    """Test fipa handler of erc1155_client."""

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
            logging.INFO, f"unidentified dialogue for message={incoming_message}.",
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

    def test_handle_propose_i(self):
        """Test the _handle_propose method of the fipa handler where all expected keys exist in the proposal."""
        # setup
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues, messages=self.list_of_fipa_messages[:1],
            ),
        )
        incoming_message = cast(
            FipaMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=fipa_dialogue,
                performative=FipaMessage.Performative.PROPOSE,
                proposal=self.mocked_proposal,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received valid PROPOSE from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}: proposal={incoming_message.proposal.values}",
        )

        self.assert_quantity_in_outbox(1)
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_RAW_MESSAGE,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            ledger_id=self.strategy.ledger_id,
            contract_id=self.strategy.contract_id,
            contract_address=incoming_message.proposal.values["contract_address"],
            callable="get_hash_single",
            kwargs=ContractApiMessage.Kwargs(
                {
                    "from_address": incoming_message.sender,
                    "to_address": self.skill.skill_context.agent_address,
                    "token_id": int(incoming_message.proposal.values["token_id"]),
                    "from_supply": int(incoming_message.proposal.values["from_supply"]),
                    "to_supply": int(incoming_message.proposal.values["to_supply"]),
                    "value": int(incoming_message.proposal.values["value"]),
                    "trade_nonce": int(incoming_message.proposal.values["trade_nonce"]),
                }
            ),
        )
        assert has_attributes, error_str

        contract_api_dialogue = cast(
            ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
        )

        expected_terms = Terms(
            ledger_id=self.strategy.ledger_id,
            sender_address=self.skill.skill_context.agent_address,
            counterparty_address=incoming_message.sender,
            amount_by_currency_id={},
            quantities_by_good_id={
                str(incoming_message.proposal.values["token_id"]): int(
                    incoming_message.proposal.values["from_supply"]
                )
                - int(incoming_message.proposal.values["to_supply"])
            },
            is_sender_payable_tx_fee=False,
            nonce=str(incoming_message.proposal.values["trade_nonce"]),
        )
        assert contract_api_dialogue.terms == expected_terms
        assert contract_api_dialogue.associated_fipa_dialogue == fipa_dialogue

        mock_logger.assert_any_call(
            logging.INFO, "requesting single hash message from contract api...",
        )

    def test_handle_propose_ii(self):
        """Test the _handle_propose method of the fipa handler where some expected keys do NOT exist in the proposal."""
        # setup
        invalid_proposal = Description({"some_key": "v1", "some_key_2": "12"})

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues, messages=self.list_of_fipa_messages[:1],
            ),
        )
        incoming_message = cast(
            FipaMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=fipa_dialogue,
                performative=FipaMessage.Performative.PROPOSE,
                proposal=invalid_proposal,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.fipa_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid PROPOSE from sender={COUNTERPARTY_AGENT_ADDRESS[-5:]}: proposal={incoming_message.proposal.values}",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the fipa handler."""
        # setup
        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues, messages=self.list_of_fipa_messages[:2],
            ),
        )
        incoming_message = cast(
            FipaMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=fipa_dialogue, performative=FipaMessage.Performative.ACCEPT,
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


class TestOefSearchHandler(ERC1155ClientTestCase):
    """Test oef_search handler of erc1155_client."""

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
                messages=self.list_of_oef_search_messages[:1],
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

    def test_handle_search_i(self):
        """Test the _handle_search method of the oef_search handler where the number of agents found is NOT 0."""
        # setup
        agents = ("agent_1", "agent_2")
        oef_search_dialogue = cast(
            OefSearchDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.oef_search_dialogues,
                messages=self.list_of_oef_search_messages[:1],
            ),
        )
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_search_dialogue,
                performative=OefSearchMessage.Performative.SEARCH_RESULT,
                agents=agents,
                agents_info=OefSearchMessage.AgentsInfo(
                    {
                        "agent_1": {"key_1": "value_1", "key_2": "value_2"},
                        "agent_2": {"key_3": "value_3", "key_4": "value_4"},
                    }
                ),
            ),
        )

        # before
        assert self.strategy.is_searching is True

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"found agents={list(map(lambda x: x[-5:], incoming_message.agents))}, stopping search.",
        )

        assert self.strategy.is_searching is False

        self.assert_quantity_in_outbox(len(agents))
        for agent in agents:
            has_attributes, error_str = self.message_has_attributes(
                actual_message=self.get_message_from_outbox(),
                message_type=FipaMessage,
                performative=FipaMessage.Performative.CFP,
                to=agent,
                sender=self.skill.skill_context.agent_address,
                query=self.strategy.get_service_query(),
            )
            assert has_attributes, error_str
            mock_logger.assert_any_call(
                logging.INFO, f"sending CFP to agent={agent[-5:]}"
            )

    def test_handle_search_ii(self):
        """Test the _handle_search method of the oef_search handler where the number of agents found is 0."""
        # setup
        agents = tuple()
        oef_search_dialogue = cast(
            OefSearchDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.oef_search_dialogues,
                messages=self.list_of_oef_search_messages[:1],
            ),
        )
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_search_dialogue,
                performative=OefSearchMessage.Performative.SEARCH_RESULT,
                agents=agents,
                agents_info=OefSearchMessage.AgentsInfo({}),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"found no agents in dialogue={oef_search_dialogue}, continue searching.",
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


class TestContractApiHandler(ERC1155ClientTestCase):
    """Test contract_api handler of erc1155_client."""

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
                state=State(self.ledger_id, self.body),
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

    def test_handle_raw_message(self):
        """Test the _handle_raw_message method of the signing handler."""
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
                performative=ContractApiMessage.Performative.RAW_MESSAGE,
                raw_message=self.mocked_raw_msg,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"received raw message={incoming_message}"
        )

        self.assert_quantity_in_decision_making_queue(1)
        message = self.get_message_from_decision_maker_inbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=SigningMessage,
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            raw_message=RawMessage(
                incoming_message.raw_message.ledger_id,
                incoming_message.raw_message.body,
                is_deprecated_mode=True,
            ),
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


class TestSigningHandler(ERC1155ClientTestCase):
    """Test signing handler of erc1155_client."""

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

    def test_handle_signed_message(self,):
        """Test the _handle_signed_message method of the signing handler."""
        # setup
        signing_counterparty = self.skill.skill_context.decision_maker_address

        fipa_dialogue = cast(
            FipaDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.fipa_dialogues,
                messages=self.list_of_fipa_messages[:2],
                counterparty=COUNTERPARTY_AGENT_ADDRESS,
            ),
        )
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:1],
                counterparty=signing_counterparty,
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
        contract_api_dialogue.associated_fipa_dialogue = fipa_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_MESSAGE,
                signed_message=SigningMessage.SignedMessage(
                    self.ledger_id, "some_body",
                ),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        fipa_dialogue_opponent = fipa_dialogue.dialogue_label.dialogue_opponent_addr
        mock_logger.assert_any_call(
            logging.INFO,
            f"sending ACCEPT_W_INFORM to agent={fipa_dialogue_opponent[-5:]}: tx_signature={incoming_message.signed_message}",
        )

        self.assert_quantity_in_outbox(1)
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=FipaMessage,
            performative=FipaMessage.Performative.ACCEPT_W_INFORM,
            to=fipa_dialogue_opponent,
            sender=self.skill.skill_context.agent_address,
            info={"tx_signature": incoming_message.signed_message.body},
        )
        assert has_attributes, error_str

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


class TestLedgerApiHandler(ERC1155ClientTestCase):
    """Test ledger_api handler of erc1155_client."""

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
                messages=self.list_of_ledger_api_messages[:1],
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

    def test_handle_error(self):
        """Test the _handle_error method of the ledger_api handler."""
        # setup
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:1],
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
