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
"""This module contains tests for aea/aea_builder.py."""
import os
import re
from pathlib import Path
from typing import Collection
from unittest.mock import Mock, patch

import pytest

from aea.aea import AEA
from aea.aea_builder import AEABuilder, _DependenciesManager
from aea.components.base import Component
from aea.configurations.base import (
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    ConnectionConfig,
    ProtocolConfig,
    PublicId,
    SkillConfig,
)
from aea.configurations.constants import DEFAULT_LEDGER, DEFAULT_PRIVATE_KEY_FILE
from aea.contracts.base import Contract
from aea.exceptions import AEAException
from aea.helpers.exception_policy import ExceptionPolicyEnum
from aea.protocols.base import Protocol
from aea.protocols.default import DefaultMessage
from aea.registries.resources import Resources
from aea.skills.base import Skill

from tests.conftest import (
    CUR_PATH,
    FETCHAI_PRIVATE_KEY_PATH,
    ROOT_DIR,
    _make_dummy_connection,
    skip_test_windows,
)

dummy_skill_path = os.path.join(CUR_PATH, "data", "dummy_skill")
contract_path = os.path.join(ROOT_DIR, "packages", "fetchai", "contracts", "erc1155")


@skip_test_windows
def test_default_timeout_for_agent():
    """Tests agents loop sleep timeout set by AEABuilder.DEFAULT_AGENT_LOOP_TIMEOUT."""
    agent_name = "MyAgent"
    private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
    builder = AEABuilder()
    builder.set_name(agent_name)
    builder.add_private_key(DEFAULT_LEDGER, private_key_path)

    aea = builder.build()
    assert aea._timeout == builder.DEFAULT_AGENT_LOOP_TIMEOUT

    builder = AEABuilder()
    builder.set_name(agent_name)
    builder.add_private_key(DEFAULT_LEDGER, private_key_path)
    builder.set_timeout(100)

    aea = builder.build()
    assert aea._timeout == 100


def test_add_package_already_existing():
    """
    Test the case when we try to add a package (already added) to the AEA builder.

    It should fail because the package is already present into the builder.
    """
    builder = AEABuilder()
    fipa_package_path = Path(ROOT_DIR) / "packages" / "fetchai" / "protocols" / "fipa"
    builder.add_component(ComponentType.PROTOCOL, fipa_package_path)

    expected_message = re.escape(
        "Component 'fetchai/fipa:0.4.0' of type 'protocol' already added."
    )
    with pytest.raises(AEAException, match=expected_message):
        builder.add_component(ComponentType.PROTOCOL, fipa_package_path)


def test_when_package_has_missing_dependency():
    """Test the case when the builder tries to load the packages, but fails because of a missing dependency."""
    builder = AEABuilder()
    expected_message = re.escape(
        "Package 'fetchai/oef:0.6.0' of type 'connection' cannot be added. "
        "Missing dependencies: ['(protocol, fetchai/oef_search:0.3.0)']"
    )
    with pytest.raises(AEAException, match=expected_message):
        # connection "fetchai/oef:0.1.0" requires
        # "fetchai/oef_search:0.3.0" and "fetchai/fipa:0.4.0" protocols.
        builder.add_component(
            ComponentType.CONNECTION,
            Path(ROOT_DIR) / "packages" / "fetchai" / "connections" / "oef",
        )


class TestReentrancy:
    """
    Test the reentrancy of the AEABuilder class, when the components are loaded from directories.

    Namely, it means that multiple calls to the AEABuilder class
    should instantiate different AEAs in all their components.

    For example:

        builder = AEABuilder()
        ... # add components etc.
        aea1 = builder.build()
        aea2 = builder.build()

    Instances of components of aea1 are not shared with the aea2's ones.
    """

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        protocol_path = os.path.join(
            ROOT_DIR, "packages", "fetchai", "protocols", "oef_search"
        )
        connection_path = os.path.join(
            ROOT_DIR, "packages", "fetchai", "connections", "soef"
        )

        builder = AEABuilder()
        builder.set_name("aea1")
        builder.add_private_key(DEFAULT_LEDGER)
        builder.add_protocol(protocol_path)
        builder.add_contract(contract_path)
        builder.add_connection(connection_path)
        builder.add_skill(dummy_skill_path)

        cls.aea1 = builder.build()

        builder.set_name("aea2")
        cls.aea2 = builder.build()

    @staticmethod
    def are_components_different(
        components_a: Collection[Component], components_b: Collection[Component]
    ) -> None:
        """
        Compare collections of component instances.

        It only makes sense if they have the same number of elements and the same component ids.
        """
        assert len(components_a) == len(
            components_b
        ), "Cannot compare, number of components is different."
        assert {c.component_id for c in components_a} == {
            c.component_id for c in components_b
        }, "Cannot compare, component ids are different."

        d1 = {c.component_id: c for c in components_a}
        d2 = {c.component_id: c for c in components_b}
        assert all(d1[k] is not d2[k] for k in d1.keys())

        c1 = {c.component_id: c.configuration for c in components_a}
        c2 = {c.component_id: c.configuration for c in components_b}
        assert all(c1[k] is not c2[k] for k in c1.keys())

    def test_skills_instances_are_different(self):
        """Test that skill instances are different."""
        aea1_skills = self.aea1.resources.get_all_skills()
        aea2_skills = self.aea2.resources.get_all_skills()
        self.are_components_different(aea1_skills, aea2_skills)

    def test_protocols_instances_are_different(self):
        """Test that protocols instances are different."""
        aea1_protocols = self.aea1.resources.get_all_protocols()
        aea2_protocols = self.aea2.resources.get_all_protocols()
        self.are_components_different(aea1_protocols, aea2_protocols)

    def test_contracts_instances_are_different(self):
        """Test that contract instances are different."""
        aea1_contracts = self.aea1.resources.get_all_contracts()
        aea2_contracts = self.aea2.resources.get_all_contracts()
        self.are_components_different(aea1_contracts, aea2_contracts)

    def test_connections_instances_are_different(self):
        """Test that connection instances are different."""
        aea1_connections = self.aea1.multiplexer.connections
        aea2_connections = self.aea2.multiplexer.connections
        self.are_components_different(aea1_connections, aea2_connections)


def test_multiple_builds_with_private_keys():
    """Test multiple calls to the 'build()' method when adding custom private keys."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key(DEFAULT_LEDGER, FETCHAI_PRIVATE_KEY_PATH)

    # the first call works
    aea_1 = builder.build()
    assert isinstance(aea_1, AEA)

    # the second call fails
    with pytest.raises(ValueError, match="Cannot build.*"):
        builder.build()

    # after reset, it works
    builder.reset()
    builder.set_name("aea_1")
    builder.add_private_key(DEFAULT_LEDGER, FETCHAI_PRIVATE_KEY_PATH)
    aea_2 = builder.build()
    assert isinstance(aea_2, AEA)


def test_multiple_builds_with_component_instance():
    """Test multiple calls to the 'build()' method when adding component instances."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key(DEFAULT_LEDGER)

    a_protocol = Protocol(
        ProtocolConfig("a_protocol", "author", "0.1.0"), DefaultMessage
    )
    builder.add_component_instance(a_protocol)

    # the first call works
    aea_1 = builder.build()
    assert isinstance(aea_1, AEA)

    # the second call fails
    with pytest.raises(ValueError, match="Cannot build.*"):
        builder.build()

    # after reset, it works
    builder.reset()
    builder.set_name("aea_1")
    builder.add_private_key(DEFAULT_LEDGER)
    builder.add_component_instance(a_protocol)
    aea_2 = builder.build()
    assert isinstance(aea_2, AEA)


def test_dependency_manager_highest_version():
    """Test dependency version priority."""
    dep_manager = _DependenciesManager()
    dep_manager.add_component(ProtocolConfig("a_protocol", "author", "0.1.0"))
    dep_manager.add_component(ProtocolConfig("a_protocol", "author", "0.2.0"))

    assert len(dep_manager.dependencies_highest_version) == 1
    assert list(dep_manager.dependencies_highest_version)[0].version == "0.2.0"

    assert len(dep_manager.protocols) == 2

    assert len(dep_manager.skills) == 0
    assert len(dep_manager.contracts) == 0


def test_remove_component_not_exists():
    """Test component remove not exists."""
    dep_manager = _DependenciesManager()
    with pytest.raises(ValueError, match=r"Component .* of type .* not present."):
        dep_manager.remove_component(
            ProtocolConfig("a_protocol", "author", "0.1.0").component_id
        )


def test_remove_component_depends_on_fail():
    """Test component remove fails cause dependency."""
    dep_manager = _DependenciesManager()
    protocol = ProtocolConfig("a_protocol", "author", "0.1.0")
    dep_manager.add_component(protocol)
    dep_manager.add_component(
        SkillConfig("skill", "author", "0.1.0", protocols=[protocol.public_id])
    )

    with pytest.raises(
        ValueError,
        match=r"Cannot remove component .* of type .*. Other components depends on it: .*",
    ):
        dep_manager.remove_component(protocol.component_id)


def test_remove_component_success():
    """Test remove registered component."""
    dep_manager = _DependenciesManager()
    protocol = ProtocolConfig("a_protocol", "author", "0.1.0")
    skill = SkillConfig("skill", "author", "0.1.0", protocols=[protocol.public_id])
    dep_manager.add_component(protocol)
    dep_manager.add_component(skill)
    dep_manager.remove_component(skill.component_id)


def test_private_keys():
    """Test add/remove private keys."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key("fetchai")

    builder.add_private_key("fetchai", is_connection=True)

    assert builder._connection_private_key_paths
    assert builder._private_key_paths

    builder.remove_private_key("fetchai")
    builder.remove_private_key("fetchai", is_connection=True)

    assert not builder._connection_private_key_paths
    assert not builder._private_key_paths


def test_can_remove_not_exists_component():
    """Test fail on remove component not registered."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key("fetchai")
    protocol = ProtocolConfig("a_protocol", "author", "0.1.0")
    with pytest.raises(ValueError):
        builder._check_can_remove(protocol.component_id)


def test_remove_protocol():
    """Test add/remove protocol."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key("fetchai")
    a_protocol = Protocol(
        ProtocolConfig("a_protocol", "author", "0.1.0"), DefaultMessage
    )
    num_deps = len(builder._package_dependency_manager.all_dependencies)
    builder.add_component_instance(a_protocol)
    assert len(builder._package_dependency_manager.all_dependencies) == num_deps + 1
    builder.remove_protocol(a_protocol.public_id)
    assert len(builder._package_dependency_manager.all_dependencies) == num_deps


def test_remove_connection():
    """Test add/remove connection."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key("fetchai")

    num_deps = len(builder._package_dependency_manager.all_dependencies)
    conn = _make_dummy_connection()
    builder.add_component_instance(conn)
    assert len(builder._package_dependency_manager.all_dependencies) == num_deps + 1
    builder.remove_connection(conn.public_id)
    assert len(builder._package_dependency_manager.all_dependencies) == num_deps


def test_remove_skill():
    """Test add/remove skill."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key("fetchai")

    skill = Skill.from_dir(dummy_skill_path, Mock())
    num_deps = len(builder._package_dependency_manager.all_dependencies)
    builder.add_component_instance(skill)
    assert len(builder._package_dependency_manager.all_dependencies) == num_deps + 1
    builder.remove_skill(skill.public_id)
    assert len(builder._package_dependency_manager.all_dependencies) == num_deps


def test_remove_contract():
    """Test add/remove contract."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key("fetchai")

    contract = Contract.from_dir(contract_path)
    num_deps = len(builder._package_dependency_manager.all_dependencies)
    builder.add_component_instance(contract)
    assert len(builder._package_dependency_manager.all_dependencies) == num_deps + 1
    builder.remove_contract(contract.public_id)
    assert len(builder._package_dependency_manager.all_dependencies) == num_deps


def test_process_connection_ids_not_specified():
    """Test process connection fails on no connection specified."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key("fetchai")

    with pytest.raises(
        ValueError, match=r"Connection ids .* not declared in the configuration file."
    ):
        builder._process_connection_ids(
            [ConnectionConfig("conn", "author", "0.1.0").public_id]
        )


def test_process_connection_ids_bad_default_connection():
    """Test fail on incorrect default connections."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key("fetchai")
    connection = _make_dummy_connection()
    builder.add_component_instance(connection)
    with pytest.raises(
        ValueError,
        match=r"Default connection not a dependency. Please add it and retry.",
    ):
        builder.set_default_connection(
            ConnectionConfig("conn", "author", "0.1.0").public_id
        )
        builder._process_connection_ids([connection.public_id])


def test_component_add_bad_dep():
    """Test component load failed cause dependency."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key("fetchai")
    connection = _make_dummy_connection()
    connection.configuration._pypi_dependencies = {"something": {"version": "==0.1.0"}}
    builder.add_component_instance(connection)

    a_protocol = Protocol(
        ProtocolConfig("a_protocol", "author", "0.1.0"), DefaultMessage
    )
    a_protocol.configuration._pypi_dependencies = {"something": {"version": "==0.2.0"}}
    with pytest.raises(
        AEAException, match=r"Conflict on package something: specifier set .*"
    ):
        builder.add_component_instance(a_protocol)


def test_find_component_failed():
    """Test fail on compomnent not found."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key("fetchai")
    a_protocol = Protocol(
        ProtocolConfig("a_protocol", "author", "0.1.0"), DefaultMessage
    )
    with pytest.raises(ValueError, match=r"Package .* not found"):
        builder._find_component_directory_from_component_id(
            Path("/some_dir"), a_protocol.component_id
        )


def test_set_from_config():
    """Test set configuration from config loaded."""
    builder = AEABuilder()
    agent_configuration = Mock()
    agent_configuration.default_connection = "test/test:0.1.0"
    agent_configuration.decision_maker_handler = {
        "dotted_path": "aea.decision_maker.default:DecisionMakerHandler",
        "file_path": ROOT_DIR + "/aea/decision_maker/default.py",
    }
    agent_configuration.skill_exception_policy = ExceptionPolicyEnum.just_log
    agent_configuration._default_connection = None
    agent_configuration.connection_private_key_paths_dict = {"fetchai": None}
    agent_configuration.ledger_apis_dict = {"fetchai": None}
    agent_configuration.private_key_paths_dict = {"fetchai": None}
    agent_configuration.protocols = (
        agent_configuration.connections
    ) = agent_configuration.contracts = agent_configuration.skills = []

    builder.set_from_configuration(agent_configuration, aea_project_path="/anydir")
    assert builder._decision_maker_handler_class is not None


def test_load_abstract_component():
    """Test abstract component loading."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key("fetchai")

    skill = Skill.from_dir(dummy_skill_path, Mock())
    skill.configuration.is_abstract = True
    builder.add_component_instance(skill)
    builder._load_and_add_components(
        ComponentType.SKILL, Resources(), "aea_1", agent_context=Mock()
    )


def test_find_import_order():
    """Test find import order works on cycle dependency."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key("fetchai")

    _old_load = ComponentConfiguration.load

    def _new_load(*args, **kwargs):
        skill_config = _old_load(*args, **kwargs)
        skill_config.skills = [Mock()]
        return skill_config

    with patch.object(ComponentConfiguration, "load", _new_load):
        with pytest.raises(
            AEAException, match=r"Cannot load skills, there is a cyclic dependency."
        ):
            builder._find_import_order(
                [
                    ComponentId(
                        ComponentType.SKILL, PublicId("dummy_author", "dummy", "0.1.0")
                    ),
                ],
                Path(os.path.join(CUR_PATH, "data", "dummy_aea")),
                True,
            )
