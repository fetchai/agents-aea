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
"""This module sets up test environment for gym skill."""
# pylint: skip-file

from pathlib import Path
from typing import cast

from aea.protocols.dialogue.base import DialogueLabel, DialogueMessage
from aea.skills.tasks import TaskManager
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.gym.custom_types import AnyObject
from packages.fetchai.protocols.gym.message import GymMessage
from packages.fetchai.skills.gym.dialogues import (
    DefaultDialogues,
    GymDialogue,
    GymDialogues,
)
from packages.fetchai.skills.gym.handlers import GymHandler
from packages.fetchai.skills.gym.helpers import ProxyEnv
from packages.fetchai.skills.gym.rl_agent import GoodPriceModel, MyRLAgent, PriceBandit
from packages.fetchai.skills.gym.tasks import GymTask


PACKAGE_ROOT = Path(__file__).parent.parent


class GymTestCase(BaseSkillTestCase):
    """Sets the gym class up for testing."""

    path_to_skill = PACKAGE_ROOT

    def setup(self):
        """Setup the test class."""
        self.nb_steps = 4000
        config_overrides = {
            "handlers": {"gym": {"args": {"nb_steps": self.nb_steps}}},
        }

        super().setup(config_overrides=config_overrides)

        # dialogues
        self.default_dialogues = cast(
            DefaultDialogues, self._skill.skill_context.default_dialogues
        )
        self.gym_dialogues = cast(GymDialogues, self._skill.skill_context.gym_dialogues)

        # handlers
        self.gym_handler = cast(GymHandler, self._skill.skill_context.handlers.gym)

        # models
        self.task = GymTask(
            skill_context=self._skill.skill_context,
            nb_steps=self.nb_steps,
        )

        self.task_manager = cast(TaskManager, self._skill.skill_context.task_manager)
        self.task_manager.start()

        self.logger = self._skill.skill_context.logger

        # mocked objects
        self.dict_str_str = {"some_key": "some_value"}
        self.mocked_task_id = 1
        self.content_bytes = b"some_contents"
        self.mocked_status_content = {"reset": "success"}
        self.mocked_action = AnyObject("some_action")
        self.mocked_observation = AnyObject("some_observation")
        self.mocked_info = AnyObject("some_info")
        self.mocked_step_id = 123
        self.mocked_reward = 3242.23423

        self.mocked_price = 765.23
        self.mocked_beta_a = 2.876
        self.mocked_beta_b = 0.8
        self.mocked_bound = 78
        self.mocked_nb_goods = 10

        self.dummy_gym_dialogue = GymDialogue(
            DialogueLabel(
                ("", ""),
                "some_counterparty_address",
                self._skill.skill_context.agent_address,
            ),
            self._skill.skill_context.agent_address,
            role=GymDialogue.Role.AGENT,
        )

        self.price_bandit = PriceBandit(
            self.mocked_price, self.mocked_beta_a, self.mocked_beta_b
        )
        self.good_price_model = GoodPriceModel(self.mocked_bound)
        self.my_rl_agent = MyRLAgent(self.mocked_nb_goods, self.logger)
        self.proxy_env = ProxyEnv(self._skill.skill_context)

        # list of messages
        self.list_of_gym_messages = (
            DialogueMessage(GymMessage.Performative.RESET, {}),
            DialogueMessage(
                GymMessage.Performative.STATUS, {"content": self.mocked_status_content}
            ),
            DialogueMessage(
                GymMessage.Performative.ACT,
                {"action": self.mocked_action, "step_id": self.mocked_step_id},
            ),
            DialogueMessage(
                GymMessage.Performative.PERCEPT,
                {
                    "step_id": self.mocked_step_id,
                    "observation": self.mocked_observation,
                    "reward": self.mocked_reward,
                    "done": True,
                    "info": self.mocked_info,
                },
            ),
            DialogueMessage(GymMessage.Performative.CLOSE, {}),
        )
