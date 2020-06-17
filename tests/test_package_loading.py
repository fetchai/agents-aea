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

"""This module contains tests for AEA package loading."""
import os
import sys
from unittest.mock import Mock

from aea.skills.base import Skill

from .conftest import CUR_PATH


def test_loading():
    """Test that we correctly load AEA package modules."""
    agent_context_mock = Mock()
    skill_directory = os.path.join(CUR_PATH, "data", "dummy_skill")

    prefixes = [
        "packages",
        "packages.dummy_author",
        "packages.dummy_author.skills",
        "packages.dummy_author.skills.dummy",
        "packages.dummy_author.skills.dummy.dummy_subpackage",
    ]
    Skill.from_dir(skill_directory, agent_context_mock)
    assert all(
        prefix in sys.modules for prefix in prefixes
    ), "Not all the subpackages are importable."

    # try to import a function from a skill submodule.
    from packages.dummy_author.skills.dummy.dummy_subpackage.foo import bar  # type: ignore

    assert bar() == 42
