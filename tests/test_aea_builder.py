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

import pytest

from aea.aea_builder import AEABuilder
from aea.configurations.base import (
    ComponentType,
    SkillConfig,
    DEFAULT_SKILL_CONFIG_FILE,
)
from aea.crypto.fetchai import FetchAICrypto
from aea.exceptions import AEAException
from aea.skills.base import SkillContext, Skill
from .common.utils import make_handler_cls_from_funcion, make_behaviour_cls_from_funcion

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


def test_reentrancy_with_components_loaded_from_directories():
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

    Instances of components  of aea1 are not shared with the aea2's ones.
    """
    dummy_skill_path = os.path.join(CUR_PATH, "data", "dummy_skill")

    builder = AEABuilder()
    builder.set_name("aea1")
    builder.add_private_key("fetchai")
    builder.add_skill(dummy_skill_path)

    aea1 = builder.build()

    builder.set_name("aea2")
    aea2 = builder.build()

    aea1_skills = aea1.resources.get_all_skills()
    aea2_skills = aea2.resources.get_all_skills()

    assert aea1_skills != aea2_skills

    aea1_skills_configs = [s.configuration for s in aea1_skills]
    aea2_skills_configs = [s.configuration for s in aea2_skills]
    assert aea1_skills_configs != aea2_skills_configs
