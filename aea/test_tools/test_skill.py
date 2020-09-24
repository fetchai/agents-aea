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
"""This module contains test case classes based on pytest for AEA end-to-end testing."""
import asyncio
import inspect
import logging
import os
from pathlib import Path
from queue import Queue
import time
from typing import Union, cast
from types import SimpleNamespace
from unittest import mock, TestCase

# import pytest

from aea.configurations.base import PublicId
from aea.context.base import AgentContext
from aea.identity.base import Identity
from aea.multiplexer import Multiplexer, MultiplexerStatus, OutBox
from aea.skills.base import Skill
from aea.skills.tasks import TaskManager

from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from agent.skills.generic_buyer.strategy import GenericStrategy


logger = logging.getLogger(__name__)


# @pytest.fixture(autouse=True)
# def cleanup_tests():
#     """Fixture to cleanup the state of a skill"""
#     # cleanup the skill
#     yield  # this is where the testing happens
#     # Teardown : fill with any logic you want


class BaseSkillTestCase(TestCase):

    path_to_skill: Union[Path, str] = Path(".")

    @classmethod
    def setup_class(cls) -> None:
        """Set up the skill test case."""
        # dummy agent context
        dummy_connection_id = PublicId("fetchai", "dummy", "0.1.0")
        dummy_protocol_id = PublicId("fetchai", "dummy_protocol", "0.1.0")
        identity = Identity("dummy_agent_name", "dummy_some_address")

        multiplexer = Multiplexer()
        multiplexer._out_queue = asyncio.Queue()

        cls.context = AgentContext(
            identity=identity,
            connection_status=MultiplexerStatus(),
            outbox=OutBox(multiplexer),
            decision_maker_message_queue=Queue(),
            decision_maker_handler_context=SimpleNamespace(),
            task_manager=TaskManager(),
            default_connection=dummy_connection_id,
            default_routing={dummy_protocol_id: dummy_connection_id},
            search_service_address="dummy_search_service_address",
            decision_maker_address="dummy_decision_maker_address",
        )

        # load skill
        cls.skill = Skill.from_dir(cls.path_to_skill, cls.context)

    @classmethod
    def teardown_class(cls):
        # cleanup
        pass


class SkillBehaviourTestCase(BaseSkillTestCase):

    # CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
    # ROOT_DIR = os.path.join(CUR_PATH, "../..")
    # path_to_skill = Path(ROOT_DIR, "agent/skills/geenric_buyer")
    path_to_skill = Path("/Users/ali/Projects/agents-aea/agent/skills/generic_buyer")

    def test_search_behaviour_setup(self):
        ###########################
        # Version 1: works
        ###########################
        # assert self.skill.models.get("strategy").is_searching is False
        # self.skill.behaviours["search"].setup()
        # assert self.skill.models.get("strategy").is_searching is True
        ###########################
        # Version 2: Does not work
        ###########################
        outbox = self.skill.skill_context.outbox

        assert outbox._multiplexer.out_queue.qsize() == 0
        expected_performative = LedgerApiMessage.Performative.GET_BALANCE
        expected_counterparty = "fetchai/ledger:0.6.0"
        expected_ledger_id = ("fetchai",)
        expected_address = ("some_address",)

        self.skill.behaviours.get("search").setup()
        # time.sleep(5)

        assert outbox._multiplexer.out_queue.qsize() == 1
        actual_message = cast(LedgerApiMessage, outbox._multiplexer.out_queue.get())
        assert actual_message.performative == expected_performative
        assert actual_message.to == expected_counterparty
        assert actual_message.ledger_id == expected_ledger_id
        assert actual_message.address == expected_address


#     def test_search_behaviour_setup_original(self):
#         with mock.patch.object(self.skill.skill_context.strategy, "is_ledger_tx", return_value="False"):
#             assert self.skill.models.get("strategy").is_searching is False
#             self.skill.behaviours["search"].setup()
#             assert self.skill.models.get("strategy").is_searching is True
#
#
# class GenericBuyerSkillBehaviourTestCase(BaseSkillTestCase):
#
#     CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
#     ROOT_DIR = os.path.join(CUR_PATH, "../..")
#     path_to_skill = Path(ROOT_DIR, "packages/fetchai/skills/test_generic_buyer")
#
#     def test_search_behaviour_setup_is_ledger_tx(self):
#         with mock.patch.object(self.skill.models.get("strategy"), "is_ledger_tx", return_value="True"):
#             outbox = self.skill.skill_context.outbox
#
#             assert outbox._multiplexer.out_queue.qsize == 0
#             expected_performative = LedgerApiMessage.Performative.GET_BALANCE
#             expected_counterparty = "fetchai/ledger:0.6.0"
#             expected_ledger_id = "fetchai",
#             expected_address = "some_address",
#
#             self.skill.behaviours["search"].setup()
#
#             assert outbox._multiplexer.out_queue.qsize == 1
#             actual_message = cast(LedgerApiMessage, outbox._multiplexer.out_queue.get())
#             assert actual_message.performative == expected_performative
#             assert actual_message.to == expected_counterparty
#             assert actual_message.ledger_id == expected_ledger_id
#             assert actual_message.address == expected_address
#
#     # @mock.patch.object("strategy.is_ledger_tx", return_value="False")
#     def test_search_behaviour_setup_not_is_ledger_tx(self):
#         self.context.behaviours.search.setup()
#         assert self.context.strategy.is_searching is True
#
#     def test_search_behaviour_act(self):
#         pass
#
#     def test_search_behaviour_teardown(self):
#         pass
#
#
# class SkillHandlerTestCase(TestCase):
#
#     path_to_skill = Path("packages/fetchai/skills/generic_buyer")
#
#     def test_fipa_handler_setup(self):
#         pass
#
#     def test_fipa_handler_handle(self):
#         pass
#
#     def test_fipa_handler_teardown(self):
#         pass
#
#     def test_ledger_api_handler_setup(self):
#         pass
#
#     def test_ledger_api_handler_handle(self):
#         pass
#
#     def test_ledger_api_handler_teardown(self):
#         pass
#
#     def test_oef_search_handler_setup(self):
#         pass
#
#     def test_oef_search_handler_handle(self):
#         pass
#
#     def test_oef_search_handler_teardown(self):
#         pass
#
#     def test_signing_handler_setup(self):
#         pass
#
#     def test_signing_handler_handle(self):
#         pass
#
#     def test_signing_handler_teardown(self):
#         pass
#
#
# class SkillModelTestCase(TestCase):
#
#     path_to_skill = Path("packages/fetchai/skills/generic_buyer")
#
#     def test_strategy(self):
#         pass
