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
"""This module contains the tests for the base classes for the skills."""
import unittest.mock
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from unittest import TestCase, mock
from unittest.mock import MagicMock, Mock, patch

import pytest

import aea
from aea.aea import AEA
from aea.common import Address
from aea.configurations.base import PublicId, SkillComponentConfiguration, SkillConfig
from aea.crypto.wallet import Wallet
from aea.decision_maker.default import GoalPursuitReadiness, OwnershipState, Preferences
from aea.exceptions import AEAException, AEAHandleException, _StopRuntime
from aea.identity.base import Identity
from aea.multiplexer import MultiplexerStatus
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, Dialogues
from aea.registries.resources import Resources
from aea.skills.base import (
    Behaviour,
    Handler,
    Model,
    Skill,
    SkillComponent,
    SkillContext,
    _check_duplicate_classes,
    _print_warning_message_for_non_declared_skill_components,
)

from tests.conftest import (
    ETHEREUM,
    ETHEREUM_PRIVATE_KEY_PATH,
    FETCHAI,
    FETCHAI_PRIVATE_KEY_PATH,
    ROOT_DIR,
    _make_dummy_connection,
)


class TestSkillContext:
    """Test the skill context."""

    @classmethod
    def setup_class(cls):
        """Test the initialisation of the AEA."""
        cls.wallet = Wallet(
            {FETCHAI: FETCHAI_PRIVATE_KEY_PATH, ETHEREUM: ETHEREUM_PRIVATE_KEY_PATH}
        )
        cls.connection = _make_dummy_connection()
        cls.identity = Identity(
            "name", addresses=cls.wallet.addresses, default_address_key=FETCHAI,
        )
        cls.my_aea = AEA(cls.identity, cls.wallet, resources=Resources())
        cls.my_aea.resources.add_connection(cls.connection)
        cls.skill_context = SkillContext(
            cls.my_aea.context, skill=MagicMock(contracts={})
        )

    def test_agent_name(self):
        """Test the agent's name."""
        assert self.skill_context.agent_name == self.my_aea.name

    def test_agent_addresses(self):
        """Test the agent's address."""
        assert self.skill_context.agent_addresses == self.my_aea.identity.addresses

    def test_agent_address(self):
        """Test the default agent's address."""
        assert self.skill_context.agent_address == self.my_aea.identity.address

    def test_connection_status(self):
        """Test the default agent's connection status."""
        assert isinstance(self.skill_context.connection_status, MultiplexerStatus)

    def test_decision_maker_message_queue(self):
        """Test the decision maker's queue."""
        assert isinstance(self.skill_context.decision_maker_message_queue, Queue)

    def test_agent_ownership_state(self):
        """Test the ownership state."""
        assert isinstance(
            self.skill_context.decision_maker_handler_context.ownership_state,
            OwnershipState,
        )

    def test_agent_preferences(self):
        """Test the agents_preferences."""
        assert isinstance(
            self.skill_context.decision_maker_handler_context.preferences, Preferences
        )

    def test_agent_is_ready_to_pursuit_goals(self):
        """Test if the agent is ready to pursuit his goals."""
        assert isinstance(
            self.skill_context.decision_maker_handler_context.goal_pursuit_readiness,
            GoalPursuitReadiness,
        )

    def test_storage(self):
        """Test the agent's storage."""
        assert self.skill_context.storage is None

    def test_message_in_queue(self):
        """Test the 'message_in_queue' property."""
        assert isinstance(self.skill_context.message_in_queue, Queue)

    def test_logger_setter(self):
        """Test the logger setter."""
        logger = self.skill_context.logger
        self.skill_context._logger = None
        self.skill_context.logger = logger
        assert self.skill_context.logger == logger

    def test_agent_context_setter(self):
        """Test the agent context setter."""
        agent_context = self.skill_context._agent_context
        self.skill_context.set_agent_context(agent_context)
        assert self.skill_context.agent_name == agent_context.agent_name
        assert self.skill_context.agent_address == agent_context.address
        assert self.skill_context.agent_addresses == agent_context.addresses

    def test_is_active_property(self):
        """Test is_active property getter."""
        assert self.skill_context.is_active is True

    def test_new_behaviours_queue(self):
        """Test 'new_behaviours_queue' property getter."""
        assert isinstance(self.skill_context.new_behaviours, Queue)

    def test_new_handlers_queue(self):
        """Test 'new_behaviours_queue' property getter."""
        assert isinstance(self.skill_context.new_handlers, Queue)

    def test_search_service_address(self):
        """Test 'search_service_address' property getter."""
        assert (
            self.skill_context.search_service_address
            == self.my_aea.context.search_service_address
        )

    def test_decision_maker_address(self):
        """Test 'decision_maker_address' property getter."""
        assert (
            self.skill_context.decision_maker_address
            == self.my_aea.context.decision_maker_address
        )

    def test_default_ledger_id(self):
        """Test 'default_ledger_id' property getter."""
        assert (
            self.skill_context.default_ledger_id
            == self.my_aea.context.default_ledger_id
        )

    def test_currency_denominations(self):
        """Test 'currency_denominations' property getter."""
        assert (
            self.skill_context.currency_denominations
            == self.my_aea.context.currency_denominations
        )

    def test_namespace(self):
        """Test the 'namespace' property getter."""
        assert isinstance(self.skill_context.namespace, SimpleNamespace)

    @classmethod
    def teardown_class(cls):
        """Test teardown."""
        pass


class SkillContextTestCase(TestCase):
    """Test case for SkillContext class."""

    def test_shared_state_positive(self):
        """Test shared_state property positive result"""
        agent_context = mock.Mock()
        agent_context.shared_state = "shared_state"
        obj = SkillContext(agent_context)
        obj.shared_state

    def test_skill_id_positive(self):
        """Test skill_id property positive result"""
        obj = SkillContext("agent_context")
        obj._skill = mock.Mock()
        obj._skill.config = mock.Mock()
        obj._skill.config.public_id = "public_id"
        obj.skill_id

    @mock.patch("aea.skills.base._default_logger.debug")
    @mock.patch("aea.skills.base.SkillContext.skill_id")
    def test_is_active_positive(self, skill_id_mock, debug_mock):
        """Test is_active setter positive result"""
        obj = SkillContext("agent_context")
        obj.is_active = "value"
        debug_mock.assert_called_once()

    def test_task_manager_positive(self):
        """Test task_manager property positive result"""
        agent_context = mock.Mock()
        agent_context.task_manager = "task_manager"
        obj = SkillContext(agent_context)
        with self.assertRaises(ValueError):
            obj.task_manager
        obj._skill = mock.Mock()
        obj.task_manager

    @mock.patch("aea.skills.base.SimpleNamespace")
    def test_handlers_positive(self, *mocks):
        """Test handlers property positive result"""
        obj = SkillContext("agent_context")
        with self.assertRaises(ValueError):
            obj.handlers
        obj._skill = mock.Mock()
        obj._skill.handlers = {}
        obj.handlers

    @mock.patch("aea.skills.base.SimpleNamespace")
    def test_behaviours_positive(self, *mocks):
        """Test behaviours property positive result"""
        obj = SkillContext("agent_context")
        with self.assertRaises(ValueError):
            obj.behaviours
        obj._skill = mock.Mock()
        obj._skill.behaviours = {}
        obj.behaviours

    def test_logger_positive(self):
        """Test logger property positive result"""
        obj = SkillContext("agent_context")
        obj.logger
        obj._logger = mock.Mock()
        obj.logger


class SkillComponentTestCase(TestCase):
    """Test case for SkillComponent class."""

    def setUp(self):
        """Set the test up."""

        class TestComponent(SkillComponent):
            """Test class for SkillComponent"""

            def parse_module(self, *args):
                """Parse module."""
                pass

            def setup(self, *args):
                """Set up."""
                pass

            def teardown(self, *args):
                """Tear down."""
                pass

        self.TestComponent = TestComponent

    def test_init_no_ctx(self):
        """Test init method no context provided."""

        with self.assertRaises(ValueError):
            self.TestComponent(name="some_name", skill_context=None)
        with self.assertRaises(ValueError):
            self.TestComponent(name=None, skill_context="skill_context")

    def test_skill_id_positive(self):
        """Test skill_id property positive."""
        ctx = mock.Mock()
        ctx.skill_id = "skill_id"
        component = self.TestComponent(
            name="name", skill_context=ctx, configuration=Mock()
        )
        component.skill_id

    def test_config_positive(self):
        """Test config property positive."""
        component = self.TestComponent(
            configuration=Mock(args={}), skill_context="ctx", name="name"
        )
        component.config

    def test_kwargs_not_empty(self):
        """Test the case when there are some kwargs not-empty"""
        kwargs = dict(foo="bar")
        component_name = "component_name"
        skill_context = SkillContext()
        with mock.patch.object(skill_context.logger, "warning") as mock_logger:
            self.TestComponent(component_name, skill_context, **kwargs)
            mock_logger.assert_any_call(
                f"The kwargs={kwargs} passed to {component_name} have not been set!"
            )


def test_load_skill():
    """Test the loading of a skill."""
    agent_context = MagicMock(agent_name="name")
    skill = Skill.from_dir(
        Path(ROOT_DIR, "tests", "data", "dummy_skill"), agent_context=agent_context
    )
    assert isinstance(skill, Skill)


def test_behaviour():
    """Test behaviour initialization."""

    class CustomBehaviour(Behaviour):
        def setup(self) -> None:
            pass

        def teardown(self) -> None:
            pass

        def act(self) -> None:
            pass

    behaviour = CustomBehaviour("behaviour", skill_context=MagicMock())

    # test getters (default values)
    assert behaviour.tick_interval == 0.001
    assert behaviour.start_at is None
    assert behaviour.is_done() is False


def test_behaviour_parse_module_without_configs():
    """Call Behaviour.parse_module without configurations."""
    assert Behaviour.parse_module(MagicMock(), {}, MagicMock()) == {}


def test_behaviour_parse_module_missing_class():
    """Test Behaviour.parse_module when a class is missing."""
    skill_context = SkillContext(
        skill=MagicMock(skill_id=PublicId.from_str("author/name:0.1.0"))
    )
    dummy_behaviours_path = Path(
        ROOT_DIR, "tests", "data", "dummy_skill", "behaviours.py"
    )
    with unittest.mock.patch.object(
        aea.skills.base._default_logger, "warning"
    ) as mock_logger_warning:
        behaviours_by_id = Behaviour.parse_module(
            dummy_behaviours_path,
            {
                "dummy_behaviour": SkillComponentConfiguration("DummyBehaviour"),
                "unknown_behaviour": SkillComponentConfiguration("UnknownBehaviour"),
            },
            skill_context,
        )
        mock_logger_warning.assert_called_with(
            "Behaviour 'UnknownBehaviour' cannot be found."
        )
        assert "dummy_behaviour" in behaviours_by_id


def test_handler_parse_module_without_configs():
    """Call Handler.parse_module without configurations."""
    assert Handler.parse_module(MagicMock(), {}, MagicMock()) == {}


def test_handler_parse_module_missing_class():
    """Test Handler.parse_module when a class is missing."""
    skill_context = SkillContext(
        skill=MagicMock(skill_id=PublicId.from_str("author/name:0.1.0"))
    )
    dummy_handlers_path = Path(ROOT_DIR, "tests", "data", "dummy_skill", "handlers.py")
    with unittest.mock.patch.object(
        aea.skills.base._default_logger, "warning"
    ) as mock_logger_warning:
        behaviours_by_id = Handler.parse_module(
            dummy_handlers_path,
            {
                "dummy_handler": SkillComponentConfiguration("DummyHandler"),
                "unknown_handelr": SkillComponentConfiguration("UnknownHandler"),
            },
            skill_context,
        )
        mock_logger_warning.assert_called_with(
            "Handler 'UnknownHandler' cannot be found."
        )
        assert "dummy_handler" in behaviours_by_id


def test_model_parse_module_without_configs():
    """Call Model.parse_module without configurations."""
    assert Model.parse_module(MagicMock(), {}, MagicMock()) == {}


def test_model_parse_module_missing_class():
    """Test Model.parse_module when a class is missing."""
    skill_context = SkillContext(
        skill=MagicMock(skill_id=PublicId.from_str("author/name:0.1.0"))
    )
    dummy_models_path = Path(ROOT_DIR, "tests", "data", "dummy_skill")
    with unittest.mock.patch.object(
        aea.skills.base._default_logger, "warning"
    ) as mock_logger_warning:
        models_by_id = Model.parse_module(
            dummy_models_path,
            {
                "dummy_model": SkillComponentConfiguration("DummyModel"),
                "unknown_model": SkillComponentConfiguration("UnknownModel"),
            },
            skill_context,
        )
        mock_logger_warning.assert_called_with("Model 'UnknownModel' cannot be found.")
        assert "dummy_model" in models_by_id


def test_check_duplicate_classes():
    """Test check duplicate classes."""
    with pytest.raises(
        AEAException,
        match="Model 'ModelClass' present both in path_1 and path_2. Remove one of them.",
    ):
        _check_duplicate_classes(
            [
                ("ModelClass", MagicMock(__module__="path_1")),
                ("ModelClass", MagicMock(__module__="path_2")),
            ]
        )


def test_print_warning_message_for_non_declared_skill_components():
    """Test the helper function '_print_warning_message_for_non_declared_skill_components'."""
    with unittest.mock.patch.object(
        aea.skills.base._default_logger, "warning"
    ) as mock_logger_warning:
        _print_warning_message_for_non_declared_skill_components(
            SkillContext(),
            {"unknown_class_1", "unknown_class_2"},
            set(),
            "type",
            "path",
        )
        mock_logger_warning.assert_any_call(
            "Class unknown_class_1 of type type found but not declared in the configuration file path."
        )
        mock_logger_warning.assert_any_call(
            "Class unknown_class_2 of type type found but not declared in the configuration file path."
        )


class TestSkill:
    """Test skill attributes."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls.skill = Skill.from_dir(
            Path(ROOT_DIR, "tests", "data", "dummy_skill"),
            MagicMock(agent_name="agent_name"),
        )

    def test_logger(self):
        """Test the logger getter."""
        self.skill.logger

    def test_logger_setter_raises_error(self):
        """Test that the logger setter raises error."""
        with pytest.raises(ValueError, match="Cannot set logger to a skill component."):
            logger = self.skill.logger
            self.skill.logger = logger

    def test_skill_context(self):
        """Test the skill context getter."""
        context = self.skill.skill_context
        assert isinstance(context, SkillContext)


class TestSkillProgrammatic:
    """Test skill attributes."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        skill_context = SkillContext()
        skill_config = SkillConfig(
            name="simple_skill", author="fetchai", version="0.1.0"
        )

        class MyHandler(Handler):
            def setup(self):
                pass

            def handle(self, message: Message):
                pass

            def teardown(self):
                pass

        class MyBehaviour(Behaviour):
            def setup(self):
                pass

            def act(self):
                pass

            def teardown(self):
                pass

        cls.handler_name = "some_handler"
        cls.handler = MyHandler(skill_context=skill_context, name=cls.handler_name)
        cls.model_name = "some_model"
        cls.model = Model(skill_context=skill_context, name=cls.model_name)
        cls.behaviour_name = "some_behaviour"
        cls.behaviour = MyBehaviour(
            skill_context=skill_context, name=cls.behaviour_name
        )
        cls.skill = Skill(
            skill_config,
            skill_context,
            handlers={cls.handler.name: cls.handler},
            models={cls.model.name: cls.model},
            behaviours={cls.behaviour.name: cls.behaviour},
        )

    def test_behaviours(self):
        """Test the behaviours getter on skill context."""
        assert (
            getattr(self.skill.skill_context.behaviours, self.behaviour_name, None)
            == self.behaviour
        )

    def test_handlers(self):
        """Test the handlers getter on skill context."""
        assert (
            getattr(self.skill.skill_context.handlers, self.handler_name, None)
            == self.handler
        )

    def test_models(self):
        """Test the handlers getter on skill context."""
        assert getattr(self.skill.skill_context, self.model_name, None) == self.model


class TestHandlerHandleExceptions:
    """Test exceptions in the handle wrapper."""

    @classmethod
    def setup_class(cls):
        """Setup test class."""

        class StandardExceptionHandler(Handler):
            def setup(self):
                pass

            def handle(self, message: Message):
                raise ValueError("expected")

            def teardown(self):
                pass

        cls.handler = StandardExceptionHandler(skill_context=mock.Mock(), name="name")

    def test_handler_standard_exception(self):
        """Test the handler exception."""
        with pytest.raises(AEAHandleException):
            with pytest.raises(ValueError):
                self.handler.handle_wrapper("msg")

    def test_handler_stop_exception(self):
        """Test the handler exception."""
        with pytest.raises(_StopRuntime):
            with mock.patch.object(self.handler, "handle", side_effect=_StopRuntime()):
                self.handler.handle_wrapper("msg")


class DefaultDialogues(Model, Dialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        Model.__init__(self, **kwargs)

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return 1  # type: ignore

        Dialogues.__init__(
            self,
            self_address=self.context.agent_name,
            end_states=[Mock()],  # type: ignore
            message_class=Message,
            dialogue_class=Dialogue,
            role_from_first_message=role_from_first_message,
        )


def test_model_dialogues_keep_terminal_dialogues_option():
    """Test Model Dialogues class."""
    dialogues = DefaultDialogues(name="test", skill_context=Mock())
    assert (
        DefaultDialogues._keep_terminal_state_dialogues
        == dialogues.is_keep_dialogues_in_terminal_state
    )

    dialogues = DefaultDialogues(
        name="test", skill_context=Mock(), keep_terminal_state_dialogues=True
    )
    assert dialogues.is_keep_dialogues_in_terminal_state is True
    assert (
        DefaultDialogues._keep_terminal_state_dialogues
        == Dialogues._keep_terminal_state_dialogues
    )

    dialogues = DefaultDialogues(
        name="test", skill_context=Mock(), keep_terminal_state_dialogues=False
    )
    assert dialogues.is_keep_dialogues_in_terminal_state is False
    assert (
        DefaultDialogues._keep_terminal_state_dialogues
        == Dialogues._keep_terminal_state_dialogues
    )


def test_setup_teardown_methods():
    """Test skill etup/teardown methods with proper super() calls."""

    def role_from_first_message(  # pylint: disable=unused-argument
        message: Message, receiver_address: Address
    ) -> Dialogue.Role:
        return None  # type: ignore

    class Test(Model, Dialogues):
        def __init__(self, name, skill_context):
            Model.__init__(self, name, skill_context)
            Dialogues.__init__(
                self, "addr", MagicMock(), Message, Dialogue, role_from_first_message
            )

        def setup(self) -> None:
            super().setup()

        def teardown(self) -> None:
            super().teardown()

    skill_context = MagicMock()
    skill_context.skill_id = PublicId("test", "test", "1.0.1")
    t = Test(name="test", skill_context=skill_context)

    with patch.object(t._dialogues_storage, "setup") as mock_setup, patch.object(
        t._dialogues_storage, "teardown"
    ) as mock_teardown:
        t.setup()
        t.teardown()

    mock_setup.assert_called_once()
    mock_teardown.assert_called_once()
