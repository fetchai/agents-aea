# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains test case classes based on pytest for AEA skill testing."""
import asyncio
import os
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from typing import Any, Dict, Optional, Tuple, Type, cast

from aea.configurations.loader import ConfigLoaders, PackageType, SkillConfig
from aea.context.base import AgentContext
from aea.crypto.ledger_apis import DEFAULT_CURRENCY_DENOMINATIONS
from aea.exceptions import AEAEnforceError
from aea.helpers.io import open_file
from aea.identity.base import Identity
from aea.mail.base import Address
from aea.multiplexer import AsyncMultiplexer, Multiplexer, OutBox
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, DialogueMessage, Dialogues
from aea.skills.base import Skill
from aea.skills.tasks import TaskManager


COUNTERPARTY_AGENT_ADDRESS = "counterparty"
COUNTERPARTY_SKILL_ADDRESS = "some_author/some_skill:0.1.0"


class BaseSkillTestCase:
    """A class to test a skill."""

    path_to_skill: Path = Path(".")
    is_agent_to_agent_messages: bool = True
    _skill: Skill
    _multiplexer: AsyncMultiplexer
    _outbox: OutBox

    @property
    def skill(self) -> Skill:
        """Get the skill."""
        try:
            value = self._skill
        except AttributeError:
            raise ValueError("Ensure skill is set during setup_class.")
        return value

    def get_quantity_in_outbox(self) -> int:
        """Get the quantity of envelopes in the outbox."""
        return self._multiplexer.out_queue.qsize()

    def get_message_from_outbox(self) -> Optional[Message]:
        """Get message from outbox."""
        if self._outbox.empty():
            return None
        envelope = self._multiplexer.out_queue.get_nowait()
        return envelope.message

    def drop_messages_from_outbox(self, number: int = 1) -> None:
        """Dismiss the first 'number' number of message from outbox."""
        while (not self._outbox.empty()) and number != 0:
            self._multiplexer.out_queue.get_nowait()
            number -= 1

    def get_quantity_in_decision_maker_inbox(self) -> int:
        """Get the quantity of messages in the decision maker inbox."""
        return self._skill.skill_context.decision_maker_message_queue.qsize()

    def get_message_from_decision_maker_inbox(self) -> Optional[Message]:
        """Get message from decision maker inbox."""
        if self._skill.skill_context.decision_maker_message_queue.empty():
            return None
        return self._skill.skill_context.decision_maker_message_queue.get_nowait()

    def drop_messages_from_decision_maker_inbox(self, number: int = 1) -> None:
        """Dismiss the first 'number' number of message from decision maker inbox."""
        while (
            not self._skill.skill_context.decision_maker_message_queue.empty()
        ) and number != 0:
            self._skill.skill_context.decision_maker_message_queue.get_nowait()
            number -= 1

    def assert_quantity_in_outbox(self, expected_quantity: int) -> None:
        """Assert the quantity of messages in the outbox."""
        quantity = self.get_quantity_in_outbox()
        assert (  # nosec
            quantity == expected_quantity
        ), f"Invalid number of messages in outbox. Expected {expected_quantity}. Found {quantity}."

    def assert_quantity_in_decision_making_queue(self, expected_quantity: int) -> None:
        """Assert the quantity of messages in the decision maker queue."""
        quantity = self.get_quantity_in_decision_maker_inbox()
        assert (  # nosec
            quantity == expected_quantity
        ), f"Invalid number of messages in decision maker queue. Expected {expected_quantity}. Found {quantity}."

    @staticmethod
    def message_has_attributes(
        actual_message: Message,
        message_type: Type[Message],
        **kwargs: Any,
    ) -> Tuple[bool, str]:
        """
        Evaluates whether a message's attributes match the expected attributes provided.

        :param actual_message: the actual message
        :param message_type: the expected message type
        :param kwargs: other expected message attributes

        :return: boolean result of the evaluation and accompanied message
        """
        if (
            type(actual_message)  # pylint: disable=unidiomatic-typecheck
            != message_type
        ):
            return (
                False,
                "The message types do not match. Actual type: {}. Expected type: {}".format(
                    type(actual_message), message_type
                ),
            )

        for attribute_name, expected_value in kwargs.items():
            actual_value = getattr(actual_message, attribute_name)
            if actual_value != expected_value:
                return (
                    False,
                    f"The '{attribute_name}' fields do not match. Actual '{attribute_name}': {actual_value}. Expected '{attribute_name}': {expected_value}",
                )

        return True, "The message has the provided expected attributes."

    def build_incoming_message(
        self,
        message_type: Type[Message],
        performative: Message.Performative,
        dialogue_reference: Optional[Tuple[str, str]] = None,
        message_id: Optional[int] = None,
        target: Optional[int] = None,
        to: Optional[Address] = None,
        sender: Optional[Address] = None,
        is_agent_to_agent_messages: Optional[bool] = None,
        **kwargs: Any,
    ) -> Message:
        """
        Quickly create an incoming message with the provided attributes.

        For any attribute not provided, the corresponding default value in message is used.

        :param message_type: the type of the message
        :param dialogue_reference: the dialogue_reference
        :param message_id: the message_id
        :param target: the target
        :param performative: the performative
        :param to: the 'to' address
        :param sender: the 'sender' address
        :param is_agent_to_agent_messages: whether the dialogue is between agents or components
        :param kwargs: other attributes

        :return: the created incoming message
        """
        if is_agent_to_agent_messages is None:
            is_agent_to_agent_messages = self.is_agent_to_agent_messages
        if sender is None:
            sender = (
                COUNTERPARTY_AGENT_ADDRESS
                if is_agent_to_agent_messages
                else COUNTERPARTY_SKILL_ADDRESS
            )
        message_attributes = dict()  # type: Dict[str, Any]

        default_dialogue_reference = Dialogues.new_self_initiated_dialogue_reference()
        dialogue_reference = (
            default_dialogue_reference
            if dialogue_reference is None
            else dialogue_reference
        )
        message_attributes["dialogue_reference"] = dialogue_reference
        if message_id is not None:
            message_attributes["message_id"] = message_id
        if target is not None:
            message_attributes["target"] = target
        message_attributes["performative"] = performative
        message_attributes.update(kwargs)

        incoming_message = message_type(**message_attributes)
        incoming_message.sender = sender
        default_to = (
            self.skill.skill_context.agent_address
            if is_agent_to_agent_messages
            else str(self.skill.public_id)
        )
        incoming_message.to = default_to if to is None else to
        return incoming_message

    def build_incoming_message_for_skill_dialogue(
        self,
        dialogue: Dialogue,
        performative: Message.Performative,
        message_type: Optional[Type[Message]] = None,
        dialogue_reference: Optional[Tuple[str, str]] = None,
        message_id: Optional[int] = None,
        target: Optional[int] = None,
        to: Optional[Address] = None,
        sender: Optional[Address] = None,
        **kwargs: Any,
    ) -> Message:
        """
        Quickly create an incoming message with the provided attributes for a dialogue.

        For any attribute not provided, a value based on the dialogue is used.
        These values are shown in parentheses in the list of parameters below.

        NOTE: This method must be used with care. The dialogue provided is part of the skill
        which is being tested. Because for any unspecified attribute, a "correct" value is used,
        the test will be, by design, insured to pass on these values.

        :param dialogue: the dialogue to which the incoming message is intended
        :param performative: the performative of the message
        :param message_type: (the message_class of the provided dialogue) the type of the message
        :param dialogue_reference: (the dialogue_reference of the provided dialogue) the dialogue reference of the message
        :param message_id: (the id of the last message in the provided dialogue + 1) the id of the message
        :param target: (the id of the last message in the provided dialogue) the target of the message
        :param to: (the agent address associated with this skill) the receiver of the message
        :param sender: (the counterparty in the provided dialogue) the sender of the message
        :param kwargs: other attributes

        :return: the created incoming message
        """
        if dialogue is None:
            raise AEAEnforceError("dialogue cannot be None.")

        if dialogue.last_message is None:
            raise AEAEnforceError("dialogue cannot be empty.")

        message_type = (
            message_type if message_type is not None else dialogue.message_class
        )
        dialogue_reference = (
            dialogue_reference
            if dialogue_reference is not None
            else dialogue.dialogue_label.dialogue_reference
        )
        message_id = (
            message_id
            if message_id is not None
            else dialogue.get_incoming_next_message_id()
        )
        target = target if target is not None else dialogue.last_message.message_id
        to = to if to is not None else dialogue.self_address
        sender = (
            sender
            if sender is not None
            else dialogue.dialogue_label.dialogue_opponent_addr
        )

        incoming_message = self.build_incoming_message(
            message_type=message_type,
            performative=performative,
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            to=to,
            sender=sender,
            **kwargs,
        )
        return incoming_message

    @staticmethod
    def _provide_unspecified_fields(
        message: DialogueMessage, last_is_incoming: Optional[bool]
    ) -> Tuple[bool, Optional[int]]:
        """
        Specifies values (an interpretation) for the unspecified fields of a DialogueMessage.

        For an unspecified is_incoming, the opposite of the last_is_incoming value is used.
        For an unspecified target, the message_id of the previous message (message_id - 1) is used.

        :param message: the DialogueMessage
        :param last_is_incoming: the is_incoming value of the previous DialogueMessage

        :return: the is_incoming and target values
        """
        default_is_incoming = not last_is_incoming
        is_incoming = default_is_incoming if message[2] is None else message[2]

        default_target = None
        target = default_target if message[3] is None else message[3]
        return is_incoming, target

    @staticmethod
    def _non_initial_incoming_message_dialogue_reference(
        dialogue: Dialogue,
    ) -> Tuple[str, str]:
        """
        Specifies the dialogue reference of a non-initial incoming message for a dialogue.

        It uses a complete version of the reference in the dialogue if it is incomplete,
        otherwise it uses the reference in the dialogue.

        :param dialogue: the dialogue to which the incoming message is intended
        :return: its dialogue reference
        """
        dialogue_reference = (
            dialogue.dialogue_label.dialogue_reference[0],
            Dialogues._generate_dialogue_nonce()  # pylint: disable=protected-access
            if dialogue.dialogue_label.dialogue_reference[1]
            == Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            else dialogue.dialogue_label.dialogue_reference[1],
        )
        return dialogue_reference

    def _extract_message_fields(
        self,
        message: DialogueMessage,
        index: int,
        last_is_incoming: bool,
    ) -> Tuple[Message.Performative, Dict, int, bool, Optional[int]]:
        """
        Extracts message attributes from a dialogue message.

        :param message: the dialogue message
        :param index: the index of this dialogue message in the sequence of messages
        :param last_is_incoming: the is_incoming of the last message in the sequence

        :return: the performative, contents, message_id, is_incoming, target of the message
        """
        performative = message[0]
        contents = message[1]
        message_id = index + 1
        is_incoming, target = self._provide_unspecified_fields(
            message, last_is_incoming=last_is_incoming
        )
        return performative, contents, message_id, is_incoming, target

    def prepare_skill_dialogue(
        self,
        dialogues: Dialogues,
        messages: Tuple[DialogueMessage, ...],
        counterparty: Optional[Address] = None,
        is_agent_to_agent_messages: Optional[bool] = None,
    ) -> Dialogue:
        """
        Quickly create a dialogue.

        The 'messages' argument is a tuple of DialogueMessages.
        For every DialogueMessage (performative, contents, is_incoming, target):
            - if 'is_incoming' is not provided: for the first message it is assumed False (outgoing),
            for any other message, it is the opposite of the one preceding it.
            - if 'target' is not provided: for the first message it is assumed 0,
            for any other message, it is the index of the message before it in the tuple of messages + 1.

        :param dialogues: a dialogues class
        :param counterparty: the message_id
        :param messages: the dialogue_reference
        :param is_agent_to_agent_messages: whether the dialogue is between agents or components

        :return: the created incoming message
        """
        if is_agent_to_agent_messages is None:
            is_agent_to_agent_messages = self.is_agent_to_agent_messages
        if counterparty is None:
            counterparty = (  # pragma: nocover
                COUNTERPARTY_AGENT_ADDRESS
                if is_agent_to_agent_messages
                else COUNTERPARTY_SKILL_ADDRESS
            )
        if len(messages) == 0:
            raise AEAEnforceError("the list of messages must be positive.")

        (
            performative,
            contents,
            message_id,
            is_incoming,
            target,
        ) = self._extract_message_fields(messages[0], index=0, last_is_incoming=True)

        if is_incoming:  # first message from the opponent
            dialogue_reference = dialogues.new_self_initiated_dialogue_reference()
            message = self.build_incoming_message(
                message_type=dialogues.message_class,
                dialogue_reference=dialogue_reference,
                message_id=Dialogue.STARTING_MESSAGE_ID,
                target=target or Dialogue.STARTING_TARGET,
                performative=performative,
                to=dialogues.self_address,
                sender=counterparty,
                is_agent_to_agent_messages=is_agent_to_agent_messages,
                **contents,
            )
            dialogue = cast(Dialogue, dialogues.update(message))
            if dialogue is None:
                raise AEAEnforceError(
                    "Cannot update the dialogue with message number {}".format(
                        message_id
                    )
                )
        else:  # first message from self
            _, dialogue = dialogues.create(
                counterparty=counterparty, performative=performative, **contents
            )

        for idx, dialogue_message in enumerate(messages[1:]):
            (
                performative,
                contents,
                message_id,
                is_incoming,
                target,
            ) = self._extract_message_fields(dialogue_message, idx + 1, is_incoming)
            if target is None:
                target = cast(Message, dialogue.last_message).message_id

            if is_incoming:  # messages from the opponent
                dialogue_reference = (
                    self._non_initial_incoming_message_dialogue_reference(dialogue)
                )
                message_id = dialogue.get_incoming_next_message_id()

                message = self.build_incoming_message(
                    message_type=dialogues.message_class,
                    dialogue_reference=dialogue_reference,
                    message_id=message_id,
                    target=target,
                    performative=performative,
                    to=dialogues.self_address,
                    sender=counterparty,
                    is_agent_to_agent_messages=is_agent_to_agent_messages,
                    **contents,
                )
                dialogue = cast(Dialogue, dialogues.update(message))
                if dialogue is None:
                    raise AEAEnforceError(
                        "Cannot update the dialogue with message number {}".format(
                            message_id
                        )
                    )
            else:  # messages from self
                dialogue.reply(performative=performative, target=target, **contents)

        return dialogue

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Set up the skill test case."""
        identity = Identity(
            "test_agent_name", "test_agent_address", "test_agent_public_key"
        )

        cls._multiplexer = AsyncMultiplexer()
        cls._multiplexer._out_queue = (  # pylint: disable=protected-access
            asyncio.Queue()
        )
        cls._outbox = OutBox(cast(Multiplexer, cls._multiplexer))
        _shared_state = cast(Optional[Dict[str, Any]], kwargs.pop("shared_state", None))
        _skill_config_overrides = cast(
            Optional[Dict[str, Any]], kwargs.pop("config_overrides", None)
        )
        _dm_context_kwargs = cast(
            Dict[str, Any], kwargs.pop("dm_context_kwargs", dict())
        )

        agent_context = AgentContext(
            identity=identity,
            connection_status=cls._multiplexer.connection_status,
            outbox=cls._outbox,
            decision_maker_message_queue=Queue(),
            decision_maker_handler_context=SimpleNamespace(**_dm_context_kwargs),
            task_manager=TaskManager(),
            default_ledger_id=identity.default_address_key,
            currency_denominations=DEFAULT_CURRENCY_DENOMINATIONS,
            default_connection=None,
            default_routing={},
            search_service_address="dummy_author/dummy_search_skill:0.1.0",
            decision_maker_address="dummy_decision_maker_address",
            data_dir=os.getcwd(),
        )

        # Pre-populate the 'shared_state' prior to loading the skill
        if _shared_state is not None:
            for key, value in _shared_state.items():
                agent_context.shared_state[key] = value

        skill_configuration_file_path: Path = Path(cls.path_to_skill, "skill.yaml")
        loader = ConfigLoaders.from_package_type(PackageType.SKILL)

        with open_file(skill_configuration_file_path) as fp:
            skill_config: SkillConfig = loader.load(fp)

        # Override skill's config prior to loading
        if _skill_config_overrides is not None:
            skill_config.update(_skill_config_overrides)

        skill_config.directory = cls.path_to_skill

        cls._skill = Skill.from_config(skill_config, agent_context)
