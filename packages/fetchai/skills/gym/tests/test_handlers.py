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
"""This module contains the tests of the handler classes of the gym skill."""
# pylint: skip-file

import logging
from multiprocessing.pool import ApplyResult
from typing import cast
from unittest.mock import Mock, patch

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.gym.message import GymMessage
from packages.fetchai.skills.gym.dialogues import GymDialogue
from packages.fetchai.skills.gym.tests.intermediate_class import GymTestCase


class TestGymHandler(GymTestCase):
    """Test Gym handler of gym."""

    is_agent_to_agent_messages = False

    def test__init__(self):
        """Test the __init__ method of the gym handler."""
        assert self.gym_handler._task_id is None

    def test_setup(self):
        """Test the setup method of the gym handler."""
        # operation
        with patch.object(
            self.task_manager, "enqueue_task", return_value=self.mocked_task_id
        ) as mocked_enqueue_task:
            with patch.object(self.logger, "log") as mock_logger:
                assert self.gym_handler.setup() is None

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO,
            "Gym handler: setup method called.",
        )
        mocked_enqueue_task.assert_any_call(self.gym_handler.task)
        assert self.gym_handler._task_id == self.mocked_task_id

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the gym handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=GymMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=GymMessage.Performative.RESET,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.gym_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid gym message={incoming_message}, unidentified dialogue.",
        )

        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=DefaultMessage,
            performative=DefaultMessage.Performative.ERROR,
            to=incoming_message.sender,
            sender=str(self.skill.skill_context.skill_id),
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"gym_message": incoming_message.encode()},
        )
        assert has_attributes, error_str

    def test_handle_percept_i(self):
        """Test the _handle_percept method of the gym handler where active_gym_dialogue==gym_dialogeu."""
        # setup
        gym_dialogue = cast(
            GymDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.gym_dialogues,
                messages=self.list_of_gym_messages[:3],
            ),
        )
        incoming_message = cast(
            GymMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=gym_dialogue,
                performative=GymMessage.Performative.PERCEPT,
                step_id=self.mocked_step_id,
                observation=self.mocked_observation,
                reward=self.mocked_reward,
                done=True,
                info=self.mocked_info,
            ),
        )

        self.gym_handler.task.proxy_env._active_dialogue = gym_dialogue

        # operation
        with patch.object(
            self.gym_handler.task.proxy_env_queue,
            "put",
        ) as mocked_put:
            self.gym_handler.handle(incoming_message)

        # after
        mocked_put.assert_any_call(incoming_message)

    def test_handle_percept_ii(self):
        """Test the _handle_percept method of the gym handler where active_gym_dialogue!=gym_dialogeu."""
        # setup
        gym_dialogue = cast(
            GymDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.gym_dialogues,
                messages=self.list_of_gym_messages[:3],
            ),
        )
        incoming_message = cast(
            GymMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=gym_dialogue,
                performative=GymMessage.Performative.PERCEPT,
                step_id=self.mocked_step_id,
                observation=self.mocked_observation,
                reward=self.mocked_reward,
                done=True,
                info=self.mocked_info,
            ),
        )

        gym_dialogue_ii = cast(
            GymDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.gym_dialogues,
                messages=self.list_of_gym_messages[:1],
            ),
        )
        self.gym_handler.task.proxy_env._active_dialogue = gym_dialogue_ii

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.gym_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            "gym dialogue not active dialogue.",
        )

    def test_handle_status_i(self):
        """Test the _handle_status method of the gym handler where active_gym_dialogue==gym_dialogeu and reset == success."""
        # setup
        gym_dialogue = cast(
            GymDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.gym_dialogues,
                messages=self.list_of_gym_messages[:1],
            ),
        )
        incoming_message = cast(
            GymMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=gym_dialogue,
                performative=GymMessage.Performative.STATUS,
                content=self.mocked_status_content,
            ),
        )

        self.gym_handler.task.proxy_env._active_dialogue = gym_dialogue

        # operation
        with patch.object(
            self.gym_handler.task.proxy_env_queue,
            "put",
        ) as mocked_put:
            self.gym_handler.handle(incoming_message)

        # after
        mocked_put.assert_any_call(incoming_message)

    def test_handle_status_ii(self):
        """Test the _handle_status method of the gym handler where active_gym_dialogue==gym_dialogeu and reset == success."""
        # setup
        gym_dialogue = cast(
            GymDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.gym_dialogues,
                messages=self.list_of_gym_messages[:1],
            ),
        )
        incoming_message = cast(
            GymMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=gym_dialogue,
                performative=GymMessage.Performative.STATUS,
                content={"reset": "failure"},
            ),
        )

        gym_dialogue_ii = cast(
            GymDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.gym_dialogues,
                messages=self.list_of_gym_messages[:1],
            ),
        )
        self.gym_handler.task.proxy_env._active_dialogue = gym_dialogue_ii

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.gym_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            "gym dialogue not active dialogue.",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the gym handler."""
        # setup
        incoming_message = self.build_incoming_message(
            message_type=GymMessage,
            performative=GymMessage.Performative.RESET,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.gym_handler.handle(incoming_message)

        # after
        gym_dialogue = cast(
            GymDialogue, self.gym_dialogues.get_dialogue(incoming_message)
        )
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle gym message of performative={incoming_message.performative} in dialogue={gym_dialogue}.",
        )

    def test_teardown(self):
        """Test the teardown method of the gym handler."""
        # setup
        self.gym_handler._task_id = self.mocked_task_id

        mock_task_result = Mock(wraps=ApplyResult)
        mock_task_result.ready.return_value = True
        mock_task_result.successful.return_value = False

        # operation
        with patch.object(
            self.gym_handler.task, "teardown"
        ) as mocked_gym_task_teardown:
            with patch.object(
                self.task_manager, "get_task_result", return_value=mock_task_result
            ) as mocked_get_result:
                with patch.object(self.logger, "log") as mock_logger:
                    assert self.gym_handler.teardown() is None

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO,
            "Gym handler: teardown method called.",
        )
        mocked_gym_task_teardown.assert_called_once()
        mocked_get_result.assert_any_call(self.mocked_task_id)
        mock_logger.assert_any_call(
            logging.WARNING,
            "Task not successful!",
        )
