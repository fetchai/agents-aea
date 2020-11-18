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

"""This test module contains the tests configuration utils."""
from unittest.mock import MagicMock

from aea.configurations.base import (
    AgentConfig,
    ComponentId,
    ComponentType,
    ConnectionConfig,
    PublicId,
    SkillConfig,
)
from aea.configurations.utils import (
    get_latest_component_id_from_prefix,
    replace_component_ids,
)


def test_get_latest_component_id_from_prefix():
    """Test the utility to get the latest concrete version id."""
    agent_config = MagicMock()
    expected_component_id = ComponentId(
        ComponentType.PROTOCOL, PublicId("author", "name", "0.1.0")
    )
    agent_config.package_dependencies = {expected_component_id}

    result = get_latest_component_id_from_prefix(
        agent_config, expected_component_id.component_prefix
    )
    assert result == expected_component_id


def test_get_latest_component_id_from_prefix_negative():
    """Test the utility to get the latest concrete version id, negative case."""
    agent_config = MagicMock()
    agent_config.package_dependencies = {}

    result = get_latest_component_id_from_prefix(
        agent_config, (ComponentType.PROTOCOL, "author", "name")
    )
    assert result is None


class BaseTestReplaceComponentIds:
    """Base test class for 'replace_component_ids' utility function."""

    old_protocol_id = PublicId("author", "old_protocol", "0.1.0")
    old_contract_id = PublicId("author", "old_contract", "0.1.0")
    old_connection_id = PublicId("author", "old_connection", "0.1.0")
    old_skill_id = PublicId("author", "old_skill", "0.1.0")

    new_protocol_id = PublicId("author", "new_protocol", "0.1.0")
    new_contract_id = PublicId("author", "new_contract", "0.1.0")
    new_connection_id = PublicId("author", "new_connection", "0.1.0")
    new_skill_id = PublicId("author", "new_skill", "0.1.0")

    new_public_ids = {
        new_protocol_id,
        new_contract_id,
        new_connection_id,
        new_skill_id,
    }

    replacements = {
        ComponentType.PROTOCOL: {old_protocol_id: new_protocol_id},
        ComponentType.CONTRACT: {old_contract_id: new_contract_id},
        ComponentType.CONNECTION: {old_connection_id: new_connection_id},
        ComponentType.SKILL: {old_skill_id: new_skill_id},
    }


class TestReplaceComponentIdsInAgentConfig(BaseTestReplaceComponentIds):
    """Test replace component ids in agent configuration."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.expected_custom_component_configuration = dict(foo="bar")

        cls.agent_config = AgentConfig(
            agent_name="agent_name",
            author="author",
            version="0.1.0",
            default_routing={str(cls.old_protocol_id): str(cls.old_connection_id)},
            default_connection=str(cls.old_connection_id),
        )

        cls.agent_config.protocols = {cls.old_protocol_id}
        cls.agent_config.contracts = {cls.old_contract_id}
        cls.agent_config.connections = {cls.old_connection_id}
        cls.agent_config.skills = {cls.old_skill_id}
        cls.agent_config.component_configurations[
            ComponentId(ComponentType.PROTOCOL, cls.old_protocol_id)
        ] = cls.expected_custom_component_configuration
        cls.agent_config.component_configurations[
            ComponentId(ComponentType.CONTRACT, cls.old_contract_id)
        ] = cls.expected_custom_component_configuration
        cls.agent_config.component_configurations[
            ComponentId(ComponentType.CONNECTION, cls.old_connection_id)
        ] = cls.expected_custom_component_configuration
        cls.agent_config.component_configurations[
            ComponentId(ComponentType.SKILL, cls.old_skill_id)
        ] = cls.expected_custom_component_configuration

        replace_component_ids(cls.agent_config, cls.replacements)

    def test_protocols_updated(self):
        """Test set of protocol ids updated."""
        assert self.agent_config.protocols == {self.new_protocol_id}

    def test_contracts_updated(self):
        """Test set of contract ids updated."""
        assert self.agent_config.contracts == {self.new_contract_id}

    def test_connections_updated(self):
        """Test set of connection ids updated."""
        assert self.agent_config.connections == {self.new_connection_id}

    def test_skills_updated(self):
        """Test set of skill ids updated."""
        assert self.agent_config.skills == {self.new_skill_id}

    def test_default_connection_updated(self):
        """Test default connection updated."""
        assert self.agent_config.default_connection == self.new_connection_id

    def test_default_routing_updated(self):
        """Test default routing updated."""
        assert self.agent_config.default_routing == {
            self.new_protocol_id: self.new_connection_id
        }

    def test_custom_configuration_updated(self):
        """Test default routing updated."""
        component_protocol_id = ComponentId(
            ComponentType.PROTOCOL, self.new_protocol_id
        )
        component_contract_id = ComponentId(
            ComponentType.CONTRACT, self.new_contract_id
        )
        component_connection_id = ComponentId(
            ComponentType.CONNECTION, self.new_connection_id
        )
        component_skill_id = ComponentId(ComponentType.SKILL, self.new_skill_id)

        assert (
            self.agent_config.component_configurations[component_protocol_id]
            == self.expected_custom_component_configuration
        )
        assert (
            self.agent_config.component_configurations[component_contract_id]
            == self.expected_custom_component_configuration
        )
        assert (
            self.agent_config.component_configurations[component_connection_id]
            == self.expected_custom_component_configuration
        )
        assert (
            self.agent_config.component_configurations[component_skill_id]
            == self.expected_custom_component_configuration
        )


class TestReplaceComponentIdsInConnectionConfig(BaseTestReplaceComponentIds):
    """Test replace component ids utility with connection configuration."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.connection_config = ConnectionConfig(
            name="connection_name",
            author="author",
            version="0.1.0",
            connections={cls.old_connection_id},
            protocols={cls.old_protocol_id},
            restricted_to_protocols={cls.old_protocol_id},
            excluded_protocols={cls.old_protocol_id},
        )
        replace_component_ids(cls.connection_config, cls.replacements)

    def test_protocols_updated(self):
        """Test set of protocol ids updated."""
        assert self.connection_config.protocols == {self.new_protocol_id}

    def test_connections_updated(self):
        """Test set of connection ids updated."""
        assert self.connection_config.connections == {self.new_connection_id}

    def test_restricted_to_protocols_updated(self):
        """Test restricted to protocols updated."""
        assert self.connection_config.restricted_to_protocols == {self.new_protocol_id}

    def test_excluded_protocols_updated(self):
        """Test excluded protocols updated."""
        assert self.connection_config.excluded_protocols == {self.new_protocol_id}


class TestReplaceComponentIdsInSkillConfig(BaseTestReplaceComponentIds):
    """Test replace component ids in skill configuration."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.expected_custom_component_configuration = dict(foo="bar")

        cls.skill_config = SkillConfig(
            name="skill_name", author="author", version="0.1.0",
        )

        cls.skill_config.protocols = {cls.old_protocol_id}
        cls.skill_config.contracts = {cls.old_contract_id}
        cls.skill_config.connections = {cls.old_connection_id}
        cls.skill_config.skills = {cls.old_skill_id}

        replace_component_ids(cls.skill_config, cls.replacements)

    def test_protocols_updated(self):
        """Test set of protocol ids updated."""
        assert self.skill_config.protocols == {self.new_protocol_id}

    def test_contracts_updated(self):
        """Test set of contract ids updated."""
        assert self.skill_config.contracts == {self.new_contract_id}

    def test_connections_updated(self):
        """Test set of connection ids updated."""
        assert self.skill_config.connections == {self.new_connection_id}

    def test_skills_updated(self):
        """Test set of skill ids updated."""
        assert self.skill_config.skills == {self.new_skill_id}
