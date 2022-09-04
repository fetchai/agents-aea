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
"""This module contains the tests for the helpers module of the gym skill."""
# pylint: skip-file

from typing import cast
from unittest.mock import patch

import pytest

from packages.fetchai.protocols.gym.message import GymMessage
from packages.fetchai.skills.gym.dialogues import GymDialogue
from packages.fetchai.skills.gym.tests.intermediate_class import GymTestCase


class TestProxyEnv(GymTestCase):
    """Test ProxyEnv of gym."""

    is_agent_to_agent_messages = False

    def test__init__(self):
        """Test the __init__ method of the ProxyEnv class."""
        assert self.proxy_env._is_rl_agent_trained is False
        assert self.proxy_env._step_count == 0
        assert self.proxy_env._active_dialogue is None

    def test_properties(self):
        """Test the properties of the ProxyEnv class."""
        assert self.proxy_env.gym_dialogues == self.gym_dialogues

        with pytest.raises(ValueError, match="GymDialogue not set yet."):
            assert self.proxy_env.active_gym_dialogue
        self.proxy_env._active_dialogue = self.dummy_gym_dialogue
        assert self.proxy_env.active_gym_dialogue == self.dummy_gym_dialogue

        assert self.proxy_env.queue == self.proxy_env._queue
        assert self.proxy_env.is_rl_agent_trained is False

    def test_step_i(self):
        """Test the step method of the ProxyEnv class where no exception."""
        # setup
        action = "some_action"
        gym_dialogue = cast(
            GymDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.gym_dialogues,
                messages=self.list_of_gym_messages[:2],
            ),
        )
        self.proxy_env._active_dialogue = gym_dialogue
        percept_msg = self.build_incoming_message(
            message_type=GymMessage,
            performative=GymMessage.Performative.PERCEPT,
            step_id=self.proxy_env._step_count + 1,
            observation=self.mocked_observation,
            reward=self.mocked_reward,
            done=True,
            info=self.mocked_info,
        )

        # operation
        with patch.object(
            self.proxy_env._queue, "get", return_value=percept_msg
        ) as mocked_q_get:
            (
                actual_observation,
                actual_reward,
                actual_done,
                actual_info,
            ) = self.proxy_env.step(action)

        # after

        # _encode_and_send_action
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=GymMessage,
            performative=GymMessage.Performative.ACT,
            to=gym_dialogue.dialogue_label.dialogue_opponent_addr,
            sender=str(self.skill.skill_context.skill_id),
            action=GymMessage.AnyObject(action),
            step_id=self.proxy_env._step_count,
        )
        assert has_attributes, error_str

        mocked_q_get.assert_called_with(block=True, timeout=None)

        assert actual_observation == self.mocked_observation.any
        assert actual_reward == self.mocked_reward
        assert actual_done is True
        assert actual_info == self.mocked_info.any

    def test_step_ii(self):
        """Test the step method of the ProxyEnv class where performative is NOT percept."""
        # setup
        action = "some_action"
        gym_dialogue = cast(
            GymDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.gym_dialogues,
                messages=self.list_of_gym_messages[:2],
            ),
        )
        self.proxy_env._active_dialogue = gym_dialogue
        invalid_percept_msg = self.build_incoming_message(
            message_type=GymMessage,
            performative=GymMessage.Performative.RESET,
        )

        # operation
        with patch.object(
            self.proxy_env._queue, "get", return_value=invalid_percept_msg
        ) as mocked_q_get:
            with pytest.raises(
                ValueError,
                match=f"Unexpected performative. Expected={GymMessage.Performative.PERCEPT} got={invalid_percept_msg.performative}",
            ):
                self.proxy_env.step(action)

        # # after

        # _encode_and_send_action
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=GymMessage,
            performative=GymMessage.Performative.ACT,
            to=gym_dialogue.dialogue_label.dialogue_opponent_addr,
            sender=str(self.skill.skill_context.skill_id),
            action=GymMessage.AnyObject(action),
            step_id=self.proxy_env._step_count,
        )
        assert has_attributes, error_str

        mocked_q_get.assert_called_with(block=True, timeout=None)

    def test_step_iii(self):
        """Test the step method of the ProxyEnv class where performative is NOT percept."""
        # setup
        action = "some_action"
        gym_dialogue = cast(
            GymDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.gym_dialogues,
                messages=self.list_of_gym_messages[:2],
            ),
        )
        self.proxy_env._active_dialogue = gym_dialogue
        invalid_percept_msg = self.build_incoming_message(
            message_type=GymMessage,
            performative=GymMessage.Performative.PERCEPT,
            step_id=self.proxy_env._step_count,
            observation=self.mocked_observation,
            reward=self.mocked_reward,
            done=True,
            info=self.mocked_info,
        )

        # operation
        with patch.object(
            self.proxy_env._queue, "get", return_value=invalid_percept_msg
        ) as mocked_q_get:
            with pytest.raises(
                ValueError,
                match=f"Unexpected step id! expected={self.proxy_env._step_count+1}, actual={self.proxy_env._step_count}",
            ):
                self.proxy_env.step(action)

        # # after

        # _encode_and_send_action
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=GymMessage,
            performative=GymMessage.Performative.ACT,
            to=gym_dialogue.dialogue_label.dialogue_opponent_addr,
            sender=str(self.skill.skill_context.skill_id),
            action=GymMessage.AnyObject(action),
            step_id=self.proxy_env._step_count,
        )
        assert has_attributes, error_str

        mocked_q_get.assert_called_with(block=True, timeout=None)

    def test_reset_i(self):
        """Test the reset method of the ProxyEnv class where no exception."""
        # setup
        status_msg = self.build_incoming_message(
            message_type=GymMessage,
            performative=GymMessage.Performative.STATUS,
            content=self.mocked_status_content,
        )

        # operation
        with patch.object(
            self.proxy_env._queue, "get", return_value=status_msg
        ) as mocked_q_get:
            self.proxy_env.reset()

        # after
        assert self.proxy_env._step_count == 0
        assert self.proxy_env._is_rl_agent_trained is False
        assert self.proxy_env._active_dialogue is not None

        self.assert_quantity_in_outbox(1)
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=GymMessage,
            performative=GymMessage.Performative.RESET,
            to=self.proxy_env.gym_address,
            sender=str(self.skill.skill_context.skill_id),
        )
        assert has_attributes, error_str

        mocked_q_get.assert_called_with(block=True, timeout=None)

    def test_reset_ii(self):
        """Test the reset method of the ProxyEnv class where performative is NOT status."""
        # setup
        invalid_msg = self.build_incoming_message(
            message_type=GymMessage,
            performative=GymMessage.Performative.RESET,
        )

        # operation
        with patch.object(
            self.proxy_env._queue, "get", return_value=invalid_msg
        ) as mocked_q_get:
            with pytest.raises(
                ValueError,
                match=f"Unexpected performative. Expected={GymMessage.Performative.STATUS} got={invalid_msg.performative}",
            ):
                self.proxy_env.reset()

        # after
        assert self.proxy_env._step_count == 0
        assert self.proxy_env._is_rl_agent_trained is False
        assert self.proxy_env._active_dialogue is not None

        self.assert_quantity_in_outbox(1)
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=GymMessage,
            performative=GymMessage.Performative.RESET,
            to=self.proxy_env.gym_address,
            sender=str(self.skill.skill_context.skill_id),
        )
        assert has_attributes, error_str

        mocked_q_get.assert_called_with(block=True, timeout=None)

    def test_close_i(self):
        """Test the close method of the ProxyEnv class."""
        # setup
        self.proxy_env._is_rl_agent_trained = True
        gym_dialogue = cast(
            GymDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.gym_dialogues,
                messages=self.list_of_gym_messages[:4],
            ),
        )
        self.proxy_env._active_dialogue = gym_dialogue

        # operation
        self.proxy_env.close()

        # after
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=GymMessage,
            performative=GymMessage.Performative.CLOSE,
            to=gym_dialogue.dialogue_label.dialogue_opponent_addr,
            sender=str(self.skill.skill_context.skill_id),
        )
        assert has_attributes, error_str
