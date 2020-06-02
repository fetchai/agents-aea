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

""" This module contains tests for aea/aea_builder.py """
import os
import re
from pathlib import Path
from typing import Collection

import pytest

from aea.aea_builder import AEABuilder
from aea.configurations.base import ComponentType
from aea.components.base import Component
from aea.crypto.fetchai import FetchAICrypto
from aea.exceptions import AEAException

from .conftest import CUR_PATH, ROOT_DIR, skip_test_windows


FETCHAI = FetchAICrypto.identifier


@skip_test_windows
def test_default_timeout_for_agent():
    """
    Tests agents loop sleep timeout
    set by AEABuilder.DEFAULT_AGENT_LOOP_TIMEOUT
    """
    agent_name = "MyAgent"
    private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
    builder = AEABuilder()
    builder.set_name(agent_name)
    builder.add_private_key(FETCHAI, private_key_path)

    aea = builder.build()
    assert aea._timeout == builder.DEFAULT_AGENT_LOOP_TIMEOUT

    builder = AEABuilder()
    builder.set_name(agent_name)
    builder.add_private_key(FETCHAI, private_key_path)
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
        "Component 'fetchai/fipa:0.2.0' of type 'protocol' already added."
    )
    with pytest.raises(AEAException, match=expected_message):
        builder.add_component(ComponentType.PROTOCOL, fipa_package_path)


def test_when_package_has_missing_dependency():
    """
    Test the case when the builder tries to load the packages,
    but fails because of a missing dependency.
    """
    builder = AEABuilder()
    expected_message = re.escape(
        "Package 'fetchai/oef:0.3.0' of type 'connection' cannot be added. "
        "Missing dependencies: ['(protocol, fetchai/fipa:0.2.0)', '(protocol, fetchai/oef_search:0.1.0)']"
    )
    with pytest.raises(AEAException, match=expected_message):
        # connection "fetchai/oef:0.1.0" requires
        # "fetchai/oef_search:0.1.0" and "fetchai/fipa:0.2.0" protocols.
        builder.add_component(
            ComponentType.CONNECTION,
            Path(ROOT_DIR) / "packages" / "fetchai" / "connections" / "oef",
        )


class TestReentrancy:
    """
    Test the reentrancy of the AEABuilder class, when the components
    are loaded from directories.

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
        dummy_skill_path = os.path.join(CUR_PATH, "data", "dummy_skill")
        protocol_path = os.path.join(
            ROOT_DIR, "packages", "fetchai", "protocols", "oef_search"
        )
        contract_path = os.path.join(
            ROOT_DIR, "packages", "fetchai", "contracts", "erc1155"
        )
        connection_path = os.path.join(
            ROOT_DIR, "packages", "fetchai", "connections", "soef"
        )

        builder = AEABuilder()
        builder.set_name("aea1")
        builder.add_private_key("fetchai")
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
        It only makes sense if they have the same number of elements and
        the same component ids.
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
