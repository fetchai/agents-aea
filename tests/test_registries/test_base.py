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
"""This module contains the tests for aea/registries/base.py."""
import os
import random
import shutil
import tempfile
import unittest.mock
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest

import aea
import aea.registries.base
from aea.aea import AEA
from aea.configurations.base import ComponentId, ComponentType, PublicId
from aea.configurations.constants import DEFAULT_LEDGER, DEFAULT_PRIVATE_KEY_FILE
from aea.connections.base import Connection
from aea.contracts.base import Contract
from aea.crypto.wallet import Wallet
from aea.helpers.transaction.base import SignedTransaction
from aea.identity.base import Identity
from aea.protocols.base import Protocol
from aea.registries.base import (
    AgentComponentRegistry,
    ComponentRegistry,
    HandlerRegistry,
    PublicIdRegistry,
)
from aea.registries.resources import Resources
from aea.skills.base import Skill

from packages.fetchai.contracts.erc1155.contract import PUBLIC_ID as ERC1155_PUBLIC_ID
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.protocols.state_update import StateUpdateMessage
from packages.fetchai.skills.error import PUBLIC_ID as ERROR_SKILL_PUBLIC_ID

from tests.conftest import CUR_PATH, ROOT_DIR, _make_dummy_connection


class TestContractRegistry:
    """Test the contract registry."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""

        cls.oldcwd = os.getcwd()
        cls.agent_name = "agent_dir_test"
        cls.t = tempfile.mkdtemp()
        cls.agent_folder = os.path.join(cls.t, cls.agent_name)
        shutil.copytree(os.path.join(CUR_PATH, "data", "dummy_aea"), cls.agent_folder)
        os.chdir(cls.agent_folder)

        contract = Contract.from_dir(
            str(Path(ROOT_DIR, "packages", "fetchai", "contracts", "erc1155"))
        )

        cls.registry = AgentComponentRegistry()
        cls.patch = unittest.mock.patch.object(cls.registry.logger, "exception")
        cls.mocked_logger = cls.patch.start()
        cls.registry.register(contract.component_id, cast(Contract, contract))
        cls.expected_contract_ids = {ERC1155_PUBLIC_ID}

    def test_fetch_all(self):
        """Test that the 'fetch_all' method works as expected."""
        contracts = self.registry.fetch_by_type(ComponentType.CONTRACT)
        assert all(isinstance(c, Contract) for c in contracts)
        assert set(c.public_id for c in contracts) == self.expected_contract_ids

    def test_fetch(self):
        """Test that the `fetch` method works as expected."""
        contract_id = ERC1155_PUBLIC_ID
        contract = self.registry.fetch(ComponentId(ComponentType.CONTRACT, contract_id))
        assert isinstance(contract, Contract)
        assert contract.id == contract_id

    def test_unregister(self):
        """Test that the 'unregister' method works as expected."""
        contract_id_removed = ERC1155_PUBLIC_ID
        component_id = ComponentId(ComponentType.CONTRACT, contract_id_removed)
        contract_removed = self.registry.fetch(component_id)
        self.registry.unregister(contract_removed.component_id)
        expected_contract_ids = set(self.expected_contract_ids)
        expected_contract_ids.remove(contract_id_removed)

        assert (
            set(
                c.public_id for c in self.registry.fetch_by_type(ComponentType.CONTRACT)
            )
            == expected_contract_ids
        )

        # restore the contract
        self.registry.register(component_id, contract_removed)

    @classmethod
    def teardown_class(cls):
        """Tear down the tests."""
        cls.mocked_logger.__exit__()
        os.chdir(cls.oldcwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestProtocolRegistry:
    """Test the protocol registry."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""

        cls.oldcwd = os.getcwd()
        cls.agent_name = "agent_dir_test"
        cls.t = tempfile.mkdtemp()
        cls.agent_folder = os.path.join(cls.t, cls.agent_name)
        shutil.copytree(os.path.join(CUR_PATH, "data", "dummy_aea"), cls.agent_folder)
        os.chdir(cls.agent_folder)

        cls.registry = AgentComponentRegistry()
        cls.patch = unittest.mock.patch.object(cls.registry.logger, "exception")
        cls.mocked_logger = cls.patch.start()

        protocol_1 = Protocol.from_dir(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "default")
        )
        protocol_2 = Protocol.from_dir(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "fipa"),
        )
        cls.registry.register(protocol_1.component_id, protocol_1)
        cls.registry.register(protocol_2.component_id, protocol_2)

        cls.expected_protocol_ids = {
            DefaultMessage.protocol_id,
            FipaMessage.protocol_id,
        }

    def test_fetch_all(self):
        """Test that the 'fetch_all' method works as expected."""
        protocols = self.registry.fetch_by_type(ComponentType.PROTOCOL)
        assert all(isinstance(p, Protocol) for p in protocols)
        assert set(p.public_id for p in protocols) == self.expected_protocol_ids

    def test_unregister(self):
        """Test that the 'unregister' method works as expected."""
        protocol_id_removed = DefaultMessage.protocol_id
        component_id = ComponentId(ComponentType.PROTOCOL, protocol_id_removed)
        protocol_removed = self.registry.fetch(component_id)
        self.registry.unregister(component_id)
        expected_protocols_ids = set(self.expected_protocol_ids)
        expected_protocols_ids.remove(protocol_id_removed)

        assert (
            set(
                p.public_id for p in self.registry.fetch_by_type(ComponentType.PROTOCOL)
            )
            == expected_protocols_ids
        )

        # restore the protocol
        self.registry.register(component_id, protocol_removed)

    @classmethod
    def teardown_class(cls):
        """Tear down the tests."""
        cls.mocked_logger.__exit__()
        os.chdir(cls.oldcwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestResources:
    """Test the resources class."""

    @classmethod
    def _patch_logger(cls):
        cls.patch_logger_exception = unittest.mock.patch.object(
            aea.registries.base._default_logger, "exception"
        )
        cls.mocked_logger_exception = cls.patch_logger_exception.__enter__()
        cls.patch_logger_warning = unittest.mock.patch.object(
            aea.registries.base._default_logger, "warning"
        )
        cls.mocked_logger_warning = cls.patch_logger_warning.__enter__()

    @classmethod
    def _unpatch_logger(cls):
        cls.mocked_logger_exception.__exit__()
        cls.mocked_logger_warning.__exit__()

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        # cls._patch_logger() # noqa: E800

        # create temp agent folder
        cls.oldcwd = os.getcwd()
        cls.agent_name = "agent_test" + str(random.randint(0, 1000))  # nosec
        cls.t = tempfile.mkdtemp()
        cls.agent_folder = os.path.join(cls.t, cls.agent_name)
        shutil.copytree(os.path.join(CUR_PATH, "data", "dummy_aea"), cls.agent_folder)
        os.chdir(cls.agent_folder)

        cls.resources = Resources()

        cls.resources.add_component(
            Protocol.from_dir(
                Path(ROOT_DIR, "packages", "fetchai", "protocols", "default")
            )
        )
        cls.resources.add_component(
            Protocol.from_dir(
                Path(ROOT_DIR, "packages", "fetchai", "protocols", "signing")
            )
        )
        cls.resources.add_component(
            Protocol.from_dir(
                Path(ROOT_DIR, "packages", "fetchai", "protocols", "state_update")
            )
        )
        cls.resources.add_component(
            Skill.from_dir(
                Path(CUR_PATH, "data", "dummy_skill"),
                agent_context=MagicMock(agent_name="name"),
            )
        )
        cls.resources.add_component(
            Skill.from_dir(
                Path(ROOT_DIR, "packages", "fetchai", "skills", "error"),
                agent_context=MagicMock(agent_name="name"),
            )
        )

        cls.error_skill_public_id = ERROR_SKILL_PUBLIC_ID
        cls.dummy_skill_public_id = PublicId.from_str("dummy_author/dummy:0.1.0")

        cls.contract_public_id = ERC1155_PUBLIC_ID

    def test_unregister_handler(self):
        """Test that the unregister of handlers work correctly."""
        assert len(self.resources.get_all_handlers()) == 4

        # unregister the error handler and test that it has been actually unregistered.
        # TODO shouldn't we prevent the unregistration of this?
        error_handler = self.resources._handler_registry.fetch(
            (self.error_skill_public_id, "error_handler")
        )
        assert error_handler is not None
        self.resources._handler_registry.unregister(
            (self.error_skill_public_id, "error_handler")
        )
        assert (
            self.resources._handler_registry.fetch(
                (self.error_skill_public_id, "error_handler")
            )
            is None
        )

        # unregister the dummy handler and test that it has been actually unregistered.
        dummy_handler = self.resources._handler_registry.fetch(
            (self.dummy_skill_public_id, "dummy")
        )
        assert dummy_handler is not None
        self.resources._handler_registry.unregister(
            (self.dummy_skill_public_id, "dummy")
        )
        assert (
            self.resources._handler_registry.fetch(
                (self.dummy_skill_public_id, "dummy")
            )
            is None
        )

        # restore the handlers
        self.resources._handler_registry.register(
            (self.error_skill_public_id, "error"), error_handler
        )
        self.resources._handler_registry.register(
            (self.dummy_skill_public_id, "dummy"), dummy_handler
        )
        assert len(self.resources.get_all_handlers()) == 4

    def test_add_and_remove_protocol(self):
        """Test that the 'add protocol' and 'remove protocol' method work correctly."""
        a_protocol = Protocol.from_dir(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "oef_search"),
        )
        self.resources.add_component(cast(Protocol, a_protocol))
        assert self.resources.get_protocol(a_protocol.public_id) == a_protocol
        assert (
            self.resources.get_protocol_by_specification_id(
                a_protocol.protocol_specification_id
            )
            == a_protocol
        )
        # restore state
        self.resources.remove_protocol(a_protocol.public_id)
        assert self.resources.get_protocol(a_protocol.public_id) is None
        assert (
            self.resources.get_protocol_by_specification_id(
                a_protocol.protocol_specification_id
            )
            is None
        )

    def test_get_all_protocols(self):
        """Test get all protocols."""
        all_protocols = self.resources.get_all_protocols()
        assert len(all_protocols) == 3

        expected_pids = {
            DefaultMessage.protocol_id,
            SigningMessage.protocol_id,
            StateUpdateMessage.protocol_id,
        }
        actual_pids = {p.public_id for p in all_protocols}
        assert expected_pids == actual_pids

    def test_add_remove_contract(self):
        """Test that the 'add contract' and 'remove contract' method work correctly."""
        a_contract = Contract.from_dir(
            Path(ROOT_DIR, "packages", "fetchai", "contracts", "erc1155"),
        )
        self.resources.add_component(a_contract)
        assert self.resources.get_contract(a_contract.public_id) == a_contract
        # restore state
        self.resources.remove_contract(a_contract.public_id)
        assert self.resources.get_contract(a_contract.public_id) is None

    def test_get_all_contracts(self):
        """Test get all contracts."""
        a_contract = Contract.from_dir(
            Path(ROOT_DIR, "packages", "fetchai", "contracts", "erc1155"),
        )
        self.resources.add_component(a_contract)
        all_contracts = self.resources.get_all_contracts()
        assert len(all_contracts) == 1
        # restore state
        self.resources.remove_contract(a_contract.public_id)

    def test_add_remove_connection(self):
        """Test that the 'add connection' and 'remove connection' methods work correctly."""
        a_connection = Connection.from_dir(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "oef"),
            data_dir=MagicMock(),
            identity=Identity("name", "address", "public_key"),
            crypto_store=MagicMock(),
        )
        self.resources.add_component(a_connection)
        assert self.resources.get_connection(a_connection.public_id) is not None
        # restore state
        self.resources.remove_connection(a_connection.public_id)

    def test_get_all_connections(self):
        """Test get all connections."""
        a_connection = Connection.from_dir(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "oef"),
            data_dir=MagicMock(),
            identity=Identity("name", "address", "public_key"),
            crypto_store=MagicMock(),
        )
        self.resources.add_component(a_connection)
        all_connections = self.resources.get_all_connections()
        assert len(all_connections) == 1
        assert all_connections[0] == a_connection
        # restore state
        self.resources.remove_connection(a_connection.public_id)

    def test_add_remove_skill(self):
        """Test that the 'remove skill' and 'add skill' method work correctly."""
        a_skill = self.resources.get_skill(self.dummy_skill_public_id)
        self.resources.remove_skill(self.dummy_skill_public_id)
        assert self.resources.get_skill(self.dummy_skill_public_id) is None
        self.resources.add_skill(a_skill)
        assert self.resources.get_skill(self.dummy_skill_public_id) == a_skill

    def test_get_handler(self):
        """Test get handler."""
        handler = self.resources.get_handler(
            DefaultMessage.protocol_id, self.dummy_skill_public_id
        )
        assert handler is not None

    def test_get_handlers(self):
        """Test get handlers."""
        default_handlers = self.resources.get_handlers(DefaultMessage.protocol_id)
        assert len(default_handlers) == 2

    def test_get_behaviours(self):
        """Test get handlers."""
        dummy_behaviours = self.resources.get_behaviours(self.dummy_skill_public_id)
        assert len(dummy_behaviours) == 2

    def test_add_component_raises_error(self):
        """Test add component with unknown component type."""
        a_component = MagicMock()
        a_component.component_type = unittest.mock.PropertyMock(return_value=None)
        with pytest.raises(ValueError):
            self.resources.add_component(a_component)

    def test_register_behaviour_with_already_existing_skill_id(self):
        """Test that registering a behaviour with an already existing skill id behaves as expected."""
        # this should raise an error, since the 'dummy" skill already has a behaviour named "dummy"
        with pytest.raises(
            ValueError,
            match="Item already registered with skill id '{}' and name '{}'".format(
                self.dummy_skill_public_id, "dummy"
            ),
        ):
            self.resources._behaviour_registry.register(
                (self.dummy_skill_public_id, "dummy"), None
            )

    def test_behaviour_registry(self):
        """Test that the behaviour registry behaves as expected."""
        dummy_behaviour = self.resources.get_behaviour(
            self.dummy_skill_public_id, "dummy"
        )
        assert len(self.resources.get_all_behaviours()) == 2
        assert dummy_behaviour is not None

        self.resources._behaviour_registry.unregister(
            (self.dummy_skill_public_id, "dummy")
        )
        assert self.resources.get_behaviour(self.dummy_skill_public_id, "dummy") is None
        assert len(self.resources.get_all_behaviours()) == 1

        self.resources._behaviour_registry.register(
            (self.dummy_skill_public_id, "dummy"), dummy_behaviour
        )

    def test_skill_loading(self):
        """Test that the skills have been loaded correctly."""
        dummy_skill = self.resources.get_skill(self.dummy_skill_public_id)
        skill_context = dummy_skill.skill_context

        handlers = dummy_skill.handlers
        behaviours = dummy_skill.behaviours
        models = dummy_skill.models

        assert len(handlers) == len(skill_context.handlers.__dict__)
        assert len(behaviours) == len(skill_context.behaviours.__dict__)

        assert handlers["dummy"] == skill_context.handlers.dummy
        assert behaviours["dummy"] == skill_context.behaviours.dummy
        assert models["dummy"] == skill_context.dummy

        assert handlers["dummy"].context == dummy_skill.skill_context
        assert behaviours["dummy"].context == dummy_skill.skill_context
        assert models["dummy"].context == dummy_skill.skill_context

    def test_handler_configuration_loading(self):
        """Test that the handler configurations are loaded correctly."""
        default_handlers = self.resources.get_handlers(DefaultMessage.protocol_id)
        assert len(default_handlers) == 2
        handler1, handler2 = default_handlers[0], default_handlers[1]
        dummy_handler = (
            handler1 if handler1.__class__.__name__ == "DummyHandler" else handler2
        )

        assert dummy_handler.config == {"handler_arg_1": 1, "handler_arg_2": "2"}

    def test_behaviour_configuration_loading(self):
        """Test that the behaviour configurations are loaded correctly."""
        dummy_behaviour = self.resources.get_behaviour(
            self.dummy_skill_public_id, "dummy"
        )
        assert dummy_behaviour.config == {"behaviour_arg_1": 1, "behaviour_arg_2": "2"}

    def test_model_configuration_loading(self):
        """Test that the model configurations are loaded correctly."""
        dummy_skill = self.resources.get_skill(self.dummy_skill_public_id)
        assert dummy_skill is not None
        assert len(dummy_skill.models) == 1
        dummy_model = dummy_skill.models["dummy"]

        assert dummy_model.config == {
            "model_arg_1": 1,
            "model_arg_2": "2",
        }

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        # cls._unpatch_logger() # noqa: E800
        os.chdir(cls.oldcwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestFilter:
    """Test the resources class."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        # create temp agent folder
        cls.oldcwd = os.getcwd()
        cls.agent_name = "agent_test" + str(random.randint(0, 1000))  # nosec
        cls.t = tempfile.mkdtemp()
        cls.agent_folder = os.path.join(cls.t, cls.agent_name)
        shutil.copytree(os.path.join(CUR_PATH, "data", "dummy_aea"), cls.agent_folder)
        os.chdir(cls.agent_folder)

        connection = _make_dummy_connection()
        private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
        wallet = Wallet({DEFAULT_LEDGER: private_key_path})
        identity = Identity(
            cls.agent_name,
            address=wallet.addresses[DEFAULT_LEDGER],
            public_key=wallet.public_keys[DEFAULT_LEDGER],
        )
        resources = Resources()

        resources.add_component(
            Skill.from_dir(
                Path(CUR_PATH, "data", "dummy_skill"),
                agent_context=MagicMock(agent_name="name"),
            )
        )

        resources.add_connection(connection)

        cls.aea = AEA(identity, wallet, resources=resources, data_dir=MagicMock())
        cls.aea.setup()

    def test_handle_internal_messages(self):
        """Test that the internal messages are handled."""
        t = SigningMessage(
            performative=SigningMessage.Performative.SIGNED_TRANSACTION,
            signed_transaction=SignedTransaction("ledger_id", {"tx": "v"}),
        )
        t.to = str(PublicId("dummy_author", "dummy", "0.1.0"))
        t.sender = "decision_maker"
        self.aea._filter.handle_internal_message(t)

        internal_handlers_list = self.aea.resources.get_handlers(t.protocol_id)
        assert len(internal_handlers_list) == 1
        internal_handler = internal_handlers_list[0]
        assert len(internal_handler.handled_internal_messages) == 1
        self.aea.teardown()

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        os.chdir(cls.oldcwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestAgentComponentRegistry:
    """Test agent component registry."""

    def setup_class(self):
        """Set up the test."""
        self.registry = AgentComponentRegistry()

    def test_ids(self):
        """Test all ids getter."""
        assert self.registry.ids() == set()

    def test_register_when_component_is_already_registered(self):
        """Test AgentComponentRegistry.register when the component is already registered."""
        component_id = ComponentId(
            ComponentType.PROTOCOL, PublicId("author", "name", "0.1.0")
        )
        component_mock = MagicMock(component_id=component_id)
        self.registry._registered_keys.add(component_id)
        with pytest.raises(
            ValueError, match=r"Component already registered with item id"
        ):
            self.registry.register(component_id, component_mock)
        self.registry._registered_keys = set()

    def test_register_when_component_id_mismatch(self):
        """Test AgentComponentRegistry.register when the component ids mismatch."""
        component_id_1 = ComponentId(
            ComponentType.PROTOCOL, PublicId("author", "name", "0.1.0")
        )
        component_id_2 = ComponentId(
            ComponentType.PROTOCOL, PublicId("author", "name", "0.2.0")
        )
        component_mock = MagicMock(component_id=component_id_1)
        with pytest.raises(
            ValueError, match="Component id '.*' is different to the id '.*' specified."
        ):
            self.registry.register(component_id_2, component_mock)
        self.registry._registered_keys = set()

    def test_unregister_when_no_item_registered(self):
        """Test AgentComponentRegistry.register when the item was not registered."""
        component_id = ComponentId(
            ComponentType.PROTOCOL, PublicId("author", "name", "0.1.0")
        )
        component_mock = MagicMock(component_id=component_id)
        self.registry.register(component_id, component_mock)
        self.registry._registered_keys.remove(component_id)
        with pytest.raises(ValueError, match="No item registered with item id '.*'"):
            self.registry.unregister(component_id)
        self.registry._registered_keys.add(component_id)
        self.registry.unregister(component_id)

    def test_fetch_all(self):
        """Test fetch all."""
        all_components = self.registry.fetch_all()
        assert len(all_components) == 0
        component_id = ComponentId(
            ComponentType.PROTOCOL, PublicId("author", "name", "0.1.0")
        )
        component_mock = MagicMock(component_id=component_id)
        self.registry.register(component_id, component_mock)
        all_components = self.registry.fetch_all()
        assert len(all_components) == 1

        # restore state
        self.registry.unregister(component_id)


class TestComponentRegistry:
    """Tests for the component registry."""

    def setup_class(self):
        """Set up the tests."""
        self.registry = ComponentRegistry()

    def test_ids(self):
        """Test the getter of all ids."""
        assert self.registry.ids() == set()

    def test_ids_non_empty(self):
        """Test ids, non-empty case."""
        dummy_skill = Skill.from_dir(
            Path(CUR_PATH, "data", "dummy_skill"),
            agent_context=MagicMock(agent_name="name"),
        )
        behaviour = next(iter(dummy_skill.behaviours.values()))
        skill_component_id = (dummy_skill.public_id, behaviour.name)
        self.registry.register(skill_component_id, behaviour)

        assert self.registry.ids() == {skill_component_id}

        self.registry.unregister(skill_component_id)

    def test_unregister_when_item_not_registered(self):
        """Test 'unregister' in case the item is not registered."""
        with pytest.raises(ValueError):
            self.registry.unregister(
                (PublicId.from_str("author/name:0.1.0"), "component_name")
            )

    def test_unregister_by_skill_when_item_not_registered(self):
        """Test 'unregister_by_skill' in case the item is not registered."""
        with pytest.raises(
            ValueError, match="No component of skill .* present in the registry."
        ):
            self.registry.unregister_by_skill(PublicId.from_str("author/skill:0.1.0"))

    def test_setup_with_inactive_skill(self):
        """Test setup with inactive skill."""
        mock_item = MagicMock(
            name="name", skill_id="skill", context=MagicMock(is_active=False)
        )
        with unittest.mock.patch.object(
            self.registry, "fetch_all", return_value=[mock_item]
        ):
            with unittest.mock.patch.object(
                self.registry.logger, "debug"
            ) as mock_debug:
                self.registry.setup()
                mock_debug.assert_called_with(
                    f"Ignoring setup() of component {mock_item.name} of skill {mock_item.skill_id}, because the skill is not active."
                )

    def test_fetch_with_latest_version(self):
        """Test fetch with public id :latest version."""
        item_id_1 = PublicId("author", "package", "0.1.0")
        item_id_2 = PublicId("author", "package", "0.2.0")
        item_id_3 = PublicId("author", "package", "0.3.0")
        item_id_latest = PublicId("author", "package")
        name = "name"
        self.registry.register((item_id_1, name), MagicMock(id=1))
        self.registry.register((item_id_3, name), MagicMock(id=3))
        self.registry.register((item_id_2, name), MagicMock(id=2))

        latest = self.registry.fetch((item_id_latest, name))
        assert latest is not None
        assert latest.id == 3

        # restore previous state
        self.registry.unregister((item_id_1, name))
        self.registry.unregister((item_id_2, name))
        self.registry.unregister((item_id_3, name))


class TestHandlerRegistry:
    """Test handler registry."""

    @classmethod
    def setup_class(cls):
        """Set up the tests."""
        cls.registry = HandlerRegistry()

    def test_fetch_skill_id_not_present(self):
        """Test fetch, negative case for skill id.."""
        # register an item
        protocol_id = MagicMock()
        protocol_id.package_version.is_latest = False
        skill_id = MagicMock()
        skill_id.package_version.is_latest = False
        handler_name = "handler"
        handler_mock = MagicMock(name=handler_name, SUPPORTED_PROTOCOL=protocol_id)
        self.registry.register((skill_id, handler_name), handler_mock)

        # fetch an item with right protocol but unknown skill id
        result = self.registry.fetch_by_protocol_and_skill(protocol_id, MagicMock())
        assert result is None

        self.registry.unregister((skill_id, handler_name))

    def test_register_and_unregister_dynamically(self):
        """Test register when protocol id is None."""
        assert len(self.registry._dynamically_added) == 0
        self.registry.register(
            (PublicId.from_str("author/name:0.1.0"), "name"),
            MagicMock(SUPPORTED_PROTOCOL=PublicId.from_str("author/protocol:0.1.0")),
            is_dynamically_added=True,
        )
        assert len(self.registry._dynamically_added) == 1
        self.registry.unregister((PublicId.from_str("author/name:0.1.0"), "name"),)
        assert len(self.registry._dynamically_added) == 0

    def test_register_and_teardown_dynamically(self):
        """Test register when protocol id is None."""
        assert len(self.registry._dynamically_added) == 0
        self.registry.register(
            (PublicId.from_str("author/name:0.1.0"), "name"),
            MagicMock(SUPPORTED_PROTOCOL=PublicId.from_str("author/protocol:0.1.0")),
            is_dynamically_added=True,
        )
        assert len(self.registry._dynamically_added) == 1
        self.registry.teardown()
        assert len(self.registry._dynamically_added) == 0

    def test_register_when_protocol_id_is_none(self):
        """Test register when protocol id is None."""
        with pytest.raises(
            ValueError, match="Please specify a supported protocol for handler class"
        ):
            self.registry.register(
                (PublicId.from_str("author/name:0.1.0"), "name"),
                MagicMock(SUPPORTED_PROTOCOL=None),
            )

    def test_register_when_skill_protocol_id_exist(self):
        """Test register when protocol id is None."""
        skill_id = PublicId.from_str("author/name:0.1.0")
        protocol_id = PublicId.from_str("author/name:0.1.0")
        self.registry.register(
            (skill_id, "name"), MagicMock(SUPPORTED_PROTOCOL=protocol_id)
        )
        with pytest.raises(
            ValueError,
            match="A handler already registered with pair of protocol id .* and skill id .*",
        ):
            self.registry.register(
                (skill_id, "name"), MagicMock(SUPPORTED_PROTOCOL=protocol_id)
            )
        self.registry.unregister((skill_id, "name"))

    def test_unregister_when_no_item_is_registered(self):
        """Test unregister when there is no item with that item id."""
        item_id = (PublicId.from_str("author/name:0.1.0"), "name")
        with pytest.raises(
            ValueError, match="No item registered with component id '.*'"
        ):
            self.registry.unregister(item_id)

    def test_unregister_by_skill(self):
        """Test unregister by skill."""
        skill_id = PublicId.from_str("author/name:0.1.0")
        with pytest.raises(
            ValueError, match="No component of skill .* present in the registry."
        ):
            self.registry.unregister_by_skill(skill_id)


class TestPublicIdRegistry:
    """Tests for the public id registry class."""

    @classmethod
    def setup_class(cls):
        """Set up the class."""
        cls.registry = PublicIdRegistry()

    def test_register_fails_when_version_latest(self):
        """Test that version 'latest' are not allowed for registration."""
        public_id = PublicId("author", "package", "latest")
        with pytest.raises(
            ValueError,
            match=f"Cannot register item with public id 'latest': {public_id}",
        ):
            self.registry.register(public_id, MagicMock())

    def test_register_fails_when_already_registered(self):
        """Test that register fails when the same public id is already registered."""
        public_id = PublicId("author", "package", "0.1.0")
        self.registry._public_id_to_item[public_id] = MagicMock()
        with pytest.raises(
            ValueError, match=f"Item already registered with item id '{public_id}'"
        ):
            self.registry.register(public_id, MagicMock())
        self.registry._public_id_to_item.pop(public_id)

    def test_unregister_fails_when_item_not_registered(self):
        """Test that unregister fails when the item is not registered.."""
        public_id = PublicId("author", "package", "0.1.0")
        with pytest.raises(
            ValueError, match=f"No item registered with item id '{public_id}'"
        ):
            self.registry.unregister(public_id)

    def test_fetch_none(self):
        """Test fetch, negative case."""
        assert self.registry.fetch(MagicMock()) is None
