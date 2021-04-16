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
"""This module contains the tests of the handler classes of the registration_aw1 skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.helpers.transaction.base import Terms
from aea.protocols.dialogue.base import DialogueMessage

from packages.fetchai.protocols.register.message import RegisterMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.registration_aw1.dialogues import (
    RegisterDialogue,
    SigningDialogue,
)

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_registration_aw1.intermediate_class import (
    RegiatrationAW1TestCase,
)


class TestAW1RegistrationHandler(RegiatrationAW1TestCase):
    """Test registration handler of registration_aw1."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "registration_aw1")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()

        cls.signature_of_ethereum_address = "some_signature_of_ethereum_address"
        cls.info = {
            "ethereum_address": cls.ethereum_address,
            "fetchai_address": cls._skill.skill_context.agent_address,
            "signature_of_ethereum_address": cls.signature_of_ethereum_address,
            "signature_of_fetchai_address": cls.signature_of_fetchai_address,
            "developer_handle": cls.developer_handle,
            "tweet": cls.tweet,
        }
        cls.list_of_messages = (
            DialogueMessage(RegisterMessage.Performative.REGISTER, {"info": cls.info}),
        )

    def test_setup(self):
        """Test the setup method of the registration_aw1 handler."""
        assert self.register_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the registration_aw1 handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=RegisterMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=RegisterMessage.Performative.REGISTER,
            info={"some_key": "some_value"},
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.register_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid register_msg message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_success_i(self):
        """Test the _handle_success method of the registration_aw1 handler where announce_termination_key IS None."""
        # setup
        self.strategy.announce_termination_key = None

        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_messages,
                is_agent_to_agent_messages=True,
            ),
        )
        incoming_message = cast(
            RegisterMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=register_dialogue,
                performative=RegisterMessage.Performative.SUCCESS,
                info={"transaction_digest": "some_transaction_digest"},
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.register_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.DEBUG,
            f"received register_msg success message={incoming_message} in dialogue={register_dialogue}.",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            f"received register message success, info={incoming_message.info}. Stop me now!",
        )

        assert self.strategy.is_registered is True
        assert self.strategy.is_registration_pending is False
        assert self.strategy.is_ready_to_register is False

    def test_handle_success_ii(self):
        """Test the _handle_success method of the registration_aw1 handler where announce_termination_key is NOT None."""
        # setup
        key = "some_key"
        self.strategy.announce_termination_key = key

        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_messages,
                is_agent_to_agent_messages=True,
            ),
        )
        incoming_message = cast(
            RegisterMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=register_dialogue,
                performative=RegisterMessage.Performative.SUCCESS,
                info={"transaction_digest": "some_transaction_digest"},
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.register_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.DEBUG,
            f"received register_msg success message={incoming_message} in dialogue={register_dialogue}.",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            f"received register message success, info={incoming_message.info}. Stop me now!",
        )

        assert self.strategy.is_registered is True
        assert self.strategy.is_registration_pending is False
        assert self.strategy.is_ready_to_register is False

        assert self.skill.skill_context.shared_state[key] is True

    def test_handle_error(self):
        """Test the _handle_error method of the registration_aw1 handler."""
        # setup
        register_dialogue = cast(
            RegisterDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.register_dialogues,
                messages=self.list_of_messages,
                is_agent_to_agent_messages=True,
            ),
        )
        incoming_message = cast(
            RegisterMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=register_dialogue,
                performative=RegisterMessage.Performative.ERROR,
                error_code=1,
                error_msg="some_error_msg",
                info={"some_key": "some_value"},
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.register_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.DEBUG,
            f"received register_msg error message={incoming_message} in dialogue={register_dialogue}.",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            f"received register message error, error_msg={incoming_message.error_msg}. Stop me now!",
        )

        assert self.strategy.is_registration_pending is False
        assert self.strategy.is_ready_to_register is False

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the registration_aw1 handler."""
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
        with patch.object(self.logger, "log") as mock_logger:
            self.register_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        register_dialogue = self.register_dialogues.get_dialogue(incoming_message)

        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle register_msg message of performative={incoming_message.performative} in dialogue={register_dialogue}.",
        )

    def test_teardown(self):
        """Test the teardown method of the registration_aw1 handler."""
        assert self.register_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestSigningHandler(RegiatrationAW1TestCase):
    """Test signing handler of registration_aw1."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "registration_aw1")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()

        cls.ledger_id = "some_ledger_id"
        cls.body_bytes = b"some_body"
        cls.body_str = "some_body"
        cls.terms = Terms(
            "some_ledger_id",
            cls._skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        cls.list_of_signing_msg_messages = (
            DialogueMessage(
                SigningMessage.Performative.SIGN_MESSAGE,
                {
                    "terms": cls.terms,
                    "raw_message": SigningMessage.RawMessage(
                        cls.ledger_id, cls.body_bytes
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

    def test_handle_signed_message(self):
        """Test the _handle_signed_message method of the signing handler."""
        # setup
        signing_dialogue = cast(
            SigningDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.signing_dialogues,
                messages=self.list_of_signing_msg_messages[:1],
                counterparty=self.skill.skill_context.decision_maker_address,
            ),
        )

        incoming_message = cast(
            SigningMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=signing_dialogue,
                performative=SigningMessage.Performative.SIGNED_MESSAGE,
                signed_message=SigningMessage.SignedMessage(
                    self.ledger_id, self.body_str
                ),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.signing_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.DEBUG,
            f"received signing message from decision maker, message={incoming_message} in dialogue={signing_dialogue}",
        )

        mock_logger.assert_any_call(
            logging.INFO,
            f"received signing message from decision maker, signature={incoming_message.signed_message.body} stored!",
        )

        assert self.strategy.signature_of_ethereum_address == self.body_str
        assert self.strategy.is_ready_to_register is True

    def test_handle_error(self):
        """Test the _handle_error method of the signing handler."""
        # setup
        signing_counterparty = self.skill.skill_context.decision_maker_address
        signing_dialogue = self.prepare_skill_dialogue(
            dialogues=self.signing_dialogues,
            messages=self.list_of_signing_msg_messages[:1],
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
            f"cannot handle signing message of performative={incoming_message.performative} in dialogue={self.signing_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the signing handler."""
        assert self.signing_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
