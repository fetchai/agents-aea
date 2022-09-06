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

"""This module contains tests for aea/components/base.py"""
import inspect
import itertools
import os
import re
import sys
from itertools import zip_longest
from pathlib import Path
from textwrap import dedent

import pytest

from aea.aea_builder import AEABuilder
from aea.components.base import Component, load_aea_package
from aea.configurations.base import (
    ConnectionConfig,
    PACKAGE_TYPE_TO_CONFIG_CLASS,
    ProtocolConfig,
)
from aea.configurations.data_types import PackageType, PublicId
from aea.configurations.loader import ConfigLoader
from aea.exceptions import AEAPackageLoadingError
from aea.helpers.base import cd
from aea.helpers.io import open_file
from aea.test_tools.test_cases import AEATestCase

from tests.conftest import (
    CUR_PATH,
    ROOT_DIR,
    connection_config_files,
    contract_config_files,
    protocol_config_files,
    skill_config_files,
)


class TestComponentProperties:
    """Test accessibility of component properties."""

    def setup_class(self):
        """Setup test."""
        self.configuration = ProtocolConfig(
            "name", "author", "0.1.0", protocol_specification_id="some/author:0.1.0"
        )
        self.configuration.build_directory = "test"
        self.component = Component(configuration=self.configuration)
        self.directory = Path()
        self.component._directory = self.directory

    def test_component_type(self):
        """Test component type attribute."""
        assert self.component.component_type == self.configuration.component_type

    def test_is_vendor(self):
        """Test component type attribute."""
        assert self.component.is_vendor is False

    def test_prefix_import_path(self):
        """Test component type attribute."""
        assert self.component.prefix_import_path == "packages.author.protocols.name"

    def test_component_id(self):
        """Test component id."""
        assert self.component.component_id == self.configuration.component_id

    def test_public_id(self):
        """Test public id."""
        assert self.component.public_id == self.configuration.public_id

    def test_directory(self):
        """Test directory."""
        assert self.component.directory == self.directory

    def test_build_directory(self):
        """Test directory."""
        assert self.component.build_directory


def test_directory_setter():
    """Test directory."""
    configuration = ProtocolConfig(
        "author", "name", "0.1.0", protocol_specification_id="some/author:0.1.0"
    )
    component = Component(configuration=configuration)

    with pytest.raises(ValueError):
        component.directory

    new_path = Path("new_path")
    component.directory = new_path
    assert component.directory == new_path


def test_load_aea_package():
    """Test aea package load."""
    config = ConnectionConfig(
        "http_client", "fetchai", "0.5.0", protocols={PublicId("fetchai", "http")}
    )
    config.directory = (
        Path(ROOT_DIR) / "packages" / "fetchai" / "connections" / "http_client"
    )
    load_aea_package(config)


def test_load_aea_package_twice():
    """Test aea package load twice and ensure python objects stay the same."""
    config = ConnectionConfig(
        "http_client", "fetchai", "0.5.0", protocols={PublicId("fetchai", "http")}
    )
    config.directory = (
        Path(ROOT_DIR) / "packages" / "fetchai" / "connections" / "http_client"
    )
    # It doesn't matter if the package is already loaded.
    # We cannot safely remove it as references to other modules
    # would persist and get stale.
    if "packages.fetchai.connections.http_client.connection" not in sys.modules:
        load_aea_package(config)
        assert "packages.fetchai.connections.http_client.connection" not in sys.modules
        from packages.fetchai.connections.http_client.connection import (
            HTTPClientConnection,
        )

        assert "packages.fetchai.connections.http_client.connection" in sys.modules
        BaseHTTPCLientConnection = HTTPClientConnection
    else:
        members = inspect.getmembers(
            sys.modules["packages.fetchai.connections.http_client.connection"],
            inspect.isclass,
        )
        BaseHTTPCLientConnection = [
            pairs[1] for pairs in members if pairs[0] == "HTTPClientConnection"
        ][0]
    # second time
    load_aea_package(config)
    from packages.fetchai.connections.http_client.connection import HTTPClientConnection

    assert BaseHTTPCLientConnection is HTTPClientConnection


class TestLoadingErrorWithUndeclaredDependency(AEATestCase):
    """Test that an error is raised when not declared dependencies are detected in import statements of modules."""

    path_to_aea = Path(CUR_PATH) / "data" / "dummy_aea"

    matching_content = re.escape(
        dedent(
            f"""        aea.exceptions.AEAPackageLoadingError: found the following packages that are imported by some module but not declared as dependencies of package (skill, dummy_author/dummy:0.1.0):

        - connection some_author/some_connection used in:
            - dummy_subpackage{os.path.sep}__init__.py
        - protocol some_author/some_protocol used in:
            - dummy_subpackage{os.path.sep}__init__.py
        """
        )
    )

    def _add_undeclared_dependency_in_dummy_skill_imports(self):
        """
        Set up the dummy skill for the test.

        Add package import statements, in some module of the dummy skill, of packages
        that are not declared as dependencies of the dummy skill.
        """
        cwd = self._get_cwd()
        module_path = Path(cwd, "skills", "dummy", "dummy_subpackage", "__init__.py")
        module_content = module_path.read_text()
        module_content += "\nimport packages.some_author.connections.some_connection"
        module_content += "\nfrom packages.some_author.protocols.some_protocol"
        module_path.write_text(module_content)
        self.run_cli_command("fingerprint", "by-path", "skills/dummy", cwd=cwd)

    def test_run(self):
        """Run the test."""
        self._add_undeclared_dependency_in_dummy_skill_imports()
        with cd(self._get_cwd()):
            builder = AEABuilder.from_aea_project(Path(self._get_cwd()))
            with pytest.raises(AEAPackageLoadingError, match=self.matching_content):
                builder.build()


class TestLoadingErrorWithUnusedDependency(AEATestCase):
    """Test that an error is raised when not used dependencies are detected in import statements of modules."""

    path_to_aea = Path(CUR_PATH) / "data" / "dummy_aea"

    matching_content = re.escape(
        dedent(
            """        aea.exceptions.AEAPackageLoadingError: The following dependencies are not used in any Python module of the package (skill, dummy_author/dummy:0.1.0):
        - connection fetchai/local
        - protocol fetchai/fipa
"""
        )
    )

    def _add_unused_dependency_in_dummy_skill_imports(self):
        """
        Set up the dummy skill for the test.

        Add a dummy dependency that is not used in the skill.
        """
        cwd = self._get_cwd()
        configuration_path = Path(cwd, "skills", "dummy", "skill.yaml")
        configuration_content = configuration_path.read_text()
        configuration_content = configuration_content.replace(
            "protocols:", "protocols:\n- fetchai/fipa:1.0.0"
        )
        configuration_content = configuration_content.replace(
            "connections: []", "connections:\n- fetchai/local:0.20.0"
        )
        configuration_path.write_text(configuration_content)
        self.run_cli_command("fingerprint", "by-path", "skills/dummy", cwd=cwd)

    def test_run(self):
        """Run the test."""
        self._add_unused_dependency_in_dummy_skill_imports()
        with cd(self._get_cwd()):
            builder = AEABuilder.from_aea_project(Path(self._get_cwd()))
            with pytest.raises(AEAPackageLoadingError, match=self.matching_content):
                builder.build()


@pytest.mark.parametrize(
    "component_type,config_file_path",
    itertools.chain.from_iterable(
        [
            zip_longest([], files, fillvalue=component_type)
            for files, component_type in [
                (protocol_config_files, PackageType.PROTOCOL),
                (contract_config_files, PackageType.CONTRACT),
                (connection_config_files, PackageType.CONNECTION),
                (skill_config_files, PackageType.SKILL),
            ]
        ]
    ),
)
def test_load_all_aea_protocol_packages(
    component_type: PackageType, config_file_path: str
) -> None:
    """Load all AEA component packages."""

    to_be_skipped = {os.path.join(CUR_PATH, "data", "gym-connection.yaml")}

    if config_file_path in to_be_skipped:
        pytest.skip(
            f"test not supported for configurations outside package: {config_file_path}"
        )

    configuration_loader = ConfigLoader.from_configuration_type(
        component_type, PACKAGE_TYPE_TO_CONFIG_CLASS
    )
    with open_file(config_file_path) as fp:
        configuration_object = configuration_loader.load(fp)
        directory = Path(config_file_path).parent
        configuration_object.directory = directory
        load_aea_package(configuration_object)
