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

"""Implementation of the common utils of the aea cli."""

import logging
import logging.config
import os
import re
import shutil
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional, cast

import click

from dotenv import load_dotenv

import jsonschema  # type: ignore
from jsonschema import ValidationError

from aea import AEA_DIR
from aea.cli.loggers import default_logging_config
from aea.configurations.base import (
    AgentConfig,
    ConfigurationType,
    ConnectionConfig,
    ContractConfig,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    Dependencies,
    ProtocolConfig,
    PublicId,
    SkillConfig,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.loader import ConfigLoader
from aea.crypto.fetchai import FETCHAI
from aea.helpers.base import (
    add_agent_component_module_to_sys_modules,
    load_agent_component_package,
)

logger = logging.getLogger("aea")
logger = default_logging_config(logger)

DEFAULT_VERSION = "0.1.0"
DEFAULT_AUTHOR = "author"
DEFAULT_CONNECTION = PublicId.from_str(
    "fetchai/stub:" + DEFAULT_VERSION
)  # type: PublicId
DEFAULT_SKILL = PublicId.from_str("fetchai/error:" + DEFAULT_VERSION)  # type: PublicId
DEFAULT_LEDGER = FETCHAI
DEFAULT_REGISTRY_PATH = str(Path("./", "packages"))
DEFAULT_LICENSE = "Apache-2.0"


from_string_to_type = dict(str=str, int=int, bool=bool, float=float)


class Context(object):
    """A class to keep configuration of the cli tool."""

    agent_config: AgentConfig

    def __init__(self, cwd: str = "."):
        """Init the context."""
        self.config = dict()  # type: Dict
        self.agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
        self.skill_loader = ConfigLoader("skill-config_schema.json", SkillConfig)
        self.connection_loader = ConfigLoader(
            "connection-config_schema.json", ConnectionConfig
        )
        self.contract_loader = ConfigLoader(
            "contract-config_schema.json", ContractConfig
        )
        self.protocol_loader = ConfigLoader(
            "protocol-config_schema.json", ProtocolConfig
        )
        self.cwd = cwd

    def set_config(self, key, value) -> None:
        """
        Set a config.

        :param key: the key for the configuration.
        :param value: the value associated with the key.
        :return: None
        """
        self.config[key] = value
        logger.debug("  config[%s] = %s" % (key, value))

    def _get_item_dependencies(self, item_type, public_id: PublicId) -> Dependencies:
        """Get the dependencies from item type and public id."""
        item_type_plural = item_type + "s"
        default_config_file_name = _get_default_configuration_file_name_from_type(
            item_type
        )
        path = Path(
            "vendor",
            public_id.author,
            item_type_plural,
            public_id.name,
            default_config_file_name,
        )
        if not path.exists():
            path = Path(item_type_plural, public_id.name, default_config_file_name)
        config_loader = ConfigLoader.from_configuration_type(item_type)
        config = config_loader.load(path.open())
        deps = cast(Dependencies, config.dependencies)
        return deps

    def get_dependencies(self) -> Dependencies:
        """Aggregate the dependencies from every component.

        :return a list of dependency version specification. e.g. ["gym >= 1.0.0"]
        """
        dependencies = {}  # type: Dependencies
        for protocol_id in self.agent_config.protocols:
            dependencies.update(self._get_item_dependencies("protocol", protocol_id))

        for connection_id in self.agent_config.connections:
            dependencies.update(
                self._get_item_dependencies("connection", connection_id)
            )

        for skill_id in self.agent_config.skills:
            dependencies.update(self._get_item_dependencies("skill", skill_id))

        for contract_id in self.agent_config.contracts:
            dependencies.update(self._get_item_dependencies("contract", contract_id))

        return dependencies


pass_ctx = click.make_pass_decorator(Context)


def try_to_load_agent_config(ctx: Context, is_exit_on_except: bool = True) -> None:
    """
    Load agent config to a click context object.

    :param ctx: click command context object.
    :param is_exit_on_except: bool option to exit on exception (default = True).

    :return None
    """
    try:
        path = Path(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE))
        with path.open(mode="r", encoding="utf-8") as fp:
            ctx.agent_config = ctx.agent_loader.load(fp)
            logging.config.dictConfig(ctx.agent_config.logging_config)
    except FileNotFoundError:
        if is_exit_on_except:
            logger.error(
                "Agent configuration file '{}' not found in the current directory.".format(
                    DEFAULT_AEA_CONFIG_FILE
                )
            )
            sys.exit(1)
    except jsonschema.exceptions.ValidationError:
        if is_exit_on_except:
            logger.error(
                "Agent configuration file '{}' is invalid. Please check the documentation.".format(
                    DEFAULT_AEA_CONFIG_FILE
                )
            )
            sys.exit(1)


def _try_to_load_protocols(ctx: Context):
    for protocol_public_id in ctx.agent_config.protocols:
        protocol_name = protocol_public_id.name
        protocol_author = protocol_public_id.author
        logger.debug("Processing protocol {}".format(protocol_public_id))
        protocol_dir = Path(
            "vendor", protocol_public_id.author, "protocols", protocol_name
        )
        if not protocol_dir.exists():
            protocol_dir = Path("protocols", protocol_name)

        try:
            ctx.protocol_loader.load(open(protocol_dir / DEFAULT_PROTOCOL_CONFIG_FILE))
        except FileNotFoundError:
            logger.error(
                "Protocol configuration file for protocol {} not found.".format(
                    protocol_name
                )
            )
            sys.exit(1)

        try:
            protocol_package = load_agent_component_package(
                "protocol", protocol_name, protocol_author, protocol_dir
            )
            add_agent_component_module_to_sys_modules(
                "protocol", protocol_name, protocol_author, protocol_package
            )
        except Exception:
            logger.error(
                "A problem occurred while processing protocol {}.".format(
                    protocol_public_id
                )
            )
            sys.exit(1)


def _load_env_file(env_file: str):
    """
    Load the content of the environment file into the process environment.

    :param env_file: path to the env file.
    :return: None.
    """
    load_dotenv(dotenv_path=Path(env_file), override=False)


def format_items(items):
    """Format list of items (protocols/connections) to a string for CLI output."""
    list_str = ""
    for item in items:
        list_str += (
            "{line}\n"
            "Public ID: {public_id}\n"
            "Name: {name}\n"
            "Description: {description}\n"
            "Author: {author}\n"
            "Version: {version}\n"
            "{line}\n".format(
                name=item["name"],
                public_id=item["public_id"],
                description=item["description"],
                author=item["author"],
                version=item["version"],
                line="-" * 30,
            )
        )
    return list_str


def retrieve_details(name: str, loader: ConfigLoader, config_filepath: str) -> Dict:
    """Return description of a protocol, skill, connection."""
    config = loader.load(open(str(config_filepath)))
    item_name = config.agent_name if isinstance(config, AgentConfig) else config.name
    assert item_name == name
    return {
        "public_id": str(config.public_id),
        "name": item_name,
        "author": config.author,
        "description": config.description,
        "version": config.version,
    }


class AEAConfigException(Exception):
    """Exception about AEA configuration."""


class ConnectionsOption(click.Option):
    """Click option for the --connections option in 'aea run'."""

    def type_cast_value(self, ctx, value) -> Optional[List[PublicId]]:
        """
        Parse the list of string passed through command line.

        E.g. from 'stub,local' to ['stub', 'local'].

        :param ctx: the click context
        :param value: the list of connection names, as a string.
        :return:
        """
        if value is None:
            return None
        try:

            def arg_strip(s):
                return s.strip(" '\"")

            input_connection_ids = [
                arg_strip(s) for s in value.split(",") if arg_strip(s) != ""
            ]

            # remove duplicates, while preserving the order
            result = OrderedDict()  # type: OrderedDict[PublicId, None]
            for connection_id_string in input_connection_ids:
                connection_public_id = PublicId.from_str(connection_id_string)
                result[connection_public_id] = None
            return list(result.keys())
        except Exception:  # pragma: no cover
            raise click.BadParameter(value)


class PublicIdParameter(click.ParamType):
    """Define a public id parameter for Click applications."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the Public Id parameter.

        Just forwards arguments to parent constructor.
        """
        super().__init__(*args, **kwargs)

    def get_metavar(self, param):
        """Return the metavar default for this param if it provides one."""
        return "PUBLIC_ID"

    def convert(self, value, param, ctx):
        """Convert the value. This is not invoked for values that are `None` (the missing value)."""
        try:
            return PublicId.from_str(value)
        except ValueError:
            self.fail(value, param, ctx)


class AgentDirectory(click.Path):
    """A click.Path, but with further checks  applications."""

    def __init__(self):
        """Initialize the agent directory parameter."""
        super().__init__(
            exists=True, file_okay=False, dir_okay=True, readable=True, writable=False
        )

    def get_metavar(self, param):
        """Return the metavar default for this param if it provides one."""
        return "AGENT_DIRECTORY"

    def convert(self, value, param, ctx):
        """Convert the value. This is not invoked for values that are `None` (the missing value)."""
        cwd = os.getcwd()
        path = Path(value)
        try:
            # check that the target folder is an AEA project.
            os.chdir(path)
            fp = open(DEFAULT_AEA_CONFIG_FILE, mode="r", encoding="utf-8")
            ctx.obj.agent_config = ctx.obj.agent_loader.load(fp)
            try_to_load_agent_config(ctx.obj)
            # everything ok - return the parameter to the command
            return value
        except Exception:
            logger.error("The name provided is not a path to an AEA project.")
            self.fail(value, param, ctx)
        finally:
            os.chdir(cwd)


def validate_package_name(package_name: str):
    """Check that the package name matches the pattern r"[a-zA-Z_][a-zA-Z0-9_]*".

    >>> validate_package_name("this_is_a_good_package_name")
    >>> validate_package_name("this-is-not")
    Traceback (most recent call last):
    ...
    click.exceptions.BadParameter: this-is-not is not a valid package name.
    """
    if re.fullmatch(PublicId.PACKAGE_NAME_REGEX, package_name) is None:
        raise click.BadParameter("{} is not a valid package name.".format(package_name))


def try_get_item_source_path(
    path: str, author_name: str, item_type_plural: str, item_name: str
) -> str:
    """
    Get the item source path.

    :param path: the source path root
    :param author_name: the name of the author of the item
    :param item_type_plural: the item type (plural)
    :param item_name: the item name

    :return: the item source path
    """
    source_path = os.path.join(path, author_name, item_type_plural, item_name)
    if not os.path.exists(source_path):
        raise click.ClickException(
            'Item "{}" not found in source folder.'.format(item_name)
        )
    return source_path


def try_get_vendorized_item_target_path(
    path: str, author_name: str, item_type_plural: str, item_name: str
) -> str:
    """
    Get the item target path.

    :param path: the target path root
    :param author_name the author name
    :param item_type_plural: the item type (plural)
    :param item_name: the item name

    :return: the item target path
    """
    target_path = os.path.join(path, "vendor", author_name, item_type_plural, item_name)
    if os.path.exists(target_path):
        raise click.ClickException(
            'Item "{}" already exists in target folder.'.format(item_name)
        )
    return target_path


def _copy_package_directory(ctx, package_path, item_type, item_name, author_name):
    """
     Copy a package directory to the agent vendor resources.

    :param ctx: the CLI context .
    :param package_path: the path to the package to be added.
    :param item_type: the type of the package.
    :param item_name: the name of the package.
    :param author_name: the author of the package.
    :return: None
    :raises SystemExit: if the copy raises an exception.
    """
    # copy the item package into the agent's supported packages.
    item_type_plural = item_type + "s"
    src = str(package_path.absolute())
    dest = os.path.join(ctx.cwd, "vendor", author_name, item_type_plural, item_name)
    logger.debug("Copying {} modules. src={} dst={}".format(item_type, src, dest))
    try:
        shutil.copytree(src, dest)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)

    Path(ctx.cwd, "vendor", author_name, item_type_plural, "__init__.py").touch()


def _find_item_locally(ctx, item_type, item_public_id) -> Path:
    """
    Find an item in the registry or in the AEA directory.

    :param ctx: the CLI context.
    :param item_type: the type of the item to load. One of: protocols, connections, skills
    :param item_public_id: the public id of the item to find.
    :return: path to the package directory (either in registry or in aea directory).
    :raises SystemExit: if the search fails.
    """
    item_type_plural = item_type + "s"
    item_name = item_public_id.name

    # check in registry
    registry_path = os.path.join(ctx.cwd, ctx.agent_config.registry_path)
    package_path = Path(
        registry_path, item_public_id.author, item_type_plural, item_name
    )
    config_file_name = _get_default_configuration_file_name_from_type(item_type)
    item_configuration_filepath = package_path / config_file_name
    if not item_configuration_filepath.exists():
        # then check in aea dir
        registry_path = AEA_DIR
        package_path = Path(registry_path, item_type_plural, item_name)
        item_configuration_filepath = package_path / config_file_name
        if not item_configuration_filepath.exists():
            logger.error("Cannot find {}: '{}'.".format(item_type, item_public_id))
            sys.exit(1)

    # try to load the item configuration file
    try:
        item_configuration_loader = ConfigLoader.from_configuration_type(
            ConfigurationType(item_type)
        )
        item_configuration = item_configuration_loader.load(
            item_configuration_filepath.open()
        )
    except ValidationError as e:
        logger.error(
            "{} configuration file not valid: {}".format(item_type.capitalize(), str(e))
        )
        sys.exit(1)

    # check that the configuration file of the found package matches the expected author and version.
    version = item_configuration.version
    author = item_configuration.author
    if item_public_id.author != author or item_public_id.version != version:
        logger.error(
            "Cannot find {} with author and version specified.".format(item_type)
        )
        sys.exit(1)

    return package_path
