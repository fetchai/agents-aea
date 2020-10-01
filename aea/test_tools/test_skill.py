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
"""This module contains test case classes based on pytest for AEA skill testing."""

import asyncio
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from typing import Any, Dict, Optional, Tuple, Type, Union, cast

from aea.context.base import AgentContext
from aea.exceptions import AEAEnforceError
from aea.identity.base import Identity
from aea.mail.base import Address
from aea.multiplexer import AsyncMultiplexer, Multiplexer, OutBox
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, Dialogues
from aea.skills.base import Skill
from aea.skills.tasks import TaskManager


class BaseSkillTestCase:
    """A class to test a skill."""

    path_to_skill: Union[Path, str] = Path(".")
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

    @staticmethod
    def message_has_attributes(
        actual_message: Message, message_type: Type[Message], **kwargs,
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
            attribute = getattr(actual_message, attribute_name)
            if callable(attribute):
                if attribute != expected_value:
                    return (
                        False,
                        "The '{}' fields do not match. Actual '{}': {}. Expected '{}': {}".format(  # pylint: disable=duplicate-string-formatting-argument
                            attribute_name,
                            attribute_name,
                            attribute,
                            attribute_name,
                            expected_value,
                        ),
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
        sender: Address = "counterparty",
        **kwargs,
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
        :param kwargs: other attributes

        :return: the created incoming message
        """
        message_attributes = dict()  # type: Dict[str, Any]

        default_dialogue_reference = (
            Dialogues._generate_dialogue_nonce(),
            "",  # pylint: disable=protected-access
        )
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
        incoming_message.to = (
            self.skill.skill_context.agent_address if to is None else to
        )

        return incoming_message

    def build_incoming_message_for_dialogue(
        self,
        dialogue: Dialogue,
        performative: Message.Performative,
        target: Optional[int] = None,
        **kwargs,
    ) -> Message:
        """
        Quickly create an incoming message with the provided attributes for a dialogue.

        For any attribute not provided, the corresponding default value in message is used.

        :param dialogue: the dialogue to which the incoming message is intended
        :param target: the target
        :param performative: the performative
        :param kwargs: other attributes

        :return: the created incoming message
        """
        if dialogue is None:
            raise AEAEnforceError("dialogue cannot be None.")

        if dialogue.last_message is None:
            raise AEAEnforceError("dialogue cannot be empty.")

        if target is None:
            target = dialogue.last_message.message_id

        incoming_message = self.build_incoming_message(
            message_type=dialogue._message_class,
            performative=performative,
            dialogue_reference=dialogue.dialogue_label.dialogue_reference,
            message_id=dialogue.last_message.message_id + 1,
            target=target,
            to=self.skill.skill_context.agent_address,
            sender=dialogue.dialogue_label.dialogue_opponent_addr,
            **kwargs,
        )

        return incoming_message

    @staticmethod
    def _complete_compact_message(
        message: Tuple[Any, ...], last_incoming: Optional[bool], message_id: int
    ) -> Tuple[Any, ...]:
        new_message = message
        if type(message[0]) != bool:  # pylint: disable=unidiomatic-typecheck
            new_message = (
                (False, *message) if last_incoming is True else (True, *message)
            )
        if type(new_message[1]) != int:  # pylint: disable=unidiomatic-typecheck
            new_message_list = list(new_message)
            new_message_list.insert(1, message_id - 1)
            new_message = tuple(new_message_list)
        return new_message

    def prepare_dialogue(
        self,
        dialogues: Dialogues,
        messages: Tuple[Tuple[Any, ...]],
        counterparty: Address = "counterparty",
    ) -> Dialogue:
        """
        Quickly create a dialogue.

        The 'messages' argument is a tuple of "compact messages".
        Each compact message is represented as a tuple (inc, target, performative, contents), where
         - 'inc' is boolean, representing whether the message is incoming (True), or outgoing (False).
            - 'inc' is optional, if not provided: for the first message is assumed False (outgoing),
            for any other message, it is the opposite of the one preceding it.
         - 'target' is integer, representing the target of the message.
            - 'target' is optional, if not provided: for the first message is assumed 0,
            for any other message, it is the index of the message before it in the tuple of messages + 1.
         - 'performative' represents the performative of the message.
         - contents is dictionary of the message's contents.

        :param dialogues: a dialogues class
        :param counterparty: the message_id
        :param messages: the dialogue_reference

        :return: the created incoming message
        """
        last_incoming = True  # if 'inc' is not specified for the first message, this line makes it so the first message is outgoing
        for incomplete_message in messages:
            complete_compact_message = self._complete_compact_message(
                incomplete_message,
                last_incoming=last_incoming,
                message_id=messages.index(incomplete_message) + 1,
            )
            last_incoming = complete_compact_message[0]
            is_incoming = complete_compact_message[0]
            message_id = messages.index(incomplete_message) + 1
            target = complete_compact_message[1]
            performative = complete_compact_message[2]
            contents = complete_compact_message[3]
            dialogue: Dialogue

            if is_incoming:  # messages from the opponent
                if message_id == 1:
                    dialogue_reference = (
                        dialogues.new_self_initiated_dialogue_reference()
                    )
                else:
                    dialogue_reference = (
                        dialogue.dialogue_label.dialogue_reference[0],
                        Dialogues._generate_dialogue_nonce()
                        if dialogue.dialogue_label.dialogue_reference[1]
                        == Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
                        else dialogue.dialogue_label.dialogue_reference[1],
                    )
                message = self.build_incoming_message(
                    message_type=dialogues._message_class,  # pylint: disable=protected-access
                    dialogue_reference=dialogue_reference,
                    message_id=message_id,
                    target=target,
                    performative=performative,
                    to=self.skill.skill_context.agent_address,
                    sender=counterparty,
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
                if message_id == 1:
                    _, dialogue = dialogues.create(
                        counterparty=counterparty, performative=performative, **contents
                    )
                else:
                    dialogue.reply(performative=performative, target=target, **contents)



            

        return dialogue

    @classmethod
    def setup(cls) -> None:
        """Set up the skill test case."""
        identity = Identity("test_agent_name", "test_agent_address")

        cls._multiplexer = AsyncMultiplexer()
        cls._multiplexer._out_queue = (  # pylint: disable=protected-access
            asyncio.Queue()
        )
        cls._outbox = OutBox(cast(Multiplexer, cls._multiplexer))

        agent_context = AgentContext(
            identity=identity,
            connection_status=cls._multiplexer.connection_status,
            outbox=cls._outbox,
            decision_maker_message_queue=Queue(),
            decision_maker_handler_context=SimpleNamespace(),
            task_manager=TaskManager(),
            default_connection=None,
            default_routing={},
            search_service_address="dummy_search_service_address",
            decision_maker_address="dummy_decision_maker_address",
        )

        cls._skill = Skill.from_dir(str(cls.path_to_skill), agent_context)
