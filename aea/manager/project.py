# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""This module contains the implementation of AEA agents project configuration."""
import os
from copy import deepcopy
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.cli.fetch import do_fetch
from aea.cli.issue_certificates import issue_certificates_
from aea.cli.utils.context import Context
from aea.configurations.base import AgentConfig, PublicId
from aea.configurations.constants import DEFAULT_REGISTRY_NAME
from aea.configurations.data_types import ComponentId
from aea.configurations.manager import AgentConfigManager
from aea.crypto.helpers import create_private_key, get_wallet_from_agent_config
from aea.exceptions import AEAValidationError, enforce


class _Base:
    """Base class to share some methods."""

    @classmethod
    def _get_agent_config(cls, path: Union[Path, str]) -> AgentConfig:
        """Get agent config instance."""
        agent_config = AEABuilder.try_to_load_agent_configuration_file(path)
        agent_config.check_aea_version()
        return agent_config

    @classmethod
    def _get_builder(
        cls,
        agent_config: AgentConfig,
        aea_project_path: Union[Path, str],
        skip_consistency_check: bool = False,
    ) -> AEABuilder:
        """Get AEABuilder instance."""
        builder = AEABuilder(
            with_default_packages=False, build_dir_root=str(aea_project_path)
        )
        builder.set_from_configuration(
            agent_config, Path(aea_project_path), skip_consistency_check
        )
        return builder

    @property
    def builder(self) -> AEABuilder:
        """Get AEABuilder instance."""
        raise NotImplementedError  # pragma: nocover

    def install_pypi_dependencies(self) -> None:
        """Install python dependencies for the project."""
        self.builder.install_pypi_dependencies()


class Project(_Base):
    """Agent project representation."""

    __slots__ = ("public_id", "path", "agents")

    def __init__(self, public_id: PublicId, path: str) -> None:
        """Init project with public_id and project's path."""
        self.public_id: PublicId = public_id
        self.path: str = path
        self.agents: Set[str] = set()

    def build(self) -> None:
        """Call all build entry points."""
        self.builder.call_all_build_entrypoints()

    @classmethod
    def load(
        cls,
        working_dir: str,
        public_id: PublicId,
        is_local: bool = False,
        is_remote: bool = False,
        is_restore: bool = False,
        cli_verbosity: str = "INFO",
        registry_path: str = DEFAULT_REGISTRY_NAME,
        skip_consistency_check: bool = False,
        skip_aea_validation: bool = False,
    ) -> "Project":
        """
        Load project with given public_id to working_dir.

        If local = False and remote = False, then the packages
        are fetched in mixed mode (i.e. first try from local
        registry, and then from remote registry in case of failure).

        :param working_dir: the working directory
        :param public_id: the public id
        :param is_local: whether to fetch from local
        :param is_remote: whether to fetch from remote
        :param is_restore: whether to restore or not
        :param cli_verbosity: the logging verbosity of the CLI
        :param registry_path: the path to the registry locally
        :param skip_consistency_check: consistency checks flag
        :param skip_aea_validation: aea validation flag
        :return: project
        """
        ctx = Context(
            cwd=working_dir, verbosity=cli_verbosity, registry_path=registry_path
        )
        ctx.set_config("skip_consistency_check", skip_consistency_check)
        ctx.set_config("skip_aea_validation", skip_aea_validation)

        path = os.path.join(working_dir, public_id.author, public_id.name)
        target_dir = os.path.join(public_id.author, public_id.name)

        if not is_restore and not os.path.exists(target_dir):
            do_fetch(ctx, public_id, is_local, is_remote, target_dir=target_dir)
        return cls(public_id, path)

    def remove(self) -> None:
        """Remove project, do cleanup."""
        rmtree(self.path)

    @property
    def agent_config(self) -> AgentConfig:
        """Get the agent configuration."""
        return self._get_agent_config(self.path)

    @property
    def builder(self) -> AEABuilder:
        """Get builder instance."""
        return self._get_builder(self.agent_config, self.path)

    def check(self) -> None:
        """Check we can still construct an AEA from the project with builder.build."""
        _ = self.builder


class AgentAlias(_Base):
    """Agent alias representation."""

    __slots__ = ("project", "agent_name", "_data_dir", "_agent_config")

    def __init__(
        self,
        project: Project,
        agent_name: str,
        data_dir: str,
        password: Optional[str] = None,
    ):
        """Init agent alias with project, config, name, agent, builder."""
        self.project = project
        self.agent_name = agent_name
        self._data_dir = data_dir
        if not os.path.exists(self._data_dir):
            os.makedirs(self._data_dir)
        self._agent_config: AgentConfig = self._get_agent_config(project.path)
        self._password = password
        self._ensure_private_keys()

    def set_agent_config_from_data(self, json_data: List[Dict]) -> None:
        """
        Set agent config instance constructed from json data.

        :param json_data: agent config json data
        """
        self._agent_config = AEABuilder.loader.load_agent_config_from_json(json_data)
        self._ensure_private_keys()

    def _ensure_private_keys(self) -> None:
        """Add private keys if not present in the config."""
        builder = self._get_builder(self.agent_config, self.project.path)
        default_ledger = builder.get_default_ledger()
        required_ledgers = builder.get_required_ledgers()
        enforce(
            default_ledger in required_ledgers,
            exception_text=f"Default ledger '{default_ledger}' not in required ledgers: {required_ledgers}",
            exception_class=AEAValidationError,
        )

        available_private_keys = self.agent_config.private_key_paths.keys()
        available_connection_private_keys = (
            self.agent_config.connection_private_key_paths.keys()
        )

        for required_ledger in set(required_ledgers):
            if required_ledger not in available_private_keys:
                self.agent_config.private_key_paths.create(
                    required_ledger, self._create_private_key(required_ledger)
                )
            if required_ledger not in available_connection_private_keys:
                self.agent_config.connection_private_key_paths.create(
                    required_ledger,
                    self._create_private_key(required_ledger, is_connection=True),
                )

    @property
    def builder(self) -> AEABuilder:
        """Get builder instance."""
        builder = self._get_builder(self.agent_config, self.project.path)
        builder.set_name(self.agent_name)
        builder.set_runtime_mode("threaded")
        builder.set_data_dir(self._data_dir)
        return builder

    @property
    def agent_config(self) -> AgentConfig:
        """Get agent config."""
        return self._agent_config

    def _create_private_key(
        self, ledger: str, replace: bool = False, is_connection: bool = False,
    ) -> str:
        """
        Create new key for agent alias in working dir keys dir.

        If file exists, check `replace` option.

        :param ledger: the ledger id
        :param replace: whether or not to replace an existing key
        :param is_connection: whether or not it is a connection key
        :return: file path to private key
        """
        file_name = (
            f"{ledger}_connection_private.key"
            if is_connection
            else f"{ledger}_private.key"
        )
        filepath = os.path.join(self._data_dir, file_name)
        if os.path.exists(filepath) and not replace:
            return filepath
        create_private_key(ledger, filepath, password=self._password)
        return filepath

    def remove_from_project(self) -> None:
        """Remove agent alias from project."""
        self.project.agents.remove(self.agent_name)

    @property
    def dict(self) -> Dict[str, Any]:
        """Convert AgentAlias to dict."""
        return {
            "public_id": str(self.project.public_id),
            "agent_name": self.agent_name,
            "config": self.config_json,
        }

    @property
    def config_json(self) -> List[Dict]:
        """Get agent config json data."""
        json_data = self.agent_config.ordered_json
        result: List[Dict] = [json_data] + json_data.pop("component_configurations", {})
        return result

    def get_aea_instance(self) -> AEA:
        """Build new aea instance."""
        self.issue_certificates()
        aea = self.builder.build(password=self._password)
        # override build dir to project's one
        aea.DEFAULT_BUILD_DIR_NAME = os.path.join(
            self.project.path, aea.DEFAULT_BUILD_DIR_NAME
        )
        return aea

    def issue_certificates(self) -> None:
        """Issue the certificates for this agent."""
        issue_certificates_(
            self.project.path,
            self.agent_config_manager,
            path_prefix=self._data_dir,
            password=self._password,
        )

    def set_overrides(
        self,
        agent_overrides: Optional[Dict] = None,
        component_overrides: Optional[List[Dict]] = None,
    ) -> None:
        """Set override for this agent alias's config."""
        overrides = deepcopy(agent_overrides or {})
        component_configurations: Dict[ComponentId, Dict] = {}

        for component_override in deepcopy(component_overrides or []):
            try:
                component_id = ComponentId.from_json(
                    {"version": "any", **component_override}
                )
                component_override.pop("author")
                component_override.pop("name")
                component_override.pop("type")
                component_override.pop("version")
                component_configurations[component_id] = component_override
            except (ValueError, KeyError) as e:  # pragma: nocover
                raise ValueError(
                    f"Component overrides are incorrect: {e} during process: {component_override}"
                )

        overrides["component_configurations"] = component_configurations
        self.agent_config_manager.update_config(overrides)
        if agent_overrides:
            self._ensure_private_keys()

    @property
    def agent_config_manager(self) -> AgentConfigManager:
        """Get agent configuration manager instance for the config."""
        return AgentConfigManager(self.agent_config, self.project.path)

    def get_overridables(self) -> Tuple[Dict, List[Dict]]:
        """Get all overridables for this agent alias's config."""
        (
            agent_overridables,
            components_overridables,
        ) = self.agent_config_manager.get_overridables()
        components_configurations = []
        for component_id, obj in components_overridables.items():
            if not obj:  # pragma: nocover
                continue
            obj.update(component_id.json)
            components_configurations.append(obj)

        return agent_overridables, components_configurations

    def get_addresses(self) -> Dict[str, str]:
        """
        Get addresses from private keys.

        :return: dict with crypto id str as key and address str as value
        """
        wallet = get_wallet_from_agent_config(
            self.agent_config, password=self._password
        )
        return wallet.addresses

    def get_connections_addresses(self) -> Dict[str, str]:
        """
        Get connections addresses from connections private keys.

        :return: dict with crypto id str as key and address str as value
        """
        wallet = get_wallet_from_agent_config(
            self.agent_config, password=self._password
        )
        return wallet.connection_cryptos.addresses
