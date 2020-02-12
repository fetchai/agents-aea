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
"""Tools used for CLI registry testing."""

from typing import List
from unittest.mock import Mock

from click import ClickException

from tests.test_cli.constants import DEFAULT_TESTING_VERSION


def raise_click_exception(*args):
    """Raise ClickException."""
    raise ClickException("Message")


class AgentConfigMock:
    """An object to mock Agent config."""

    def __init__(self, *args, **kwargs):
        """Init the AgentConfigMock object."""
        self.connections: List[str] = kwargs.get("connections", [])
        self.protocols: List[str] = kwargs.get("protocols", [])
        self.skills: List[str] = kwargs.get("skills", [])

    registry_path = "registry"
    name = "name"
    author = "author"


class ContextMock:
    """An object to mock Context."""

    cwd = "cwd"

    def __init__(self, *args, **kwargs):
        """Init the ContextMock object."""
        self.invoke = Mock()
        self.agent_config = AgentConfigMock(*args, **kwargs)


class PublicIdMock:
    """An object to mock PublicId."""

    DEFAULT_VERSION = DEFAULT_TESTING_VERSION

    def __init__(self, author="author", name="name", version=DEFAULT_TESTING_VERSION):
        """Init the Public ID mock object."""
        self.name = name
        self.author = author
        self.version = version

    @classmethod
    def from_str(cls, public_id):
        """Create object from str public_id without validation."""
        author, name, version = public_id.replace(":", "/").split("/")
        return cls(author, name, version)
