# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

from aea_ledger_cosmos import CosmosCrypto
from aea_ledger_ethereum import EthereumCrypto
from click import ClickException
from packaging.specifiers import SpecifierSet

import aea
from aea.configurations.base import PackageVersion
from aea.configurations.constants import DEFAULT_LEDGER

from tests.conftest import AUTHOR
from tests.test_cli.constants import DEFAULT_TESTING_VERSION


def raise_click_exception(*args, **kwargs):
    """Raise ClickException."""
    raise ClickException("Message")


class AgentConfigMock:
    """A class to mock Agent config."""

    def __init__(self, *args, **kwargs):
        """Init the AgentConfigMock object."""
        self.aea_version_specifiers: SpecifierSet = kwargs.get(
            "aea_version_specifier", SpecifierSet(f"=={aea.__version__}")
        )
        self.connections: List[str] = kwargs.get("connections", [])
        self.contracts: List[str] = kwargs.get("contracts", [])
        self.description: str = kwargs.get("description", "")
        self.version: str = kwargs.get("version", "")
        self.protocols: List[str] = kwargs.get("protocols", [])
        self.skills: List[str] = kwargs.get("skills", [])
        self.agent_name: str = kwargs.get("agent_name", "agent_name")
        self.author: str = AUTHOR
        private_key_paths = kwargs.get("private_key_paths", [])
        self.private_key_paths = Mock()
        self.private_key_paths.read_all = Mock(return_value=private_key_paths)
        self.private_key_paths.read = Mock(
            return_value=private_key_paths[0][1] if private_key_paths else None
        )
        connection_private_key_paths = kwargs.get("connection_private_key_paths", [])
        self.connection_private_key_paths = Mock()
        self.connection_private_key_paths.read_all = Mock(
            return_value=connection_private_key_paths
        )
        self.get = lambda x, default=None: getattr(self, x, default)
        self.component_configurations = {}
        self.package_dependencies = set()
        self.config: dict = {}
        self.default_ledger = DEFAULT_LEDGER

    name = "name"


class FaultyAgentConfigMock:
    """A Class to mock Agent config with missing attributes."""

    def __init__(self, *args, **kwargs):
        """Init faulty agent config."""


class ContextMock:
    """A class to mock Context."""

    cwd = "cwd"

    def __init__(self, *args, **kwargs):
        """Init the ContextMock object."""
        self.invoke = Mock()
        self.agent_config = AgentConfigMock(*args, **kwargs)
        self.config: dict = {}
        self.connection_loader = ConfigLoaderMock()
        self.agent_loader = ConfigLoaderMock()
        self.clean_paths: List = []
        self.obj = self
        self.registry_path = "packages"
        self.cwd = "cwd"

    def set_config(self, key, value):
        """Set config."""
        setattr(self.config, key, value)


class PublicIdMock:
    """A class to mock PublicId."""

    DEFAULT_VERSION = DEFAULT_TESTING_VERSION

    def __init__(self, author=AUTHOR, name="name", version=DEFAULT_TESTING_VERSION):
        """Init the Public ID mock object."""
        self.name = name
        self.author = author
        self.version = version

    @classmethod
    def from_str(cls, public_id):
        """Create object from str public_id without validation."""
        author, name, version = public_id.replace(":", "/").split("/")
        return cls(author, name, version)

    @property
    def package_version(self) -> PackageVersion:
        """Get package version."""
        return PackageVersion(self.version)

    def without_hash(
        self,
    ) -> "PublicIdMock":
        """Returns the mock object."""
        return self


class AEAConfMock:
    """A class to mock AgentConfig."""

    def __init__(self, *args, **kwargs):
        """Init the AEAConf mock object."""
        self.author = AUTHOR
        self.version = DEFAULT_TESTING_VERSION
        self.ledger_apis = Mock()
        ledger_apis = (
            (CosmosCrypto.identifier, "value"),
            (EthereumCrypto.identifier, "value"),
        )
        self.ledger_apis.read_all = Mock(return_value=ledger_apis)
        ledger_api_config = {"host": "host", "port": "port", "address": "address"}
        self.ledger_apis.read = Mock(return_value=ledger_api_config)


class ConfigLoaderMock:
    """A class to mock ConfigLoader."""

    def __init__(self, *args, **kwargs):
        """Init the ConfigLoader mock object."""
        self.required_fields = kwargs.get("required_fields", [])

    def load(self, *args, **kwargs):
        """Mock the load method."""
        return AEAConfMock()

    def dump(self, *args, **kwargs):
        """Mock the dump method."""
        pass


class StopTest(Exception):
    """An exception to stop test."""

    pass


def raise_stoptest(*args, **kwargs):
    """Raise StopTest exception."""
    raise StopTest()
