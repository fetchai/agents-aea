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

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.nb_steps = 4000
        config_overrides = {
            "handlers": {"gym": {"args": {"nb_steps": cls.nb_steps}}},
        }

        super().setup(config_overrides=config_overrides)

        # dialogues
        cls.default_dialogues = cast(
            DefaultDialogues, cls._skill.skill_context.default_dialogues
        )
        cls.gym_dialogues = cast(GymDialogues, cls._skill.skill_context.gym_dialogues)

        # handlers
        cls.gym_handler = cast(GymHandler, cls._skill.skill_context.handlers.gym)

        # models
        cls.task = GymTask(
            skill_context=cls._skill.skill_context,
            nb_steps=cls.nb_steps,
        )

        cls.task_manager = cast(TaskManager, cls._skill.skill_context.task_manager)
        cls.task_manager.start()

        cls.logger = cls._skill.skill_context.logger

        # mocked objects
        cls.dict_str_str = {"some_key": "some_value"}
        cls.mocked_task_id = 1
        cls.content_bytes = b"some_contents"
        cls.mocked_status_content = {"reset": "success"}
        cls.mocked_action = AnyObject("some_action")
        cls.mocked_observation = AnyObject("some_observation")
        cls.mocked_info = AnyObject("some_info")
        cls.mocked_step_id = 123
        cls.mocked_reward = 3242.23423

        cls.mocked_price = 765.23
        cls.mocked_beta_a = 2.876
        cls.mocked_beta_b = 0.8
        cls.mocked_bound = 78
        cls.mocked_nb_goods = 10

        cls.dummy_gym_dialogue = GymDialogue(
            DialogueLabel(
                ("", ""),
                "some_counterparty_address",
                cls._skill.skill_context.agent_address,
            ),
            cls._skill.skill_context.agent_address,
            role=GymDialogue.Role.AGENT,
        )

        cls.price_bandit = PriceBandit(
            cls.mocked_price, cls.mocked_beta_a, cls.mocked_beta_b
        )
        cls.good_price_model = GoodPriceModel(cls.mocked_bound)
        cls.my_rl_agent = MyRLAgent(cls.mocked_nb_goods, cls.logger)
        cls.proxy_env = ProxyEnv(cls._skill.skill_context)

        # list of messages
        cls.list_of_gym_messages = (
            DialogueMessage(GymMessage.Performative.RESET, {}),
            DialogueMessage(
                GymMessage.Performative.STATUS, {"content": cls.mocked_status_content}
            ),
            DialogueMessage(
                GymMessage.Performative.ACT,
                {"action": cls.mocked_action, "step_id": cls.mocked_step_id},
            ),
            DialogueMessage(
                GymMessage.Performative.PERCEPT,
                {
                    "step_id": cls.mocked_step_id,
                    "observation": cls.mocked_observation,
                    "reward": cls.mocked_reward,
                    "done": True,
                    "info": cls.mocked_info,
                },
            ),
            DialogueMessage(GymMessage.Performative.CLOSE, {}),
        )
