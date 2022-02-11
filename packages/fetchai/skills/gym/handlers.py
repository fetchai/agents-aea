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
"""This module contains the handler for the 'gym' skill."""

from typing import Any, Optional, cast

from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.gym.message import GymMessage
from packages.fetchai.skills.gym.dialogues import (
    DefaultDialogues,
    GymDialogue,
    GymDialogues,
)
from packages.fetchai.skills.gym.rl_agent import DEFAULT_NB_STEPS
from packages.fetchai.skills.gym.tasks import GymTask


class GymHandler(Handler):
    """Gym handler."""

    SUPPORTED_PROTOCOL = GymMessage.protocol_id

    def __init__(self, **kwargs: Any):
        """Initialize the handler."""
        nb_steps = kwargs.pop("nb_steps", DEFAULT_NB_STEPS)
        super().__init__(**kwargs)
        self.task = GymTask(self.context, nb_steps)
        self._task_id: Optional[int] = None

    def setup(self) -> None:
        """Set up the handler."""
        self.context.logger.info("Gym handler: setup method called.")
        # launch the task
        self._task_id = self.context.task_manager.enqueue_task(self.task)

    def handle(self, message: Message) -> None:
        """
        Implement messages.

        :param message: the message
        :return: None
        """
        gym_msg = cast(GymMessage, message)

        # recover dialogue
        gym_dialogues = cast(GymDialogues, self.context.gym_dialogues)
        gym_dialogue = cast(GymDialogue, gym_dialogues.update(gym_msg))
        if gym_dialogue is None:
            self._handle_unidentified_dialogue(gym_msg)
            return

        # handle message
        if gym_msg.performative == GymMessage.Performative.PERCEPT:
            self._handle_percept(gym_msg, gym_dialogue)
        elif gym_msg.performative == GymMessage.Performative.STATUS:
            self._handle_status(gym_msg, gym_dialogue)
        else:
            self._handle_invalid(gym_msg, gym_dialogue)

    def _handle_unidentified_dialogue(self, gym_msg: GymMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param gym_msg: the message
        """
        self.context.logger.info(
            "received invalid gym message={}, unidentified dialogue.".format(gym_msg)
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg, _ = default_dialogues.create(
            counterparty=gym_msg.sender,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"gym_message": gym_msg.encode()},
        )
        self.context.outbox.put_message(message=default_msg)

    def _handle_percept(self, gym_msg: GymMessage, gym_dialogue: GymDialogue) -> None:
        """
        Handle messages.

        :param gym_msg: the gym message
        :param gym_dialogue: the gym dialogue
        """
        if self.task.proxy_env.active_gym_dialogue == gym_dialogue:
            self.task.proxy_env_queue.put(gym_msg)
        else:
            self.context.logger.warning("gym dialogue not active dialogue.")

    def _handle_status(self, gym_msg: GymMessage, gym_dialogue: GymDialogue) -> None:
        """
        Handle messages.

        :param gym_msg: the gym message
        :param gym_dialogue: the gym dialogue
        """
        if (
            self.task.proxy_env.active_gym_dialogue == gym_dialogue
            and gym_msg.content.get("reset", "failure") == "success"
        ):
            self.task.proxy_env_queue.put(gym_msg)
        else:
            self.context.logger.warning("gym dialogue not active dialogue.")

    def _handle_invalid(self, gym_msg: GymMessage, gym_dialogue: GymDialogue) -> None:
        """
        Handle an invalid http message.

        :param gym_msg: the gym message
        :param gym_dialogue: the gym dialogue
        """
        self.context.logger.warning(
            "cannot handle gym message of performative={} in dialogue={}.".format(
                gym_msg.performative, gym_dialogue
            )
        )

    def teardown(self) -> None:
        """Teardown the handler."""
        self.context.logger.info("Gym handler: teardown method called.")
        if self._task_id is None:
            return  # pragma: nocover
        self.task.teardown()
        result = self.context.task_manager.get_task_result(self._task_id)
        if not result.successful():
            self.context.logger.warning("Task not successful!")
