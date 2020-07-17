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

"""This module contains tests for decision_maker."""

from queue import Queue
from typing import Optional, cast
from unittest import mock

import eth_account

from fetchai.ledger.api.token import TokenTxFactory
from fetchai.ledger.crypto import Address as FetchaiAddress
from fetchai.ledger.transaction import Transaction as FetchaiTransaction

import pytest

import aea
import aea.decision_maker.default
from aea.configurations.base import PublicId
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.decision_maker.default import DecisionMakerHandler
from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.helpers.transaction.base import (
    RawMessage,
    RawTransaction,
    SignedMessage,
    Terms,
)
from aea.identity.base import Identity
from aea.protocols.base import Message
from aea.protocols.signing.dialogues import SigningDialogue
from aea.protocols.signing.dialogues import SigningDialogues as BaseSigningDialogues
from aea.protocols.signing.message import SigningMessage
from aea.protocols.state_update.dialogues import StateUpdateDialogue
from aea.protocols.state_update.dialogues import (
    StateUpdateDialogues as BaseStateUpdateDialogues,
)
from aea.protocols.state_update.message import StateUpdateMessage

from tests.conftest import (
    COSMOS,
    COSMOS_PRIVATE_KEY_PATH,
    ETHEREUM,
    ETHEREUM_PRIVATE_KEY_PATH,
    FETCHAI,
    FETCHAI_PRIVATE_KEY_PATH,
)


class SigningDialogues(BaseSigningDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, agent_address: str) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        BaseSigningDialogues.__init__(self, agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return SigningDialogue.Role.SKILL

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> SigningDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = SigningDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue


class StateUpdateDialogues(BaseStateUpdateDialogues):
    """This class keeps track of all oef_search dialogues."""

    def __init__(self, agent_address: str) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        BaseStateUpdateDialogues.__init__(self, agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return StateUpdateDialogue.Role.DECISION_MAKER

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> StateUpdateDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = StateUpdateDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue


class TestDecisionMaker:
    """Test the decision maker."""

    @classmethod
    def _patch_logger(cls):
        cls.patch_logger_warning = mock.patch.object(
            aea.decision_maker.default.logger, "warning"
        )
        cls.mocked_logger_warning = cls.patch_logger_warning.__enter__()

    @classmethod
    def _unpatch_logger(cls):
        cls.mocked_logger_warning.__exit__()

    @classmethod
    def setup_class(cls):
        """Initialise the decision maker."""
        cls._patch_logger()
        cls.wallet = Wallet(
            {
                COSMOS: COSMOS_PRIVATE_KEY_PATH,
                ETHEREUM: ETHEREUM_PRIVATE_KEY_PATH,
                FETCHAI: FETCHAI_PRIVATE_KEY_PATH,
            }
        )
        cls.agent_name = "test"
        cls.identity = Identity(
            cls.agent_name, addresses=cls.wallet.addresses, default_address_key=COSMOS,
        )
        cls.decision_maker_handler = DecisionMakerHandler(
            identity=cls.identity, wallet=cls.wallet
        )
        cls.decision_maker = DecisionMaker(cls.decision_maker_handler)

        cls.tx_sender_addr = "agent_1"
        cls.tx_counterparty_addr = "pk"
        cls.info = {"some_info_key": "some_info_value"}
        cls.ledger_id = FETCHAI

        cls.decision_maker.start()

    def test_properties(self):
        """Test the properties of the decision maker."""
        assert isinstance(self.decision_maker.message_in_queue, Queue)
        assert isinstance(self.decision_maker.message_out_queue, Queue)

    def test_decision_maker_handle_state_update_initialize_and_apply(self):
        """Test the handle method for a stateUpdate message with Initialize and Apply performative."""
        good_holdings = {"good_id": 2}
        currency_holdings = {"FET": 100}
        utility_params = {"good_id": 20.0}
        exchange_params = {"FET": 10.0}
        currency_deltas = {"FET": -10}
        good_deltas = {"good_id": 1}

        state_update_dialogues = StateUpdateDialogues("agent")
        state_update_message_1 = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.INITIALIZE,
            dialogue_reference=state_update_dialogues.new_self_initiated_dialogue_reference(),
            amount_by_currency_id=currency_holdings,
            quantities_by_good_id=good_holdings,
            exchange_params_by_currency_id=exchange_params,
            utility_params_by_good_id=utility_params,
        )
        state_update_message_1.counterparty = "decision_maker"
        state_update_dialogue = cast(
            Optional[StateUpdateDialogue],
            state_update_dialogues.update(state_update_message_1),
        )
        assert state_update_dialogue is not None, "StateUpdateDialogue not created"
        self.decision_maker.handle(state_update_message_1)
        assert (
            self.decision_maker_handler.context.ownership_state.amount_by_currency_id
            is not None
        )
        assert (
            self.decision_maker_handler.context.ownership_state.quantities_by_good_id
            is not None
        )
        assert (
            self.decision_maker_handler.context.preferences.exchange_params_by_currency_id
            is not None
        )
        assert (
            self.decision_maker_handler.context.preferences.utility_params_by_good_id
            is not None
        )

        state_update_message_2 = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.APPLY,
            dialogue_reference=state_update_dialogue.dialogue_label.dialogue_reference,
            message_id=state_update_message_1.message_id + 1,
            target=state_update_message_1.message_id,
            amount_by_currency_id=currency_deltas,
            quantities_by_good_id=good_deltas,
        )
        state_update_message_2.counterparty = "decision_maker"
        state_update_dialogue.update(state_update_message_2)
        self.decision_maker.handle(state_update_message_2)
        expected_amount_by_currency_id = {
            key: currency_holdings.get(key, 0) + currency_deltas.get(key, 0)
            for key in set(currency_holdings) | set(currency_deltas)
        }
        expected_quantities_by_good_id = {
            key: good_holdings.get(key, 0) + good_deltas.get(key, 0)
            for key in set(good_holdings) | set(good_deltas)
        }
        assert (
            self.decision_maker_handler.context.ownership_state.amount_by_currency_id
            == expected_amount_by_currency_id
        ), "The amount_by_currency_id must be equal with the expected amount."
        assert (
            self.decision_maker_handler.context.ownership_state.quantities_by_good_id
            == expected_quantities_by_good_id
        )

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        cls._unpatch_logger()
        cls.decision_maker.stop()


class TestDecisionMaker2:
    """Test the decision maker."""

    @classmethod
    def _patch_logger(cls):
        cls.patch_logger_warning = mock.patch.object(
            aea.decision_maker.default.logger, "warning"
        )
        cls.mocked_logger_warning = cls.patch_logger_warning.__enter__()

    @classmethod
    def _unpatch_logger(cls):
        cls.mocked_logger_warning.__exit__()

    @classmethod
    def setup_class(cls):
        """Initialise the decision maker."""
        cls._patch_logger()
        cls.wallet = Wallet(
            {
                COSMOS: COSMOS_PRIVATE_KEY_PATH,
                ETHEREUM: ETHEREUM_PRIVATE_KEY_PATH,
                FETCHAI: FETCHAI_PRIVATE_KEY_PATH,
            }
        )
        cls.agent_name = "test"
        cls.identity = Identity(
            cls.agent_name, addresses=cls.wallet.addresses, default_address_key=COSMOS,
        )
        cls.decision_maker_handler = DecisionMakerHandler(
            identity=cls.identity, wallet=cls.wallet
        )
        cls.decision_maker = DecisionMaker(cls.decision_maker_handler)

        cls.tx_sender_addr = "agent_1"
        cls.tx_counterparty_addr = "pk"
        cls.info = {"some_info_key": "some_info_value"}
        cls.ledger_id = FETCHAI

        cls.decision_maker.start()

    def test_decision_maker_execute_w_wrong_input(self):
        """Test the execute method with wrong input."""
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.put_nowait("wrong input")
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.put("wrong input")

    def test_decision_maker_queue_access_not_permitted(self):
        """Test the in queue of the decision maker can not be accessed."""
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.get()
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.get_nowait()
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.protected_get(
                access_code="some_invalid_code"
            )

    def test_handle_tx_signing_fetchai(self):
        """Test tx signing for fetchai."""
        tx = TokenTxFactory.transfer(
            FetchaiAddress("v3sZs7gKKz9xmoTo9yzRkfHkjYuX42MzXaq4eVjGHxrX9qu3U"),
            FetchaiAddress("2bzQNV4TTjMAiKZe85EyLUttoFpHHuksRzUUBYB1brt98pMXKK"),
            1,
            1,
            [],
        )
        signing_dialogues = SigningDialogues("agent1")
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            skill_callback_ids=(str(PublicId("author", "a_skill", "0.1.0")),),
            skill_callback_info={},
            terms=Terms(
                ledger_id=FETCHAI,
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_transaction=RawTransaction(FETCHAI, tx),
        )
        signing_msg.counterparty = "decision_maker"
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert (
            signing_msg_response.performative
            == SigningMessage.Performative.SIGNED_TRANSACTION
        )
        assert signing_msg_response.skill_callback_ids == signing_msg.skill_callback_ids
        assert type(signing_msg_response.signed_transaction.body) == FetchaiTransaction

    def test_handle_tx_signing_ethereum(self):
        """Test tx signing for ethereum."""
        tx = {"gasPrice": 30, "nonce": 1, "gas": 20000}
        signing_dialogues = SigningDialogues("agent2")
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            skill_callback_ids=(str(PublicId("author", "a_skill", "0.1.0")),),
            skill_callback_info={},
            terms=Terms(
                ledger_id=ETHEREUM,
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_transaction=RawTransaction(ETHEREUM, tx),
        )
        signing_msg.counterparty = "decision_maker"
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert (
            signing_msg_response.performative
            == SigningMessage.Performative.SIGNED_TRANSACTION
        )
        assert signing_msg_response.skill_callback_ids == signing_msg.skill_callback_ids
        assert (
            type(signing_msg_response.signed_transaction.body)
            == eth_account.datastructures.AttributeDict
        )

    def test_handle_tx_signing_unknown(self):
        """Test tx signing for unknown."""
        tx = {}
        signing_dialogues = SigningDialogues("agent3")
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            skill_callback_ids=(str(PublicId("author", "a_skill", "0.1.0")),),
            skill_callback_info={},
            terms=Terms(
                ledger_id="unknown",
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_transaction=RawTransaction("unknown", tx),
        )
        signing_msg.counterparty = "decision_maker"
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert signing_msg_response.performative == SigningMessage.Performative.ERROR
        assert signing_msg_response.skill_callback_ids == signing_msg.skill_callback_ids
        assert (
            signing_msg_response.error_code
            == SigningMessage.ErrorCode.UNSUCCESSFUL_TRANSACTION_SIGNING
        )

    def test_handle_message_signing_fetchai(self):
        """Test message signing for fetchai."""
        message = b"0x11f3f9487724404e3a1fb7252a322656b90ba0455a2ca5fcdcbe6eeee5f8126d"
        signing_dialogues = SigningDialogues("agent4")
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            skill_callback_ids=(str(PublicId("author", "a_skill", "0.1.0")),),
            skill_callback_info={},
            terms=Terms(
                ledger_id=FETCHAI,
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_message=RawMessage(FETCHAI, message),
        )
        signing_msg.counterparty = "decision_maker"
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert (
            signing_msg_response.performative
            == SigningMessage.Performative.SIGNED_MESSAGE
        )
        assert signing_msg_response.skill_callback_ids == signing_msg.skill_callback_ids
        assert type(signing_msg_response.signed_message) == SignedMessage

    def test_handle_message_signing_ethereum(self):
        """Test message signing for ethereum."""
        message = b"0x11f3f9487724404e3a1fb7252a322656b90ba0455a2ca5fcdcbe6eeee5f8126d"
        signing_dialogues = SigningDialogues("agent4")
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            skill_callback_ids=(str(PublicId("author", "a_skill", "0.1.0")),),
            skill_callback_info={},
            terms=Terms(
                ledger_id=ETHEREUM,
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_message=RawMessage(ETHEREUM, message),
        )
        signing_msg.counterparty = "decision_maker"
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert (
            signing_msg_response.performative
            == SigningMessage.Performative.SIGNED_MESSAGE
        )
        assert signing_msg_response.skill_callback_ids == signing_msg.skill_callback_ids
        assert type(signing_msg_response.signed_message) == SignedMessage

    def test_handle_message_signing_ethereum_deprecated(self):
        """Test message signing for ethereum deprecated."""
        message = b"0x11f3f9487724404e3a1fb7252a3226"
        signing_dialogues = SigningDialogues("agent5")
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            skill_callback_ids=(str(PublicId("author", "a_skill", "0.1.0")),),
            skill_callback_info={},
            terms=Terms(
                ledger_id=ETHEREUM,
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_message=RawMessage(ETHEREUM, message, is_deprecated_mode=True),
        )
        signing_msg.counterparty = "decision_maker"
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert (
            signing_msg_response.performative
            == SigningMessage.Performative.SIGNED_MESSAGE
        )
        assert signing_msg_response.skill_callback_ids == signing_msg.skill_callback_ids
        assert type(signing_msg_response.signed_message) == SignedMessage
        assert signing_msg_response.signed_message.is_deprecated_mode

    def test_handle_message_signing_unknown(self):
        """Test message signing for unknown."""
        message = b"0x11f3f9487724404e3a1fb7252a322656b90ba0455a2ca5fcdcbe6eeee5f8126d"
        signing_dialogues = SigningDialogues("agent6")
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            skill_callback_ids=(str(PublicId("author", "a_skill", "0.1.0")),),
            skill_callback_info={},
            terms=Terms(
                ledger_id="unknown",
                sender_address="pk1",
                counterparty_address="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            raw_message=RawMessage("unknown", message),
        )
        signing_msg.counterparty = "decision_maker"
        self.decision_maker.message_in_queue.put_nowait(signing_msg)
        signing_msg_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert signing_msg_response.performative == SigningMessage.Performative.ERROR
        assert signing_msg_response.skill_callback_ids == signing_msg.skill_callback_ids
        assert (
            signing_msg_response.error_code
            == SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING
        )

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        cls._unpatch_logger()
        cls.decision_maker.stop()
