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
"""Module with package utils of the aea cli."""
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import click
from jsonschema import ValidationError

from aea import AEA_DIR, get_current_aea_version
from aea.cli.fingerprint import fingerprint_item
from aea.cli.utils.config import (
    dump_item_config,
    get_non_vendor_package_path,
    load_item_config,
)
from aea.cli.utils.constants import NOT_PERMITTED_AUTHORS
from aea.cli.utils.context import Context
from aea.cli.utils.loggers import logger
from aea.configurations.base import (
    AgentConfig,
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    PackageConfiguration,
    PackageType,
    _compute_fingerprint,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.constants import AGENT, DEFAULT_AEA_CONFIG_FILE
from aea.configurations.constants import (
    DISTRIBUTED_PACKAGES as DISTRIBUTED_PACKAGES_STR,
)
from aea.configurations.constants import (
    IMPORT_TEMPLATE_1,
    IMPORT_TEMPLATE_2,
    PACKAGES,
    PACKAGE_PUBLIC_ID_VAR_NAME,
    SKILL,
    VENDOR,
)
from aea.configurations.data_types import PackageId, PublicId
from aea.configurations.loader import ConfigLoader
from aea.configurations.manager import AgentConfigManager
from aea.configurations.utils import replace_component_ids
from aea.crypto.helpers import get_wallet_from_agent_config, private_key_verify
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.exceptions import AEAEnforceError
from aea.helpers.base import compute_specifier_from_version, recursive_update
from aea.helpers.dependency_tree import COMPONENTS
from aea.helpers.io import open_file
from aea.helpers.ipfs.base import IPFSHashOnly
from aea.helpers.sym_link import create_symlink


DISTRIBUTED_PACKAGES = [PublicId.from_str(dp) for dp in DISTRIBUTED_PACKAGES_STR]
ROOT = Path(".")


def verify_private_keys_ctx(
    ctx: Context,
    aea_project_path: Path = ROOT,
    password: Optional[str] = None,
) -> None:
    """
    Verify private keys with ctx provided.

    :param ctx: Context
    :param aea_project_path: the path to the aea project
    :param password: the password to encrypt/decrypt the private key.
    """
    try:
        AgentConfigManager.verify_private_keys(
            aea_project_path,
            private_key_helper=private_key_verify,
            substitude_env_vars=False,
            password=password,
        ).dump_config()
        agent_config = AgentConfigManager.verify_private_keys(
            aea_project_path,
            private_key_helper=private_key_verify,
            password=password,
        ).agent_config
        if ctx is not None:
            ctx.agent_config = agent_config
    except ValueError as e:  # pragma: nocover
        raise click.ClickException(str(e))


def validate_package_name(package_name: str) -> None:
    """Check that the package name matches the pattern r"[a-zA-Z_][a-zA-Z0-9_]*".

    >>> validate_package_name("this_is_a_good_package_name")
    >>> validate_package_name("this-is-not")
    Traceback (most recent call last):
    ...
    click.exceptions.BadParameter: this-is-not is not a valid package name.

    :param package_name: the package name
    """
    if re.fullmatch(PublicId.PACKAGE_NAME_REGEX, package_name) is None:
        raise click.BadParameter("{} is not a valid package name.".format(package_name))


def _is_valid_author_handle(author: str) -> bool:
    """
    Check that the author matches the pattern r"[a-zA-Z_][a-zA-Z0-9_]*".

    >>> _is_valid_author_handle("this_is_a_good_author_name")
    ...
    True
    >>> _is_valid_author_handle("this-is-not")
    ...
    False

    :param author: author name
    :return: bool indicating whether author name is valid
    """
    if re.fullmatch(PublicId.AUTHOR_REGEX, author) is None:
        return False
    return True


def _is_permitted_author_handle(author: str) -> bool:
    """
    Check that the author handle is permitted.

    :param author: the author
    :return: bool
    """
    result = author not in NOT_PERMITTED_AUTHORS
    return result


def try_get_item_source_path(
    path: str, author_name: Optional[str], item_type_plural: str, item_name: str
) -> str:
    """
    Get the item source path.

    :param path: the source path root
    :param author_name: the name of the author of the item
    :param item_type_plural: the item type (plural)
    :param item_name: the item name

    :return: the item source path
    """
    if author_name is None:
        source_path = os.path.join(path, item_type_plural, item_name)
    else:
        source_path = os.path.join(path, author_name, item_type_plural, item_name)
    if not os.path.exists(source_path):
        raise click.ClickException(
            f'Item "{author_name}/{item_name}" not found in source folder "{source_path}".'
        )
    return source_path


def try_get_item_target_path(
    path: str, author_name: str, item_type_plural: str, item_name: str
) -> str:
    """
    Get the item target path.

    :param path: the target path root
    :param author_name: the author name
    :param item_type_plural: the item type (plural)
    :param item_name: the item name

    :return: the item target path
    """
    target_path = os.path.join(path, author_name, item_type_plural, item_name)
    if os.path.exists(target_path):
        path_ = Path(target_path)
        raise click.ClickException(
            f'Item "{path_.name}" already exists in target folder "{path_.parent}".'
        )
    return target_path


def get_package_path(
    project_directory: str,
    item_type: str,
    public_id: PublicId,
    is_vendor: bool = True,
    vendor_dirname: str = VENDOR,
) -> str:
    """
    Get a vendorized path for a package.

    :param project_directory: path to search packages
    :param item_type: item type.
    :param public_id: item public ID.
    :param is_vendor: flag for vendorized path (True by default).
    :param vendor_dirname: name of the vendor directory: default "vendor"

    :return: vendorized destination path for package.
    """
    item_type_plural = item_type + "s"
    if is_vendor:
        return os.path.join(
            project_directory,
            vendor_dirname,
            public_id.author,
            item_type_plural,
            public_id.name,
        )
    return os.path.join(project_directory, item_type_plural, public_id.name)


def get_package_path_unified(
    project_directory: str,
    agent_config: AgentConfig,
    item_type: str,
    public_id: PublicId,
) -> str:
    """
    Get a path for a package, either vendor or not.

    That is:
    - if the author in the public id is not the same of the AEA project author,
      just look into vendor/
    - Otherwise, first look into local packages, then into vendor/.

    :param project_directory: directory to look for packages.
    :param agent_config: agent configuration.
    :param item_type: item type.
    :param public_id: item public ID.

    :return: vendorized destination path for package.
    """
    vendor_path = get_package_path(
        project_directory, item_type, public_id, is_vendor=True
    )
    if agent_config.author != public_id.author or not is_item_present(
        project_directory, agent_config, item_type, public_id, is_vendor=False
    ):
        return vendor_path
    return get_package_path(project_directory, item_type, public_id, is_vendor=False)


def get_dotted_package_path_unified(
    project_directory: str, agent_config: AgentConfig, *args: Any
) -> str:
    """
    Get a *dotted* path for a package, either vendor or not.

    :param project_directory: base dir for package lookup.
    :param agent_config: AgentConfig.
    :param args: arguments for 'get_package_path_unified'

    :return: the dotted path to the package.
    """
    path = get_package_path_unified(project_directory, agent_config, *args)
    path_relative_to_cwd = Path(path).relative_to(Path(project_directory))
    relative_path_str = str(path_relative_to_cwd).replace(os.sep, ".")
    return relative_path_str


def copy_package_directory(src: Path, dst: str) -> Path:
    """
     Copy a package directory to the agent vendor resources.

    :param src: source path to the package to be added.
    :param dst: str package destination path.

    :return: copied folder target path.
    :raises ClickException: if the copy raises an exception.
    """
    # copy the item package into the agent's supported packages.
    src_path = str(src.absolute())
    logger.debug("Copying modules. src={} dst={}".format(src_path, dst))
    try:
        shutil.copytree(src_path, dst)
    except Exception as e:  # pylint: disable=broad-except
        raise click.ClickException(str(e))

    items_folder = os.path.split(dst)[0]
    Path(items_folder, "__init__.py").touch()
    return Path(dst)


def find_item_locally(
    ctx: Context,
    item_type: str,
    item_public_id: PublicId,
    package_type_config_class: Optional[Dict] = None,
) -> Tuple[Path, ComponentConfiguration]:
    """
    Find an item in the local registry.

    :param ctx: the CLI context.
    :param item_type: the type of the item to load. One of: protocols, connections, skills
    :param item_public_id: the public id of the item to find.
    :param package_type_config_class: Package type to config loader mappings.

    :return: tuple of path to the package directory (either in registry or in aea directory) and component configuration

    :raises ClickException: if the search fails.
    """
    item_type_plural = item_type + "s"
    item_name = item_public_id.name

    try:
        registry_path = ctx.registry_path
    except ValueError as e:
        raise click.ClickException(str(e))

    # check in registry
    package_path = Path(
        registry_path, item_public_id.author, item_type_plural, item_name
    )
    config_file_name = _get_default_configuration_file_name_from_type(item_type)
    item_configuration_filepath = package_path / config_file_name
    if not item_configuration_filepath.exists():
        raise click.ClickException(
            "Cannot find {}: '{}'.".format(item_type, item_public_id)
        )

    # try to load the item configuration file
    try:
        item_configuration_loader = ConfigLoader.from_configuration_type(
            PackageType(item_type), package_type_config_class=package_type_config_class
        )
        with open_file(item_configuration_filepath) as fp:
            item_configuration = item_configuration_loader.load(fp)
    except ValidationError as e:
        raise click.ClickException(
            "{} configuration file not valid: {}".format(item_type.capitalize(), str(e))
        )

    # check that the configuration file of the found package matches the expected author and version.
    version = item_configuration.version
    author = item_configuration.author
    if item_public_id.author != author or (
        not item_public_id.package_version.is_latest
        and item_public_id.version != version
    ):
        raise click.ClickException(
            "Cannot find {} with author and version specified.".format(item_type)
        )

    return package_path, item_configuration


def find_item_in_distribution(  # pylint: disable=unused-argument
    ctx: Context,
    item_type: str,
    item_public_id: PublicId,
    package_type_config_class: Optional[Dict] = None,
) -> Path:
    """
    Find an item in the AEA directory.

    :param ctx: the CLI context.
    :param item_type: the type of the item to load. One of: protocols, connections, skills
    :param item_public_id: the public id of the item to find.
    :param package_type_config_class: Package type to config loader mappings.
    :return: path to the package directory (either in registry or in aea directory).
    :raises ClickException: if the search fails.
    """
    item_type_plural = item_type + "s"
    item_name = item_public_id.name

    # check in aea dir
    package_path = Path(AEA_DIR, item_type_plural, item_name)
    config_file_name = _get_default_configuration_file_name_from_type(item_type)
    item_configuration_filepath = package_path / config_file_name
    if not item_configuration_filepath.exists():
        raise click.ClickException(
            "Cannot find {}: '{}'.".format(item_type, item_public_id)
        )

    # try to load the item configuration file
    try:
        item_configuration_loader = ConfigLoader.from_configuration_type(
            PackageType(item_type), package_type_config_class=package_type_config_class
        )
        with open_file(item_configuration_filepath) as fp:
            item_configuration = item_configuration_loader.load(fp)
    except ValidationError as e:
        raise click.ClickException(
            "{} configuration file not valid: {}".format(item_type.capitalize(), str(e))
        )

    # check that the configuration file of the found package matches the expected author and version.
    version = item_configuration.version
    author = item_configuration.author
    if item_public_id.author != author or (
        not item_public_id.package_version.is_latest
        and item_public_id.version != version
    ):
        raise click.ClickException(
            "Cannot find {} with author and version specified.".format(item_type)
        )

    return package_path  # pragma: no cover


def validate_author_name(author: Optional[str] = None) -> str:
    """
    Validate an author name.

    :param author: the author name (optional)
    :return: validated author name
    """
    is_acceptable_author = False
    if (
        author is not None
        and _is_valid_author_handle(author)
        and _is_permitted_author_handle(author)
    ):
        is_acceptable_author = True
        valid_author = author
    while not is_acceptable_author:
        author_prompt = click.prompt(
            "Please enter the author handle you would like to use", type=str
        )
        valid_author = author_prompt
        if _is_valid_author_handle(author_prompt) and _is_permitted_author_handle(
            author_prompt
        ):
            is_acceptable_author = True
        elif not _is_valid_author_handle(author_prompt):
            is_acceptable_author = False
            click.echo(
                "Not a valid author handle. Please try again. "
                "Author handles must satisfy the following regex: {}".format(
                    PublicId.AUTHOR_REGEX
                )
            )
        elif not _is_permitted_author_handle(author_prompt):
            is_acceptable_author = False
            click.echo(
                "Not a permitted author handle. The following author handles are not allowed: {}".format(
                    NOT_PERMITTED_AUTHORS
                )
            )

    return valid_author


def is_fingerprint_correct(
    package_path: Path, item_config: PackageConfiguration
) -> bool:
    """
    Validate fingerprint of item before adding.

    :param package_path: path to a package folder.
    :param item_config: item configuration.
    :return: bool indicating correctness of fingerprint.
    """
    fingerprint = _compute_fingerprint(
        package_path, ignore_patterns=item_config.fingerprint_ignore_patterns
    )
    return item_config.fingerprint == fingerprint


def register_item(ctx: Context, item_type: str, item_public_id: PublicId) -> None:
    """
    Register item in agent configuration.

    :param ctx: click context object.
    :param item_type: type of item.
    :param item_public_id: PublicId of item.
    """
    logger.debug(
        "Registering the {} into {}".format(item_type, DEFAULT_AEA_CONFIG_FILE)
    )
    supported_items = get_items(ctx.agent_config, item_type)
    supported_items.add(item_public_id)
    with open_file(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w") as fp:
        ctx.agent_loader.dump(ctx.agent_config, fp)


def is_item_present_unified(
    ctx: Context, item_type: str, item_public_id: PublicId
) -> bool:
    """
    Check if item is present, either vendor or not.

    That is:
    - if the author in the public id is not the same of the AEA project author,
      just look into vendor/
    - Otherwise, first look into local packages, then into vendor/.

    :param ctx: context object.
    :param item_type: type of an item.
    :param item_public_id: PublicId of an item.
    :return: True if the item is present, False otherwise.
    """
    is_in_vendor = is_item_present(
        ctx.cwd, ctx.agent_config, item_type, item_public_id, is_vendor=True
    )
    if item_public_id.author != ctx.agent_config.author:
        return is_in_vendor
    return is_in_vendor or is_item_present(
        ctx.cwd, ctx.agent_config, item_type, item_public_id, is_vendor=False
    )


def is_item_present(
    path: str,
    agent_config: AgentConfig,
    item_type: str,
    item_public_id: PublicId,
    is_vendor: bool = True,
    with_version: bool = False,
) -> bool:
    """
    Check if item is already present in AEA.

    Optionally, consider the check also with the version.

    :param path: path to look for packages.
    :param agent_config: agent config
    :param item_type: type of an item.
    :param item_public_id: PublicId of an item.
    :param is_vendor: flag for vendorized path (True by default).
    :param with_version: if true, consider also the package version.

    :return: boolean is item present.
    """
    item_path = Path(
        get_package_path(path, item_type, item_public_id, is_vendor=is_vendor)
    )
    registered_item_public_id = get_item_public_id_by_author_name(
        agent_config, item_type, item_public_id.author, item_public_id.name
    )
    is_item_registered_no_version = registered_item_public_id is not None
    does_path_exist = Path(item_path).exists()
    if item_public_id.package_version.is_latest or not with_version:
        return is_item_registered_no_version and does_path_exist

    # the following makes sense because public id is not latest
    component_id = ComponentId(ComponentType(item_type), item_public_id.without_hash())
    component_is_registered = component_id in {
        cid.without_hash() for cid in agent_config.package_dependencies
    }
    return component_is_registered and does_path_exist


def is_item_with_hash_present(
    path: str, agent_config: AgentConfig, package_hash: str, is_vendor: bool = True
) -> Optional[PublicId]:
    """Returns a public id if item with provided hash is present."""

    for component_id in agent_config.all_components_id:
        if component_id.public_id.hash == package_hash:
            return component_id.public_id

    hash_tool = IPFSHashOnly()
    package_path = Path(path) / ("vendor" if is_vendor else "packages")
    for component_type, config_file_name in COMPONENTS:
        for config_file_path in package_path.glob(f"**/{config_file_name}"):
            component_path = config_file_path.parent
            calculated_hash = hash_tool.hash_directory(str(component_path))
            if package_hash == calculated_hash:
                return load_item_config(component_type, component_path).public_id
    return None


def get_item_id_present(
    agent_config: AgentConfig, item_type: str, item_public_id: PublicId
) -> PublicId:
    """
    Get the item present in AEA.

    :param agent_config: AgentConfig.
    :param item_type: type of an item.
    :param item_public_id: PublicId of an item.

    :return: boolean is item present.
    :raises: AEAEnforceError
    """
    registered_item_public_id = get_item_public_id_by_author_name(
        agent_config, item_type, item_public_id.author, item_public_id.name
    )
    if registered_item_public_id is None:
        raise AEAEnforceError("Cannot find item.")  # pragma: nocover
    return registered_item_public_id


def get_item_public_id_by_author_name(
    agent_config: AgentConfig, item_type: str, author: str, name: str
) -> Optional[PublicId]:
    """
    Get component public_id by author and name.

    :param agent_config: AgentConfig
    :param item_type: str. component type: connection, skill, contract, protocol
    :param author: str. author name
    :param name: str. component name

    :return: PublicId
    """
    items_in_config = {
        (x.author, x.name): x for x in get_items(agent_config, item_type)
    }
    return items_in_config.get((author, name), None)


def get_items(agent_config: AgentConfig, item_type: str) -> Set[PublicId]:
    """
    Get all items of certain type registered in AgentConfig.

    :param agent_config: AgentConfig
    :param item_type: str. component type: connection, skill, contract, protocol

    :return: set of public ids
    """
    item_type_plural = item_type + "s"
    return getattr(agent_config, item_type_plural)


def is_distributed_item(item_public_id: PublicId) -> bool:
    """
    Check whether the item public id correspond to a package in the distribution.

    If the provided item has version 'latest', only the prefixes are compared.
    Otherwise, the function will try to match the exact version occurrence among the distributed packages.

    :param item_public_id: public id of the item
    :return: bool, indicating whether distributed or not
    """
    if item_public_id.package_version.is_latest:
        return any(item_public_id.same_prefix(other) for other in DISTRIBUTED_PACKAGES)
    return item_public_id in DISTRIBUTED_PACKAGES


def _override_ledger_configurations(agent_config: AgentConfig) -> None:
    """Override LedgerApis configurations with agent override configurations."""
    ledger_component_id = ComponentId(
        ComponentType.CONNECTION, PublicId.from_str("fetchai/ledger:latest")
    )
    prefix_to_component_configuration = {
        key.component_prefix: value
        for key, value in agent_config.component_configurations.items()
    }
    if ledger_component_id.component_prefix not in prefix_to_component_configuration:
        return
    ledger_apis_config = prefix_to_component_configuration[
        ledger_component_id.component_prefix
    ]["config"].get("ledger_apis", {})
    recursive_update(LedgerApis.ledger_api_configs, ledger_apis_config)


def try_get_balance(  # pylint: disable=unused-argument
    agent_config: AgentConfig, wallet: Wallet, type_: str
) -> int:
    """
    Try to get wallet balance.

    :param agent_config: agent config object.
    :param wallet: wallet object.
    :param type_: type of ledger API.

    :return: token balance.
    """
    try:
        if not LedgerApis.has_ledger(type_):  # pragma: no cover
            raise ValueError("No ledger api config for {} available.".format(type_))
        address = wallet.addresses.get(type_)
        if address is None:  # pragma: no cover
            raise ValueError("No key '{}' in wallet.".format(type_))
        balance = LedgerApis.get_balance(type_, address)
        if balance is None:  # pragma: no cover
            raise ValueError("No balance returned!")
        return balance
    except ValueError as e:  # pragma: no cover
        raise click.ClickException(str(e))


def get_wallet_from_context(ctx: Context, password: Optional[str] = None) -> Wallet:
    """
    Get wallet from current click Context.

    :param ctx: click context
    :param password: the password to encrypt/decrypt private keys

    :return: wallet
    """
    verify_private_keys_ctx(ctx=ctx, password=password)
    wallet = get_wallet_from_agent_config(ctx.agent_config, password=password)
    return wallet


def update_item_public_id_in_init(
    item_type: str, package_path: Path, item_id: PublicId
) -> None:
    """
    Update item config and item config file.

    :param item_type: type of item.
    :param package_path: path to a package folder.
    :param item_id: public_id
    """
    if item_type != SKILL:
        return
    init_filepath = os.path.join(package_path, "__init__.py")
    with open_file(init_filepath, "r") as f:
        file_content = f.readlines()
    with open_file(init_filepath, "w") as f:
        for line in file_content:
            if PACKAGE_PUBLIC_ID_VAR_NAME in line:
                f.write(
                    f'{PACKAGE_PUBLIC_ID_VAR_NAME} = PublicId.from_str("{str(item_id)}")'
                )
            else:
                f.write(line)


def update_references(
    ctx: Context, replacements: Dict[ComponentId, ComponentId]
) -> None:
    """
    Update references across an AEA project.

    Caveat: the update is done in a sequential manner. There is no check
    of multiple updates, due to the occurrence of transitive relations.
    E.g. replacements as {c1: c2, c2: c3} might lead to c1 replaced with c3
      instead of c2.

    :param ctx: the context.
    :param replacements: mapping from old component ids to new component ids.
    """
    # preprocess replacement so to index them by component type
    replacements_by_type: Dict[ComponentType, Dict[PublicId, PublicId]] = {}
    for old, new in replacements.items():
        replacements_by_type.setdefault(old.component_type, {})[
            old.public_id
        ] = new.public_id

    aea_project_root = Path(ctx.cwd)
    # update agent configuration
    agent_config = load_item_config(PackageType.AGENT.value, aea_project_root)
    replace_component_ids(agent_config, replacements_by_type)
    dump_item_config(agent_config, aea_project_root)

    # update every (non-vendor) AEA package.
    for package_path in get_non_vendor_package_path(aea_project_root):
        package_type = PackageType(package_path.parent.name[:-1])
        package_config = load_item_config(package_type.value, package_path)
        replace_component_ids(package_config, replacements_by_type)
        dump_item_config(package_config, package_path)


def create_symlink_vendor_to_local(
    ctx: Context, item_type: str, public_id: PublicId
) -> None:
    """
    Creates a symlink from the vendor to the local folder.

    :param ctx: click context
    :param item_type: item type
    :param public_id: public_id of the item
    """
    vendor_path_str = get_package_path(ctx.cwd, item_type, public_id, is_vendor=True)
    local_path = get_package_path(ctx.cwd, item_type, public_id, is_vendor=False)
    vendor_path = Path(vendor_path_str)
    if not os.path.exists(vendor_path.parent):
        os.makedirs(vendor_path.parent)
    create_symlink(vendor_path, Path(local_path), Path(ctx.cwd))


def create_symlink_packages_to_vendor(ctx: Context) -> None:
    """
    Creates a symlink from a local packages to the vendor folder.

    :param ctx: click context
    """
    if not os.path.exists(PACKAGES):
        create_symlink(Path(PACKAGES), Path(VENDOR), Path(ctx.cwd))


def replace_all_import_statements(
    aea_project_path: Path,
    item_type: ComponentType,
    old_public_id: PublicId,
    new_public_id: PublicId,
) -> None:
    """
    Replace all import statements in Python modules of all the non-vendor packages.

    The function looks for two patterns:
    - from packages.<author>.<item_type_plural>.<name>
    - import packages.<author>.<item_type_plural>.<name>

    :param aea_project_path: path to the AEA project.
    :param item_type: the item type.
    :param old_public_id: the old public id.
    :param new_public_id: the new public id.
    """
    old_formats = dict(
        author=old_public_id.author, type=item_type.to_plural(), name=old_public_id.name
    )
    new_formats = dict(
        author=new_public_id.author, type=item_type.to_plural(), name=new_public_id.name
    )
    old_import_1 = IMPORT_TEMPLATE_1.format(**old_formats)
    old_import_2 = IMPORT_TEMPLATE_2.format(**old_formats)
    new_import_1 = IMPORT_TEMPLATE_1.format(**new_formats)
    new_import_2 = IMPORT_TEMPLATE_2.format(**new_formats)

    pattern_1 = re.compile(rf"^{old_import_1}", re.MULTILINE)
    pattern_2 = re.compile(rf"^{old_import_2}", re.MULTILINE)

    for package_path in get_non_vendor_package_path(aea_project_path):
        for python_module in package_path.rglob("*.py"):
            content = python_module.read_text()
            content = pattern_1.sub(new_import_1, content)
            content = pattern_2.sub(new_import_2, content)
            python_module.write_text(content)


def fingerprint_all(ctx: Context) -> None:
    """
    Fingerprint all non-vendor packages.

    :param ctx: the CLI context.
    """

    aea_project_path = Path(ctx.cwd)
    for package_path in get_non_vendor_package_path(aea_project_path):
        item_type = package_path.parent.name[:-1]
        config = load_item_config(item_type, package_path)
        fingerprint_item(ctx, item_type, config.public_id)


def update_aea_version_range(package_configuration: PackageConfiguration) -> None:
    """Update 'aea_version' range."""
    version = get_current_aea_version()
    if not package_configuration.aea_version_specifiers.contains(version):
        new_aea_version = compute_specifier_from_version(version)
        old_aea_version = package_configuration.aea_version
        click.echo(
            f"Updating AEA version specifier from {old_aea_version} to {new_aea_version}."
        )
        package_configuration.aea_version = new_aea_version


def list_available_packages(
    project_path: Union[Path, str]
) -> List[Tuple[PackageId, Path]]:
    """Returns a list of paths for all available packages in an AEA project."""

    project_path = Path(project_path)
    agent_config = load_item_config(AGENT, project_path)
    packages = []

    for component_type in (
        ComponentType.PROTOCOL,
        ComponentType.CONNECTION,
        ComponentType.CONTRACT,
        ComponentType.SKILL,
    ):
        components = getattr(agent_config, component_type.to_plural(), set())
        for public_id in components:
            package_path = Path(
                get_package_path(
                    str(project_path), component_type.value, public_id, is_vendor=True
                )
            )
            if not package_path.is_dir():
                package_path = Path(
                    get_package_path(
                        str(project_path),
                        component_type.value,
                        public_id,
                        is_vendor=False,
                    ),
                )

            packages.append((PackageId(component_type.value, public_id), package_path))

    return packages
