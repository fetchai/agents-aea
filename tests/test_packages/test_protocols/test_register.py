# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This module contains tests for the register protocol."""
from typing import Type
from unittest.mock import patch

import pytest

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

from packages.fetchai.protocols.register.dialogues import (
    RegisterDialogue as BaseRegisterDialogue,
)
from packages.fetchai.protocols.register.dialogues import (
    RegisterDialogues as BaseRegisterDialogues,
)
from packages.fetchai.protocols.register.message import RegisterMessage


class TestRegisterMessage:
    """Test the register message module."""

    @classmethod
    def setup_class(cls):
        """Setup class for test case."""
        cls.info = {"a": "b", "c": "d"}

    def test_register(self):
        """Test for an error for a register message."""
        tx_msg = RegisterMessage(
            performative=RegisterMessage.Performative.REGISTER, info=self.info
        )
        assert tx_msg._is_consistent()
        encoded_tx_msg = tx_msg.encode()
        decoded_tx_msg = tx_msg.serializer.decode(encoded_tx_msg)
        assert tx_msg == decoded_tx_msg

    def test_success(self):
        """Test for an error for a success message."""
        tx_msg = RegisterMessage(
            performative=RegisterMessage.Performative.SUCCESS,
            info=self.info,
            target=1,
            message_id=2,
        )
        assert tx_msg._is_consistent()
        encoded_tx_msg = tx_msg.encode()
        decoded_tx_msg = tx_msg.serializer.decode(encoded_tx_msg)
        assert tx_msg == decoded_tx_msg

    def test_error(self):
        """Test for an error for a register error message."""
        some_error_code = 1
        some_error_msg = "Some error message"
        tx_msg = RegisterMessage(
            performative=RegisterMessage.Performative.ERROR,
            error_code=some_error_code,
            error_msg=some_error_msg,
            info=self.info,
        )
        assert tx_msg._is_consistent()
        encoded_tx_msg = tx_msg.encode()
        decoded_tx_msg = tx_msg.serializer.decode(encoded_tx_msg)
        assert tx_msg == decoded_tx_msg


def test_consistency_check_negative():
    """Test the consistency check, negative case."""
    tx_msg = RegisterMessage(performative=RegisterMessage.Performative.REGISTER,)
    assert not tx_msg._is_consistent()


def test_serialization_negative():
    """Test serialization when performative is not recognized."""
    tx_msg = RegisterMessage(
        performative=RegisterMessage.Performative.REGISTER, info={},
    )

    with patch.object(RegisterMessage.Performative, "__eq__", return_value=False):
        with pytest.raises(
            ValueError, match=f"Performative not valid: {tx_msg.performative}"
        ):
            tx_msg.serializer.encode(tx_msg)

    encoded_tx_bytes = tx_msg.serializer.encode(tx_msg)
    with patch.object(RegisterMessage.Performative, "__eq__", return_value=False):
        with pytest.raises(
            ValueError, match=f"Performative not valid: {tx_msg.performative}"
        ):
            tx_msg.serializer.decode(encoded_tx_bytes)


def test_dialogues():
    """Test instantiation of dialogues."""
    register_dialogues = RegisterDialogues("agent_addr")
    msg, dialogue = register_dialogues.create(
        counterparty="abc", performative=RegisterMessage.Performative.REGISTER, info={}
    )
    assert dialogue is not None


class RegisterDialogue(BaseRegisterDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[RegisterMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        BaseRegisterDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class RegisterDialogues(BaseRegisterDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return RegisterDialogue.Role.AGENT

        BaseRegisterDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=RegisterDialogue,
        )
