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
import logging
import logging.config
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import click
import jsonschema
import yaml

from aea.cli.utils.constants import (
    ALLOWED_PATH_ROOTS,
    AUTHOR_KEY,
    CLI_CONFIG_PATH,
    RESOURCE_TYPE_TO_CONFIG_FILE,
)
from aea.cli.utils.context import Context
from aea.cli.utils.exceptions import AEAConfigException
from aea.cli.utils.generic import load_yaml
from aea.configurations.base import (
    ComponentId,
    ComponentType,
    PackageConfiguration,
    PackageType,
    PublicId,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.constants import AGENT, AGENTS, DEFAULT_AEA_CONFIG_FILE, VENDOR
from aea.configurations.loader import ConfigLoader, ConfigLoaders
from aea.exceptions import AEAEnforceError, AEAException, enforce


def try_to_load_agent_config(
    ctx: Context, is_exit_on_except: bool = True, agent_src_path: str = None
) -> None:
    """
    Load agent config to a click context object.

    :param ctx: click command context object.
    :param is_exit_on_except: bool option to exit on exception (default = True).
    :param agent_src_path: path to an agent dir if needed to load a custom config.

    :return None
    """
    if agent_src_path is None:
        agent_src_path = ctx.cwd

    try:
        path = Path(os.path.join(agent_src_path, DEFAULT_AEA_CONFIG_FILE))
        with path.open(mode="r", encoding="utf-8") as fp:
            ctx.agent_config = ctx.agent_loader.load(fp)
            ctx.agent_config.directory = Path(agent_src_path)
            logging.config.dictConfig(ctx.agent_config.logging_config)
    except FileNotFoundError:
        if is_exit_on_except:
            raise click.ClickException(
                "Agent configuration file '{}' not found in the current directory.".format(
                    DEFAULT_AEA_CONFIG_FILE
                )
            )
    except jsonschema.exceptions.ValidationError:
        if is_exit_on_except:
            raise click.ClickException(
                "Agent configuration file '{}' is invalid. Please check the documentation.".format(
                    DEFAULT_AEA_CONFIG_FILE
                )
            )
    except AEAEnforceError as e:
        raise click.ClickException(str(e))  # pragma: nocover


def _init_cli_config() -> None:
    """
    Create cli config folder and file.

    :return: None
    """
    conf_dir = os.path.dirname(CLI_CONFIG_PATH)
    if not os.path.exists(conf_dir):
        os.makedirs(conf_dir)
    with open(CLI_CONFIG_PATH, "w+") as f:
        yaml.dump({}, f, default_flow_style=False)


def update_cli_config(dict_conf: Dict) -> None:
    """
    Update CLI config and write to yaml file.

    :param dict_conf: dict config to write.

    :return: None
    """
    config = get_or_create_cli_config()
    config.update(dict_conf)
    with open(CLI_CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_or_create_cli_config() -> Dict:
    """
    Read or create CLI config from yaml file.

    :return: dict CLI config.
    """
    try:
        return load_yaml(CLI_CONFIG_PATH)
    except FileNotFoundError:
        _init_cli_config()
    return load_yaml(CLI_CONFIG_PATH)


def set_cli_author(click_context) -> None:
    """
    Set CLI author in the CLI Context.

    The key of the new field is 'cli_author'.

    :param click_context: the Click context
    :return: None.
    """
    config = get_or_create_cli_config()
    cli_author = config.get(AUTHOR_KEY, None)
    if cli_author is None:
        raise click.ClickException(
            "The AEA configurations are not initialized. Use `aea init` before continuing."
        )
    click_context.obj.set_config("cli_author", cli_author)


def load_item_config(item_type: str, package_path: Path) -> PackageConfiguration:
    """
    Load item configuration.

    :param item_type: type of item.
    :param package_path: path to package from which config should be loaded.

    :return: configuration object.
    """
    configuration_file_name = _get_default_configuration_file_name_from_type(item_type)
    configuration_path = package_path / configuration_file_name
    configuration_loader = ConfigLoader.from_configuration_type(PackageType(item_type))
    with configuration_path.open() as file_input:
        item_config = configuration_loader.load(file_input)
    return item_config


def dump_item_config(
    package_configuration: PackageConfiguration, package_path: Path
) -> None:
    """
    Dump item configuration.

    :param package_configuration: the package configuration.
    :param package_path: path to package from which config should be dumped.

    :return: None
    """
    configuration_file_name = _get_default_configuration_file_name_from_type(
        package_configuration.package_type
    )
    configuration_path = package_path / configuration_file_name
    configuration_loader = ConfigLoader.from_configuration_type(
        package_configuration.package_type
    )
    with configuration_path.open("w") as file_output:
        configuration_loader.dump(package_configuration, file_output)  # type: ignore


def handle_dotted_path(
    value: str, author: str
) -> Tuple[List[str], Path, ConfigLoader, Optional[ComponentId]]:
    """Separate the path between path to resource and json path to attribute.

    Allowed values:
        'agent.an_attribute_name'
        'protocols.my_protocol.an_attribute_name'
        'connections.my_connection.an_attribute_name'
        'contracts.my_contract.an_attribute_name'
        'skills.my_skill.an_attribute_name'
        'vendor.author.[protocols|contracts|connections|skills].package_name.attribute_name

    We also return the component id to retrieve the configuration of a specific
    component. Notice that at this point we don't know the version,
    so we put 'latest' as version, but later we will ignore it because
    we will filter with only the component prefix (i.e. the triple type, author and name).

    :param value: dotted path.
    :param author: the author string.

    :return: Tuple[list of settings dict keys, filepath, config loader, component id].
    """
    parts = value.split(".")

    root = parts[0]
    if root not in ALLOWED_PATH_ROOTS:
        raise AEAException(
            "The root of the dotted path must be one of: {}".format(ALLOWED_PATH_ROOTS)
        )

    if (
        len(parts) < 2
        or parts[0] == AGENT
        and len(parts) < 2
        or parts[0] == VENDOR
        and len(parts) < 5
        or parts[0] != AGENT
        and len(parts) < 3
    ):
        raise AEAException(
            "The path is too short. Please specify a path up to an attribute name."
        )

    # if the root is 'agent', stop.
    if root == AGENT:
        resource_type_plural = AGENTS
        path_to_resource_configuration = Path(DEFAULT_AEA_CONFIG_FILE)
        json_path = parts[1:]
        component_id = None
    elif root == VENDOR:
        # parse json path
        resource_author = parts[1]
        resource_type_plural = parts[2]
        resource_name = parts[3]

        # extract component id
        resource_type_singular = resource_type_plural[:-1]
        try:
            component_type = ComponentType(resource_type_singular)
        except ValueError as e:
            raise AEAException(
                f"'{resource_type_plural}' is not a valid component type. Please use one of {ComponentType.plurals()}."
            ) from e
        component_id = ComponentId(
            component_type, PublicId(resource_author, resource_name)
        )

        # find path to the resource directory
        path_to_resource_directory = (
            Path(".") / VENDOR / resource_author / resource_type_plural / resource_name
        )
        path_to_resource_configuration = (
            path_to_resource_directory
            / RESOURCE_TYPE_TO_CONFIG_FILE[resource_type_plural]
        )
        json_path = parts[4:]
        if not path_to_resource_directory.exists():
            raise AEAException(  # pragma: nocover
                "Resource vendor/{}/{}/{} does not exist.".format(
                    resource_author, resource_type_plural, resource_name
                )
            )
    else:
        # navigate the resources of the agent to reach the target configuration file.
        resource_type_plural = root
        resource_name = parts[1]

        # extract component id
        resource_type_singular = resource_type_plural[:-1]
        component_type = ComponentType(resource_type_singular)
        resource_author = author
        component_id = ComponentId(
            component_type, PublicId(resource_author, resource_name)
        )

        # find path to the resource directory
        path_to_resource_directory = Path(".") / resource_type_plural / resource_name
        path_to_resource_configuration = (
            path_to_resource_directory
            / RESOURCE_TYPE_TO_CONFIG_FILE[resource_type_plural]
        )
        json_path = parts[2:]
        if not path_to_resource_directory.exists():
            raise AEAException(
                "Resource {}/{} does not exist.".format(
                    resource_type_plural, resource_name
                )
            )

    config_loader = ConfigLoader.from_configuration_type(resource_type_plural[:-1])
    return json_path, path_to_resource_configuration, config_loader, component_id


def update_item_config(item_type: str, package_path: Path, **kwargs) -> None:
    """
    Update item config and item config file.

    :param item_type: type of item.
    :param package_path: path to a package folder.
    :param kwargs: pairs of config key-value to update.

    :return: None
    """
    item_config = load_item_config(item_type, package_path)
    for key, value in kwargs.items():
        setattr(item_config, key, value)

    config_filepath = os.path.join(
        package_path, item_config.default_configuration_filename
    )
    loader = ConfigLoaders.from_package_type(item_type)
    with open(config_filepath, "w") as f:
        loader.dump(item_config, f)


def validate_item_config(item_type: str, package_path: Path) -> None:
    """
    Validate item configuration.

    :param item_type: type of item.
    :param package_path: path to a package folder.

    :return: None
    :raises AEAConfigException: if something is wrong with item configuration.
    """
    item_config = load_item_config(item_type, package_path)
    loader = ConfigLoaders.from_package_type(item_type)
    for field_name in loader.required_fields:
        try:
            getattr(item_config, field_name)
        except AttributeError:
            raise AEAConfigException(
                "Parameter '{}' is missing from {} config.".format(
                    field_name, item_type
                )
            )


def _try_get_configuration_object_from_aea_config(
    ctx: Context, component_id: ComponentId
) -> Optional[Dict]:
    """
    Try to get the configuration object in the AEA config.

    The result is not guaranteed because there might not be any

    :param ctx: the CLI context.
    :param component_id: the component id whose prefix points to the relevant
        custom configuration in the AEA configuration file.
    :return: the configuration object to get/set an attribute.
    """
    if component_id is None:
        # this is the case when the prefix of the json path is 'agent'.
        return None  # pragma: nocover
    type_, author, name = (
        component_id.component_type,
        component_id.author,
        component_id.name,
    )
    component_ids = set(ctx.agent_config.component_configurations.keys())
    true_component_id = _try_get_component_id_from_prefix(
        component_ids, (type_, author, name)
    )
    if true_component_id is not None:
        return ctx.agent_config.component_configurations.get(true_component_id)
    return None


def _try_get_component_id_from_prefix(
    component_ids: Set[ComponentId], component_prefix: Tuple[ComponentType, str, str]
) -> Optional[ComponentId]:
    """
    Find the component id matching a component prefix.

    :param component_ids: the set of component id.
    :param component_prefix: the component prefix.
    :return: the component id that matches the prefix.
    :raises ValueError: if there are more than two components as candidate results.
    """
    type_, author, name = component_prefix
    results = list(
        filter(
            lambda x: x.component_type == type_
            and x.author == author
            and x.name == name,
            component_ids,
        )
    )
    if len(results) == 0:
        return None
    enforce(len(results) == 1, f"Expected only one component, found {len(results)}.")
    return results[0]


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
