# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""A module with config tools of the aea cli."""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Set

import click
import jsonschema
import yaml

from aea.cli.registry.settings import (
    DEFAULT_IPFS_URL,
    REGISTRY_CONFIG_KEY,
    REGISTRY_LOCAL,
    REMOTE_HTTP,
)
from aea.cli.utils.constants import AUTHOR_KEY, CLI_CONFIG_PATH, DEFAULT_CLI_CONFIG
from aea.cli.utils.context import Context
from aea.cli.utils.exceptions import AEAConfigException
from aea.cli.utils.generic import load_yaml
from aea.configurations.base import (
    ComponentType,
    PackageConfiguration,
    PackageType,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.constants import DEFAULT_AEA_CONFIG_FILE
from aea.configurations.loader import ConfigLoader, ConfigLoaders
from aea.configurations.validation import ExtraPropertiesError, _SCHEMAS_DIR
from aea.exceptions import AEAEnforceError, AEAValidationError
from aea.helpers.io import open_file


def try_to_load_agent_config(
    ctx: Context, is_exit_on_except: bool = True, agent_src_path: str = None
) -> None:
    """
    Load agent config to a click context object.

    :param ctx: click command context object.
    :param is_exit_on_except: bool option to exit on exception (default = True).
    :param agent_src_path: path to an agent dir if needed to load a custom config.
    """
    if agent_src_path is None:
        agent_src_path = ctx.cwd

    try:
        path = Path(os.path.join(agent_src_path, DEFAULT_AEA_CONFIG_FILE))
        with open_file(path, mode="r", encoding="utf-8") as fp:
            ctx.agent_config = ctx.agent_loader.load(fp)
            ctx.agent_config.directory = Path(agent_src_path)
    except FileNotFoundError:
        if is_exit_on_except:
            raise click.ClickException(
                "Agent configuration file '{}' not found in the current directory.".format(
                    DEFAULT_AEA_CONFIG_FILE
                )
            )
    except (
        jsonschema.exceptions.ValidationError,
        ExtraPropertiesError,
        AEAValidationError,
    ) as e:
        if is_exit_on_except:
            raise click.ClickException(
                "Agent configuration file '{}' is invalid: `{}`. Please check the documentation.".format(
                    DEFAULT_AEA_CONFIG_FILE, str(e)
                )
            )
    except AEAEnforceError as e:
        raise click.ClickException(str(e))  # pragma: nocover


def validate_cli_config(config: Dict) -> None:
    """Validate CLI config using config schema."""
    with open_file(Path(_SCHEMAS_DIR, "cli_config.json")) as fp:
        schema = json.load(fp)

    validator = jsonschema.Draft4Validator(schema=schema)
    validator.validate(config)


def _init_cli_config() -> None:
    """Create cli config folder and file."""
    conf_dir = os.path.dirname(CLI_CONFIG_PATH)
    if not os.path.exists(conf_dir):
        os.makedirs(conf_dir)
    with open_file(CLI_CONFIG_PATH, "w+") as f:
        yaml.dump(DEFAULT_CLI_CONFIG, f, default_flow_style=False)


def update_cli_config(dict_conf: Dict) -> None:
    """
    Update CLI config and write to yaml file.

    :param dict_conf: dict config to write.
    """
    config = get_or_create_cli_config()
    config.update(dict_conf)

    validate_cli_config(config)

    with open_file(CLI_CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_or_create_cli_config() -> Dict:
    """
    Read or create CLI config from yaml file.

    :return: dict CLI config.
    """
    try:
        config = load_yaml(CLI_CONFIG_PATH)
    except FileNotFoundError:
        _init_cli_config()
        config = load_yaml(CLI_CONFIG_PATH)

    validate_cli_config(config)
    return config


def set_cli_author(click_context: click.Context) -> None:
    """
    Set CLI author in the CLI Context.

    The key of the new field is 'cli_author'.

    :param click_context: the Click context
    """
    config = get_or_create_cli_config()
    cli_author = config.get(AUTHOR_KEY, None)
    if cli_author is None:
        raise click.ClickException(
            "The AEA configurations are not initialized. Use `aea init` before continuing."
        )
    click_context.obj.set_config("cli_author", cli_author)


def get_registry_config() -> Dict:
    """Returns registry config from CLI config."""

    config = get_or_create_cli_config()
    cli_registry_config = config.get(REGISTRY_CONFIG_KEY, None)
    if cli_registry_config is None:
        raise click.ClickException(
            "The AEA configurations are not initialized. Use `aea init` before continuing."
        )
    return cli_registry_config


def get_registry_path_from_cli_config() -> Optional[str]:
    """Get registry path from config."""
    return (
        get_or_create_cli_config()
        .get(REGISTRY_CONFIG_KEY, {})
        .get("settings", {})
        .get(REGISTRY_LOCAL, {})
        .get("default_packages_path")
    )


def get_default_author_from_cli_config() -> Optional[str]:
    """Get registry path from config."""
    config = get_or_create_cli_config()
    return config.get(AUTHOR_KEY, None)


def get_default_remote_registry(default: str = REMOTE_HTTP) -> str:
    """Return remote registry from cli config."""
    return (
        get_or_create_cli_config()
        .get("registry_config", {})
        .get("settings", {})
        .get("remote", {})
        .get("default", default)
    )


def get_ipfs_node_multiaddr(default: str = DEFAULT_IPFS_URL) -> str:
    """Return remote registry from cli config."""
    return (
        get_or_create_cli_config()
        .get("registry_config", {})
        .get("settings", {})
        .get("remote", {})
        .get("ipfs", {})
        .get("ipfs_node", default)
    )


def load_item_config(
    item_type: str, package_path: Path, package_type_config_class: Optional[Dict] = None
) -> PackageConfiguration:
    """
    Load item configuration.

    :param item_type: type of item.
    :param package_path: path to package from which config should be loaded.
    :param package_type_config_class: Package type to config loader mappings.

    :return: configuration object.
    """
    configuration_file_name = _get_default_configuration_file_name_from_type(item_type)
    configuration_path = package_path / configuration_file_name
    configuration_loader = ConfigLoader.from_configuration_type(
        PackageType(item_type), package_type_config_class=package_type_config_class
    )
    with open_file(configuration_path) as file_input:
        item_config = configuration_loader.load(file_input)
    return item_config


def dump_item_config(
    package_configuration: PackageConfiguration,
    package_path: Path,
    package_type_config_class: Optional[Dict] = None,
) -> None:
    """
    Dump item configuration.

    :param package_configuration: the package configuration.
    :param package_path: path to package from which config should be dumped.
    :param package_type_config_class: Package type to config loader mappings.
    """
    configuration_file_name = _get_default_configuration_file_name_from_type(
        package_configuration.package_type
    )
    configuration_path = package_path / configuration_file_name
    configuration_loader = ConfigLoader.from_configuration_type(
        package_configuration.package_type,
        package_type_config_class=package_type_config_class,
    )
    with configuration_path.open("w") as file_output:
        configuration_loader.dump(package_configuration, file_output)  # type: ignore


def update_item_config(
    item_type: str,
    package_path: Path,
    package_type_config_class: Optional[Dict] = None,
    **kwargs: Any
) -> None:
    """
    Update item config and item config file.

    :param item_type: type of item.
    :param package_path: path to a package folder.
    :param package_type_config_class: Package type to config loader mappings.
    :param kwargs: pairs of config key-value to update.
    """
    item_config = load_item_config(item_type, package_path)
    for key, value in kwargs.items():
        setattr(item_config, key, value)

    config_filepath = os.path.join(
        package_path, item_config.default_configuration_filename
    )
    loader = ConfigLoaders.from_package_type(
        item_type, package_type_config_class=package_type_config_class
    )
    with open_file(config_filepath, "w") as f:
        loader.dump(item_config, f)


def validate_item_config(
    item_type: str,
    package_path: Path,
    package_type_config_class: Optional[Dict] = None,
) -> None:
    """
    Validate item configuration.

    :param item_type: type of item.
    :param package_path: path to a package folder.
    :param package_type_config_class: Package type to config loader mappings.

    :raises AEAConfigException: if something is wrong with item configuration.
    """
    item_config = load_item_config(
        item_type, package_path, package_type_config_class=package_type_config_class
    )
    loader = ConfigLoaders.from_package_type(
        item_type, package_type_config_class=package_type_config_class
    )
    for field_name in loader.required_fields:
        try:
            getattr(item_config, field_name)
        except AttributeError:
            raise AEAConfigException(
                "Parameter '{}' is missing from {} config.".format(
                    field_name, item_type
                )
            )


def get_non_vendor_package_path(aea_project_path: Path) -> Set[Path]:
    """
    Get all the paths to non-vendor packages.

    :param aea_project_path: the path to an AEA project.
    :return: the set of paths, one for each non-vendor package configuration file.
    """
    result: Set[Path] = set()
    for item_type_plural in ComponentType.plurals():
        nonvendor_package_dir_of_type = aea_project_path / item_type_plural
        result = result.union(
            {p for p in nonvendor_package_dir_of_type.iterdir() if p.is_dir()}
            if nonvendor_package_dir_of_type.exists()
            else {}
        )
    return result
