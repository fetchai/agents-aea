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
"""This module contains the tests for aea/registries/filter.py."""
import queue
import unittest.mock
from unittest.mock import MagicMock

import aea
from aea.configurations.base import PublicId, SkillConfig
from aea.protocols.signing import SigningMessage
from aea.registries.filter import Filter
from aea.registries.resources import Resources
from aea.skills.base import Skill

from tests.data.dummy_skill.behaviours import DummyBehaviour


class TestFilter:
    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls.resources = Resources()
        cls.decision_make_queue = queue.Queue()
        cls.filter = Filter(cls.resources, cls.decision_make_queue)

    def test_get_active_handlers_skill_id_none(self):
        """Test get active handlers with skill id None."""
        protocol_id = PublicId.from_str("author/name:0.1.0")
        active_handlers = self.filter.get_active_handlers(protocol_id, skill_id=None)
        assert len(active_handlers) == 0

    def test_get_active_handlers_skill_id_not_none(self):
        """Test get active handlers with skill id not None."""
        protocol_id = PublicId.from_str("author/name:0.1.0")
        skill_id = PublicId.from_str("author/skill:0.1.0")
        active_handlers = self.filter.get_active_handlers(
            protocol_id, skill_id=skill_id
        )
        assert len(active_handlers) == 0

    def test_get_active_behaviours(self):
        """Test get active behaviours."""
        active_behaviours = self.filter.get_active_behaviours()
        assert len(active_behaviours) == 0

    def test_handle_internal_messages_when_empty(self):
        """Test handle internal messages when queue is empty."""
        with unittest.mock.patch.object(
            self.decision_make_queue, "empty", side_effect=[False, True]
        ):
            with unittest.mock.patch.object(
                aea.registries.filter.logger, "warning"
            ) as mock_logger_warning:
                self.filter.handle_internal_messages()
                mock_logger_warning.assert_called_with(
                    "The decision maker out queue is unexpectedly empty."
                )

    def test_handle_internal_message_when_none(self):
        """Test handle internal message when the received message is None."""
        self.decision_make_queue.put(None)
        with unittest.mock.patch.object(
            aea.registries.filter.logger, "warning"
        ) as mock_logger_warning:
            self.filter.handle_internal_messages()
            mock_logger_warning.assert_called_with(
                "Got 'None' while processing internal messages."
            )

    def test_handle_internal_message_when_unknown_data_type(self):
        """Test handle internal message when the received message is of unknown data type."""
        msg = MagicMock()
        self.decision_make_queue.put(msg)
        with unittest.mock.patch.object(
            aea.registries.filter.logger, "warning"
        ) as mock_logger_warning:
            self.filter.handle_internal_messages()
            mock_logger_warning.assert_called_with(
                "Cannot handle a {} message.".format(type(msg))
            )
        assert self.decision_make_queue.empty()

    def test_handle_internal_message_new_behaviours(self):
        """Test handle internal message when there are new behaviours to register."""
        skill = Skill(
            SkillConfig("name", "author", "0.1.0"),
            handlers={},
            behaviours={},
            models={},
        )
        self.resources.add_skill(skill)
        new_behaviour = DummyBehaviour(name="dummy2", skill_context=skill.skill_context)
        skill.skill_context.new_behaviours.put(new_behaviour)
        self.filter.handle_internal_messages()

        assert self.decision_make_queue.empty()
        assert len(self.resources.behaviour_registry.fetch_all()) == 1
        # restore previous state
        self.resources.remove_skill(skill.public_id)
        assert len(self.resources.behaviour_registry.fetch_all()) == 0

    def test_handle_internal_message_new_behaviours_with_error(self):
        """Test handle internal message when an error happens while registering a new behaviour."""
        skill = Skill(
            SkillConfig("name", "author", "0.1.0"),
            handlers={},
            behaviours={},
            models={},
        )
        self.resources.add_skill(skill)
        new_behaviour = DummyBehaviour(name="dummy2", skill_context=skill.skill_context)
        with unittest.mock.patch.object(
            self.resources.behaviour_registry, "register", side_effect=ValueError
        ):
            with unittest.mock.patch.object(
                aea.registries.filter.logger, "warning"
            ) as mock_logger_warning:
                skill.skill_context.new_behaviours.put(new_behaviour)
                self.filter.handle_internal_messages()

        mock_logger_warning.assert_called_with(
            "Error when trying to add a new behaviour: "
        )
        assert self.decision_make_queue.empty()
        assert len(self.resources.behaviour_registry.fetch_all()) == 0
        # restore previous state
        self.resources.component_registry.unregister(skill.component_id)

    def test_handle_signing_message(self):
        """Test the handling of a signing message."""
        public_id = "author/non_existing_skill:0.1.0"
        message = SigningMessage(
            SigningMessage.Performative.ERROR,
            skill_callback_ids=(public_id,),
            skill_callback_info={},
            error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
        )
        self.decision_make_queue.put(message)
        with unittest.mock.patch.object(
            aea.registries.filter.logger, "warning"
        ) as mock_logger_warning:
            self.filter.handle_internal_messages()
            mock_logger_warning.assert_called_with(
                f"No internal handler fetched for skill_id={public_id}"
            )

        assert self.decision_make_queue.empty()
