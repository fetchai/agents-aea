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
import unittest.mock
from unittest.mock import MagicMock

import pytest

from aea.configurations.base import PublicId, SkillConfig
from aea.helpers.async_friendly_queue import AsyncFriendlyQueue
from aea.registries.filter import Filter
from aea.registries.resources import Resources
from aea.skills.base import Skill

from packages.fetchai.protocols.signing import SigningMessage

from tests.data.dummy_skill.behaviours import DummyBehaviour
from tests.data.dummy_skill.handlers import DummyHandler


class TestFilter:
    """Test class for filter."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls.resources = Resources()
        cls.decision_make_queue = AsyncFriendlyQueue()
        cls.filter = Filter(cls.resources, cls.decision_make_queue)

    @pytest.mark.asyncio
    async def test_get_internal_message(self):
        """Test get internal message."""
        msg = MagicMock()
        self.decision_make_queue.put(msg)
        _msg = await self.filter.get_internal_message()
        assert msg == _msg, "Should get message"

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

    def test_handle_internal_message_when_none(self):
        """Test handle internal message when the received message is None."""
        with unittest.mock.patch.object(
            self.filter.logger, "warning"
        ) as mock_logger_warning:
            self.filter.handle_internal_message(None)
            mock_logger_warning.assert_called_with(
                "Got 'None' while processing internal messages."
            )

    def test_handle_internal_message_when_no_handler(self):
        """Test handle internal message when the message has no matching handler."""
        msg = MagicMock()
        msg.to = "author/name:0.1.0"
        with unittest.mock.patch.object(
            self.filter.logger, "warning"
        ) as mock_logger_warning:
            self.filter.handle_internal_message(msg)
            mock_logger_warning.assert_called_with(
                "No internal handler fetched for skill_id={}".format(msg.to)
            )
        assert self.decision_make_queue.empty()

    def test_handle_internal_message_when_invalid_to(self):
        """Test handle internal message when the message has an invalid to."""
        msg = MagicMock()
        msg.to = "author!name"
        with unittest.mock.patch.object(
            self.filter.logger, "warning"
        ) as mock_logger_warning:
            self.filter.handle_internal_message(msg)
            mock_logger_warning.assert_called_with(
                "Invalid public id as destination={}".format(msg.to)
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
        self.filter.handle_new_handlers_and_behaviours()

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
                self.filter.logger, "warning"
            ) as mock_logger_warning:
                skill.skill_context.new_behaviours.put(new_behaviour)
                self.filter.handle_new_handlers_and_behaviours()

        mock_logger_warning.assert_called_with(
            "Error when trying to add a new behaviour: "
        )
        assert self.decision_make_queue.empty()
        assert len(self.resources.behaviour_registry.fetch_all()) == 0
        # restore previous state
        self.resources.component_registry.unregister(skill.component_id)

    def test_handle_internal_message_new_handlers(self):
        """Test handle internal message when there are new handlers to register."""
        skill = Skill(
            SkillConfig("name", "author", "0.1.0"),
            handlers={},
            behaviours={},
            models={},
        )
        self.resources.add_skill(skill)
        new_handler = DummyHandler(name="dummy2", skill_context=skill.skill_context)
        skill.skill_context.new_handlers.put(new_handler)
        self.filter.handle_new_handlers_and_behaviours()

        assert self.decision_make_queue.empty()
        assert len(self.resources.handler_registry.fetch_all()) == 1
        # restore previous state
        self.resources.remove_skill(skill.public_id)
        assert len(self.resources.handler_registry.fetch_all()) == 0

    def test_handle_internal_message_new_handlers_with_error(self):
        """Test handle internal message when an error happens while registering a new handler."""
        skill = Skill(
            SkillConfig("name", "author", "0.1.0"),
            handlers={},
            behaviours={},
            models={},
        )
        self.resources.add_skill(skill)
        new_handler = DummyHandler(name="dummy2", skill_context=skill.skill_context)
        with unittest.mock.patch.object(
            self.resources.handler_registry, "register", side_effect=ValueError
        ):
            with unittest.mock.patch.object(
                self.filter.logger, "warning"
            ) as mock_logger_warning:
                skill.skill_context.new_handlers.put(new_handler)
                self.filter.handle_new_handlers_and_behaviours()

        mock_logger_warning.assert_called_with(
            "Error when trying to add a new handler: "
        )
        assert self.decision_make_queue.empty()
        assert len(self.resources.handler_registry.fetch_all()) == 0
        # restore previous state
        self.resources.component_registry.unregister(skill.component_id)

    def test_handle_signing_message(self):
        """Test the handling of a signing message."""
        public_id = "author/non_existing_skill:0.1.0"
        message = SigningMessage(
            SigningMessage.Performative.ERROR,
            error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
        )
        message.to = public_id
        with unittest.mock.patch.object(
            self.filter.logger, "warning"
        ) as mock_logger_warning:
            self.filter.handle_internal_message(message)
            mock_logger_warning.assert_called_with(
                f"No internal handler fetched for skill_id={public_id}"
            )

        assert self.decision_make_queue.empty()
