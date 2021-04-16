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
"""This module contains the tests of the handler classes of the confirmation aw1 skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import PropertyMock, patch

import pytest

from aea.crypto.ledger_apis import LedgerApis
from aea.helpers.transaction.base import (
    RawTransaction,
    SignedTransaction,
    Terms,
    TransactionDigest,
    TransactionReceipt,
)
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.contract_api.custom_types import Kwargs, State
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.register.message import RegisterMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.confirmation_aw1.behaviours import TransactionBehaviour
from packages.fetchai.skills.confirmation_aw1.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    RegisterDialogue,
    RegisterDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.confirmation_aw1.handlers import (
    AW1RegistrationHandler,
    ContractApiHandler,
    LEDGER_API_ADDRESS,
    LedgerApiHandler,
    SigningHandler,
)
from packages.fetchai.skills.confirmation_aw1.strategy import Strategy

from tests.conftest import ROOT_DIR


class TestAW1RegistrationHandler(BaseSkillTestCase):
    """Test registration handler of confirmation aw1."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw1")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.register_handler = cast(
            AW1RegistrationHandler, cls._skill.skill_context.handlers.registration
        )
        cls.logger = cls._skill.skill_context.logger
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)

        cls.tx_behaviour = cast(
            TransactionBehaviour, cls._skill.skill_context.behaviours.transaction
        )

        cls.register_dialogues = cast(
            RegisterDialogues, cls._skill.skill_context.register_dialogues
        )
        cls.contract_api_dialogues = cast(
            ContractApiDialogues, cls._skill.skill_context.contract_api_dialogues
        )

        cls.info = {"ethereum_address": "some_ethereum_address"}
        cls.kwargs = {"address": "some_ethereum_address"}
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
        cls.list_of_registration_messages = (
            DialogueMessage(RegisterMessage.Performative.REGISTER, {"info": cls.info}),
        )

    def test_setup(self):
        """Test the setup method of the fipa handler."""
        assert self.register_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the register handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=RegisterMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=RegisterMessage.Performative.REGISTER,
            info=self.info,
        )

        # operation
        with patch.object(self.register_handler.context.logger, "log") as mock_logger:
            self.register_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid register_msg message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_register_is_valid_i(self):
        """Test the _handle_register method of the register handler where is_valid is True and NOT in developer_only_mode."""
        # setup
        incoming_message = cast(
            RegisterMessage,
            self.build_incoming_message(
                message_type=RegisterMessage,
                performative=RegisterMessage.Performative.REGISTER,
                info=self.info,
            ),
        )

        # operation
        with patch.object(
            self.strategy, "valid_registration", return_value=(True, 0, "all good!"),
        ) as mock_valid:
            with patch.object(
                self.strategy, "lock_registration_temporarily"
            ) as mock_lock:
                with patch.object(
                    self.strategy, "get_kwargs", return_value=self.kwargs
                ) as mock_kwargs:
                    with patch.object(
                        self.strategy, "get_terms", return_value=self.terms
                    ) as mock_terms:
                        with patch.object(self.logger, "log") as mock_logger:
                            self.register_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_valid.called_once()
        mock_lock.called_once()
        mock_kwargs.called_once()
        mock_terms.called_once()

        mock_logger.assert_any_call(
            logging.INFO,
            f"valid registration={incoming_message.info}. Verifying if tokens staked.",
        )

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=ContractApiMessage,
            performative=ContractApiMessage.Performative.GET_STATE,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            contract_id=self.strategy.contract_id,
            contract_address=self.strategy.contract_address,
            callable=self.strategy.contract_callable,
            kwargs=ContractApiMessage.Kwargs(self.kwargs),
        )
        assert has_attributes, error_str

        contract_api_dialogue = cast(
            ContractApiDialogue, self.contract_api_dialogues.get_dialogue(message)
        )
        register_dialogue = cast(
            RegisterDialogue, self.register_dialogues.get_dialogue(incoming_message)
        )

        assert contract_api_dialogue.terms == self.terms
        assert contract_api_dialogue.associated_register_dialogue == register_dialogue

    def test_handle_register_is_valid_ii(self):
        """Test the _handle_register method of the register handler where is_valid is True and IN developer_only_mode."""
        # setup
        self.strategy.developer_handle_only = True

        incoming_message = cast(
            RegisterMessage,
            self.build_incoming_message(
                message_type=RegisterMessage,
                performative=RegisterMessage.Performative.REGISTER,
                info=self.info,
            ),
        )

        # operation
        with patch.object(
            self.strategy, "valid_registration", return_value=(True, 0, "all good!"),
        ) as mock_valid:
            with patch.object(
                self.strategy, "lock_registration_temporarily"
            ) as mock_lock:
                with patch.object(
                    self.strategy, "get_terms", return_value=self.terms
                ) as mock_terms:
                    with patch.object(
                        self.strategy, "finalize_registration"
                    ) as mock_finalize:
                        with patch.object(self.logger, "log") as mock_logger:
                            self.register_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_valid.called_once()
        mock_lock.called_once()
        mock_terms.called_once()

        mock_logger.assert_any_call(
            logging.INFO,
            f"valid registration={incoming_message.info}. Verifying if tokens staked.",
        )

        mock_finalize.assert_called_once()
        register_dialogue = cast(
            RegisterDialogue, self.register_dialogues.get_dialogue(incoming_message)
        )
        assert register_dialogue.terms == self.terms
        assert register_dialogue in self.tx_behaviour.waiting

    def test_handle_register_is_not_valid(self):
        """Test the _handle_register method of the register handler where is_valid is False."""
        # setup
        incoming_message = cast(
            RegisterMessage,
            self.build_incoming_message(
                message_type=RegisterMessage,
                performative=RegisterMessage.Performative.REGISTER,
                info=self.info,
            ),
        )

        error_code = 1
        error_msg = "already registered!"

        # operation
        with patch.object(
            self.strategy,
            "valid_registration",
            return_value=(False, error_code, error_msg),
        ) as mock_valid:
            with patch.object(self.logger, "log") as mock_logger:
                self.register_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_valid.called_once()

        mock_logger.assert_any_call(
            logging.INFO, f"invalid registration={incoming_message.info}. Rejecting.",
        )

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=RegisterMessage,
            performative=RegisterMessage.Performative.ERROR,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            error_code=error_code,
            error_msg=error_msg,
            info={},
        )
        assert has_attributes, error_str

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the fipa handler."""
        # setup
        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_registration_messages[:1],
            ),
        )
        incoming_message = cast(
            RegisterMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=register_dialogue,
                performative=RegisterMessage.Performative.SUCCESS,
                info=self.info,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.register_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle register_msg message of performative={incoming_message.performative} in dialogue={register_dialogue}.",
        )

    def test_teardown(self):
        """Test the teardown method of the fipa handler."""
        assert self.register_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestContractApiHandler(BaseSkillTestCase):
    """Test contract_api handler of confirmation aw1."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw1")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.contract_api_handler = cast(
            ContractApiHandler, cls._skill.skill_context.handlers.contract_api
        )
        cls.tx_behaviour = cast(
            TransactionBehaviour, cls._skill.skill_context.behaviours.transaction
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.logger = cls.contract_api_handler.context.logger

        cls.contract_api_dialogues = cast(
            ContractApiDialogues, cls._skill.skill_context.contract_api_dialogues
        )
        cls.register_dialogues = cast(
            RegisterDialogues, cls._skill.skill_context.register_dialogues
        )

        cls.ledger_id = "some_ledger_id"
        cls.contract_id = "some_contract_id"
        cls.contract_address = "some_contract_address,"
        cls.callable = "some_callable"
        cls.kwargs = Kwargs({"some_key": "some_value"})

        cls.state = State("some_ledger_id", {"some_key": "some_value"})

        cls.list_of_contract_api_messages = (
            DialogueMessage(
                ContractApiMessage.Performative.GET_STATE,
                {
                    "ledger_id": cls.ledger_id,
                    "contract_id": cls.contract_id,
                    "contract_address": cls.contract_address,
                    "callable": cls.callable,
                    "kwargs": cls.kwargs,
                },
            ),
        )
        cls.info = {"ethereum_address": "some_ethereum_address"}
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
        cls.list_of_registration_messages = (
            DialogueMessage(
                RegisterMessage.Performative.REGISTER,
                {"info": cls.info},
                is_incoming=True,
            ),
        )

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

    def test_handle_state_staked(self,):
        """Test the _handle_state method of the contract_api handler where has_staked is True."""
        # setup
        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_registration_messages[:1],
                is_agent_to_agent_messages=True,
            ),
        )

        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:1],
            ),
        )
        contract_api_dialogue.associated_register_dialogue = register_dialogue
        contract_api_dialogue.terms = self.terms

        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=contract_api_dialogue,
            performative=ContractApiMessage.Performative.STATE,
            state=self.state,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(self.strategy, "has_staked", return_value=True):
                with patch.object(
                    self.strategy, "finalize_registration"
                ) as mock_finalize:
                    self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"received state message={incoming_message}"
        )

        mock_logger.assert_any_call(
            logging.INFO, "Has staked! Requesting funds release."
        )

        mock_finalize.assert_called_once()

        assert register_dialogue.terms == contract_api_dialogue.terms

        assert register_dialogue in self.tx_behaviour.waiting

    def test_handle_state_not_staked(self,):
        """Test the _handle_state method of the contract_api handler where has_staked is False."""
        # setup
        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_registration_messages[:1],
                is_agent_to_agent_messages=True,
            ),
        )

        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:1],
            ),
        )
        contract_api_dialogue.associated_register_dialogue = register_dialogue
        contract_api_dialogue.terms = self.terms

        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=contract_api_dialogue,
            performative=ContractApiMessage.Performative.STATE,
            state=self.state,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(self.strategy, "has_staked", return_value=False):
                with patch.object(self.strategy, "unlock_registration") as mock_unlock:
                    self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"received state message={incoming_message}"
        )

        mock_unlock.assert_called_once()

        mock_logger.assert_any_call(
            logging.INFO,
            f"invalid registration={cast(RegisterMessage, register_dialogue.last_incoming_message).info}. Rejecting.",
        )

        self.assert_quantity_in_outbox(1)
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=RegisterMessage,
            performative=RegisterMessage.Performative.ERROR,
            to=register_dialogue.dialogue_label.dialogue_opponent_addr,
            sender=self.skill.skill_context.agent_address,
            error_code=1,
            error_msg="No funds staked!",
            info={},
        )
        assert has_attributes, error_str

    def test_handle_state_register_msg_is_none(self,):
        """Test the _handle_state method of the contract_api handler where register_msg is None."""
        # setup
        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_registration_messages[:1],
                is_agent_to_agent_messages=True,
            ),
        )
        register_dialogue._incoming_messages = []

        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:1],
            ),
        )
        contract_api_dialogue.associated_register_dialogue = register_dialogue
        contract_api_dialogue.terms = self.terms

        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=contract_api_dialogue,
            performative=ContractApiMessage.Performative.STATE,
            state=self.state,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with pytest.raises(ValueError, match="Could not retrieve fipa message"):
                self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"received state message={incoming_message}"
        )

    def test_handle_error_i(self):
        """Test the _handle_error method of the contract_api handler."""
        # setup
        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_registration_messages[:1],
                is_agent_to_agent_messages=True,
            ),
        )

        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:1],
            ),
        )
        contract_api_dialogue.associated_register_dialogue = register_dialogue
        contract_api_dialogue.terms = self.terms

        incoming_message = cast(
            ContractApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=contract_api_dialogue,
                performative=ContractApiMessage.Performative.ERROR,
                data=b"some_data",
            ),
        )

        # operation
        with patch.object(self.strategy, "unlock_registration") as mock_unlock:
            with patch.object(self.logger, "log") as mock_logger:
                self.contract_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received ledger_api error message={incoming_message} in dialogue={contract_api_dialogue}.",
        )

        mock_unlock.assert_called_once()

    def test_handle_error_ii(self):
        """Test the _handle_error method of the contract_api handler where register_dialogue's last incoming message is None."""
        # setup
        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_registration_messages[:1],
                is_agent_to_agent_messages=True,
            ),
        )
        register_dialogue._incoming_messages = []

        contract_api_dialogue = cast(
            ContractApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.contract_api_dialogues,
                messages=self.list_of_contract_api_messages[:1],
            ),
        )
        contract_api_dialogue.associated_register_dialogue = register_dialogue
        contract_api_dialogue.terms = self.terms

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
            with pytest.raises(ValueError, match="Could not retrieve fipa message"):
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
    """Test signing handler of confirmation aw1."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw1")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.signing_handler = cast(
            SigningHandler, cls._skill.skill_context.handlers.signing
        )
        cls.tx_behaviour = cast(
            TransactionBehaviour, cls._skill.skill_context.behaviours.transaction
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.logger = cls._skill.skill_context.logger

        cls.register_dialogues = cast(
            RegisterDialogue, cls._skill.skill_context.register_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )
        cls.terms = Terms(
            "some_ledger_id",
            cls._skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )

        cls.info = {"ethereum_address": "some_ethereum_address"}
        cls.list_of_registration_messages = (
            DialogueMessage(
                RegisterMessage.Performative.REGISTER,
                {"info": cls.info},
                is_incoming=True,
            ),
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

        cls.list_of_ledger_api_messages = (
            DialogueMessage(LedgerApiMessage.Performative.GET_RAW_TRANSACTION, {}),
            DialogueMessage(LedgerApiMessage.Performative.RAW_TRANSACTION, {}),
            DialogueMessage(LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION, {}),
            DialogueMessage(LedgerApiMessage.Performative.TRANSACTION_DIGEST, {}),
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

    def test_handle_signed_transaction_last_ledger_api_message_is_none(self,):
        """Test the _handle_signed_transaction method of the signing handler."""
        # setup
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:1],
            ),
        )
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:2],
            ),
        )
        signing_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
        signing_dialogue.associated_ledger_api_dialogue._incoming_messages = []
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=signing_dialogue,
            performative=SigningMessage.Performative.SIGNED_TRANSACTION,
            signed_transaction=SigningMessage.SignedTransaction(
                "some_ledger_id", {"some_key": "some_value"}
            ),
        )

        # operation
        with pytest.raises(
            ValueError, match="Could not retrieve last message in ledger api dialogue"
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.INFO, "transaction signing was successful.")

    def test_handle_signed_transaction_last_ledger_api_message_is_not_none(self,):
        """Test the _handle_signed_transaction method of the signing handler where the last ledger_api message is not None."""
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
        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:2],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        signing_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
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
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.skill_context.skill_id),
            signed_transaction=incoming_message.signed_transaction,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(logging.INFO, "sending transaction to ledger.")

    def test_handle_error(self):
        """Test the _handle_error method of the signing handler."""
        # setup
        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_registration_messages[:1],
                counterparty=COUNTERPARTY_AGENT_ADDRESS,
                is_agent_to_agent_messages=True,
            ),
        )

        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:4],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        ledger_api_dialogue.associated_register_dialogue = register_dialogue

        signing_counterparty = self.skill.skill_context.decision_maker_address
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_messages[:1],
                counterparty=signing_counterparty,
            ),
        )
        signing_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.ERROR,
                error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_TRANSACTION_SIGNING,
            ),
        )

        # operation
        with patch.object(self.tx_behaviour, "failed_processing"):
            with patch.object(self.logger, "log") as mock_logger:
                self.signing_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction signing was not successful. Error_code={incoming_message.error_code} in dialogue={signing_dialogue}",
        )

        # finish_processing
        assert self.tx_behaviour.processing_time == 0.0
        assert self.tx_behaviour.processing is None

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


class TestGenericLedgerApiHandler(BaseSkillTestCase):
    """Test ledger_api handler of confirmation aw1."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw1")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.ledger_api_handler = cast(
            LedgerApiHandler, cls._skill.skill_context.handlers.ledger_api
        )
        cls.transaction_behaviour = cast(
            TransactionBehaviour, cls._skill.skill_context.behaviours.transaction
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.logger = cls._skill.skill_context.logger

        cls.register_dialogues = cast(
            RegisterDialogue, cls._skill.skill_context.register_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )

        cls.terms = Terms(
            "some_ledger_id",
            cls._skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        cls.info = {"ethereum_address": "some_ethereum_address"}
        cls.list_of_registration_messages = (
            DialogueMessage(
                RegisterMessage.Performative.REGISTER,
                {"info": cls.info},
                is_incoming=True,
            ),
        )

        cls.raw_transaction = RawTransaction(
            "some_ledger_id", {"some_key": "some_value"}
        )
        cls.signed_transaction = SignedTransaction(
            "some_ledger_id", {"some_key": "some_value"}
        )
        cls.transaction_digest = TransactionDigest("some_ledger_id", "some_body")
        cls.transaction_receipt = TransactionReceipt(
            "some_ledger_id",
            {"receipt_key": "receipt_value"},
            {"transaction_key": "transaction_value"},
        )
        cls.list_of_ledger_api_messages = (
            DialogueMessage(
                LedgerApiMessage.Performative.GET_RAW_TRANSACTION, {"terms": cls.terms}
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
            DialogueMessage(
                LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                {"transaction_receipt": cls.transaction_receipt},
            ),
        )

        cls.list_of_aws_aeas = ["awx_aea_1", "awx_aea_2"]
        cls.developer_handle = "some_developer_handle"

    def _check_send_confirmation_details_to_awx_aeas(self, aea, mock_logger):
        mock_logger.assert_any_call(
            logging.INFO,
            f"informing awx_aeas={self.list_of_aws_aeas} of registration success of confirmed aea={aea} of developer={self.developer_handle}.",
        )
        for awx_awa in self.list_of_aws_aeas:
            message = self.get_message_from_outbox()
            has_attributes, error_str = self.message_has_attributes(
                actual_message=message,
                message_type=DefaultMessage,
                performative=DefaultMessage.Performative.BYTES,
                to=awx_awa,
                sender=self.skill.skill_context.agent_address,
                content=f"{aea}_{self.developer_handle}".encode("utf-8"),
            )
            assert has_attributes, error_str

    def test_setup(self):
        """Test the setup method of the ledger_api handler."""
        # setup
        list_of_aea = ["aea_1", "aea_2"]

        # operation
        with patch.object(
            type(self.strategy),
            "all_registered_aeas",
            new_callable=PropertyMock,
            return_value=list_of_aea,
        ):
            with patch.object(
                type(self.strategy),
                "awx_aeas",
                new_callable=PropertyMock,
                return_value=self.list_of_aws_aeas,
            ):
                with patch.object(
                    self.strategy,
                    "get_developer_handle",
                    return_value=self.developer_handle,
                ):
                    with patch.object(self.logger, "log") as mock_logger:
                        self.ledger_api_handler.setup()

        # after
        self.assert_quantity_in_outbox(len(self.list_of_aws_aeas) * len(list_of_aea))

        for aea in list_of_aea:
            self._check_send_confirmation_details_to_awx_aeas(aea, mock_logger)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the ledger_api handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=LedgerApiMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=LedgerApiMessage.Performative.ERROR,
            code=1,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid ledger_api message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_raw_transaction(self):
        """Test the _handle_raw_transaction method of the ledger_api handler."""
        # setup
        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_registration_messages[:1],
                is_agent_to_agent_messages=True,
            ),
        )
        register_dialogue.terms = self.terms

        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:1],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        ledger_api_dialogue.associated_register_dialogue = register_dialogue

        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.RAW_TRANSACTION,
                raw_transaction=self.raw_transaction,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.ledger_api_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_decision_making_queue(1)

        mock_logger.assert_any_call(
            logging.INFO, f"received raw transaction={incoming_message}"
        )

        message = self.get_message_from_decision_maker_inbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=SigningMessage,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            to=self.skill.skill_context.decision_maker_address,
            sender=str(self.skill.skill_context.skill_id),
            terms=self.terms,
        )
        assert has_attributes, error_str

        signing_dialogue = cast(
            SigningDialogue, self.signing_dialogues.get_dialogue(message)
        )

        assert signing_dialogue.associated_ledger_api_dialogue == ledger_api_dialogue

        mock_logger.assert_any_call(
            logging.INFO,
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
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
            to=incoming_message.sender,
            sender=str(self.skill.skill_context.skill_id),
            transaction_digest=self.transaction_digest,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO, "checking transaction is settled.",
        )

    def test_handle_transaction_receipt_i(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler."""
        # setup
        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_registration_messages[:1],
                is_agent_to_agent_messages=True,
            ),
        )
        register_dialogue.terms = self.terms

        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        ledger_api_dialogue.associated_register_dialogue = register_dialogue
        last_outgoing_message = cast(
            LedgerApiMessage, ledger_api_dialogue.last_outgoing_message
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
        with patch.object(
            self.transaction_behaviour, "finish_processing"
        ) as mocked_finish:
            with patch.object(
                LedgerApis, "is_transaction_settled", return_value=True
            ) as mocked_settled:
                with patch.object(
                    type(self.strategy),
                    "awx_aeas",
                    new_callable=PropertyMock,
                    return_value=self.list_of_aws_aeas,
                ):
                    with patch.object(
                        self.strategy,
                        "get_developer_handle",
                        return_value=self.developer_handle,
                    ):
                        with patch.object(self.logger, "log") as mock_logger:
                            self.ledger_api_handler.handle(incoming_message)

        # after
        mocked_settled.assert_called_once()
        mocked_finish.assert_any_call(ledger_api_dialogue)

        self.assert_quantity_in_outbox(3)
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=RegisterMessage,
            performative=RegisterMessage.Performative.SUCCESS,
            to=COUNTERPARTY_AGENT_ADDRESS,
            sender=self.skill.skill_context.agent_address,
            info={"transaction_digest": last_outgoing_message.transaction_digest.body},
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"informing counterparty={message.to} of registration success.",
        )

        # _send_confirmation_details_to_awx_aeas
        self._check_send_confirmation_details_to_awx_aeas(message.to, mock_logger)

    def test_handle_transaction_receipt_ii(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where last register msg is None."""
        # setup
        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_registration_messages[:1],
                is_agent_to_agent_messages=True,
            ),
        )
        register_dialogue.terms = self.terms
        register_dialogue._incoming_messages = []

        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        ledger_api_dialogue.associated_register_dialogue = register_dialogue

        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        # operation
        with patch.object(
            self.transaction_behaviour, "finish_processing"
        ) as mocked_finish:
            with patch.object(
                LedgerApis, "is_transaction_settled", return_value=True
            ) as mocked_settled:
                with pytest.raises(
                    ValueError, match="Could not retrieve last register message"
                ):
                    self.ledger_api_handler.handle(incoming_message)

        # after
        mocked_settled.assert_called_once()
        mocked_finish.assert_any_call(ledger_api_dialogue)

    def test_handle_transaction_receipt_iii(self):
        """Test the _handle_transaction_receipt method of the ledger_api handler where tx is NOT settled."""
        # setup
        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_registration_messages[:1],
                is_agent_to_agent_messages=True,
            ),
        )
        register_dialogue.terms = self.terms

        ledger_api_dialogue = cast(
            LedgerApiDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.ledger_api_dialogues,
                messages=self.list_of_ledger_api_messages[:5],
                counterparty=LEDGER_API_ADDRESS,
            ),
        )
        ledger_api_dialogue.associated_register_dialogue = register_dialogue

        incoming_message = cast(
            LedgerApiMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=ledger_api_dialogue,
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=self.transaction_receipt,
            ),
        )

        # operation
        with patch.object(
            self.transaction_behaviour, "failed_processing"
        ) as mocked_failed:
            with patch.object(
                LedgerApis, "is_transaction_settled", return_value=False
            ) as mocked_settled:
                with patch.object(self.logger, "log") as mock_logger:
                    self.ledger_api_handler.handle(incoming_message)

        # after
        mocked_settled.assert_called_once()
        mocked_failed.assert_any_call(ledger_api_dialogue)

        self.assert_quantity_in_outbox(0)
        assert self.transaction_behaviour.processing is None
        assert self.transaction_behaviour.processing_time == 0.0

        mock_logger.assert_any_call(
            logging.INFO,
            f"transaction_receipt={self.transaction_receipt} not settled or not valid, aborting",
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
        with patch.object(
            self.transaction_behaviour, "failed_processing"
        ) as mocked_failed:
            with patch.object(self.logger, "log") as mock_logger:
                self.ledger_api_handler.handle(incoming_message)

        # after
        mocked_failed.assert_called_once()

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
