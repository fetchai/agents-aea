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
"""Module with package utils of the aea cli."""
import os
import re
import shutil
from pathlib import Path
from typing import Dict, Optional, Set, Tuple

import click
from jsonschema import ValidationError

from aea import AEA_DIR
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
    PackageType,
    PublicId,
    _compute_fingerprint,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.constants import DEFAULT_AEA_CONFIG_FILE
from aea.configurations.constants import (
    DISTRIBUTED_PACKAGES as DISTRIBUTED_PACKAGES_STR,
)
from aea.configurations.constants import (
    IMPORT_TEMPLATE_1,
    IMPORT_TEMPLATE_2,
    LEDGER_CONNECTION,
    PACKAGES,
    PACKAGE_PUBLIC_ID_VAR_NAME,
    SKILL,
    VENDOR,
)
from aea.configurations.loader import ConfigLoader
from aea.configurations.utils import replace_component_ids
from aea.crypto.helpers import verify_or_create_private_keys
from aea.crypto.ledger_apis import DEFAULT_LEDGER_CONFIGS, LedgerApis
from aea.crypto.wallet import Wallet
from aea.exceptions import AEAEnforceError
from aea.helpers.base import recursive_update
from aea.helpers.sym_link import create_symlink


DISTRIBUTED_PACKAGES = [PublicId.from_str(dp) for dp in DISTRIBUTED_PACKAGES_STR]
ROOT = Path(".")


def verify_or_create_private_keys_ctx(
    ctx: Context, aea_project_path: Path = ROOT, exit_on_error: bool = True,
) -> None:
    """
    Verify or create private keys with ctx provided.

    :param ctx: Context
    """
    try:
        agent_config = verify_or_create_private_keys(aea_project_path, exit_on_error)
        if ctx is not None:
            ctx.agent_config = agent_config
    except ValueError as e:  # pragma: nocover
        click.ClickException(str(e))


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


def _is_valid_author_handle(author: str) -> bool:
    """
    Check that the author matches the pattern r"[a-zA-Z_][a-zA-Z0-9_]*".

    >>> _is_valid_author_handle("this_is_a_good_author_name")
    ...
    True
    >>> _is_valid_author_handle("this-is-not")
    ...
    False
    """
    if re.fullmatch(PublicId.AUTHOR_REGEX, author) is None:
        return False
    return True


def _is_permitted_author_handle(author: str) -> bool:
    """
    Check that the author handle is permitted.

    :param author: the author
    :retun: bool
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
            'Item "{}" not found in source folder.'.format(item_name)
        )
    return source_path


def try_get_item_target_path(
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
    target_path = os.path.join(path, author_name, item_type_plural, item_name)
    if os.path.exists(target_path):
        raise click.ClickException(
            'Item "{}" already exists in target folder.'.format(item_name)
        )
    return target_path


def get_package_path(
    ctx: Context, item_type: str, public_id: PublicId, is_vendor: bool = True
) -> str:
    """
    Get a vendorized path for a package.

    :param ctx: context.
    :param item_type: item type.
    :param public_id: item public ID.
    :param is_vendor: flag for vendorized path (True by defaut).

    :return: vendorized estenation path for package.
    """
    item_type_plural = item_type + "s"
    if is_vendor:
        return os.path.join(
            ctx.cwd, VENDOR, public_id.author, item_type_plural, public_id.name
        )
    return os.path.join(ctx.cwd, item_type_plural, public_id.name)


def get_package_path_unified(ctx: Context, item_type: str, public_id: PublicId) -> str:
    """
    Get a path for a package, either vendor or not.

    That is:
    - if the author in the public id is not the same of the AEA project author,
      just look into vendor/
    - Otherwise, first look into local packages, then into vendor/.

    :param ctx: context.
    :param item_type: item type.
    :param public_id: item public ID.

    :return: vendorized estenation path for package.
    """
    vendor_path = get_package_path(ctx, item_type, public_id, is_vendor=True)
    if ctx.agent_config.author != public_id.author or not is_item_present(
        ctx, item_type, public_id, is_vendor=False
    ):
        return vendor_path
    return get_package_path(ctx, item_type, public_id, is_vendor=False)


def copy_package_directory(src: Path, dst: str) -> Path:
    """
     Copy a package directory to the agent vendor resources.

    :param src: source path to the package to be added.
    :param dst: str package destenation path.

    :return: copied folder target path.
    :raises SystemExit: if the copy raises an exception.
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
    ctx: Context, item_type: str, item_public_id: PublicId
) -> Tuple[Path, ComponentConfiguration]:
    """
    Find an item in the local registry.

    :param ctx: the CLI context.
    :param item_type: the type of the item to load. One of: protocols, connections, skills
    :param item_public_id: the public id of the item to find.

    :return: tuple of path to the package directory (either in registry or in aea directory) and component configuration

    :raises SystemExit: if the search fails.
    """
    item_type_plural = item_type + "s"
    item_name = item_public_id.name

    # check in registry
    registry_path = (
        os.path.join(ctx.cwd, ctx.agent_config.registry_path)
        if ctx.registry_path is None
        else ctx.registry_path
    )
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
            PackageType(item_type)
        )
        item_configuration = item_configuration_loader.load(
            item_configuration_filepath.open()
        )
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
    ctx: Context, item_type: str, item_public_id: PublicId
) -> Path:
    """
    Find an item in the AEA directory.

    :param ctx: the CLI context.
    :param item_type: the type of the item to load. One of: protocols, connections, skills
    :param item_public_id: the public id of the item to find.
    :return: path to the package directory (either in registry or in aea directory).
    :raises SystemExit: if the search fails.
    """
    item_type_plural = item_type + "s"
    item_name = item_public_id.name

    # check in aea dir
    registry_path = AEA_DIR
    package_path = Path(registry_path, item_type_plural, item_name)
    config_file_name = _get_default_configuration_file_name_from_type(item_type)
    item_configuration_filepath = package_path / config_file_name
    if not item_configuration_filepath.exists():
        raise click.ClickException(
            "Cannot find {}: '{}'.".format(item_type, item_public_id)
        )

    # try to load the item configuration file
    try:
        item_configuration_loader = ConfigLoader.from_configuration_type(
            PackageType(item_type)
        )
        item_configuration = item_configuration_loader.load(
            item_configuration_filepath.open()
        )
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


def is_fingerprint_correct(package_path: Path, item_config) -> bool:
    """
    Validate fingerprint of item before adding.

    :param package_path: path to a package folder.
    :param item_config: item configuration.

    :return: None.
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

    :return: None.
    """
    logger.debug(
        "Registering the {} into {}".format(item_type, DEFAULT_AEA_CONFIG_FILE)
    )
    supported_items = get_items(ctx.agent_config, item_type)
    supported_items.add(item_public_id)
    ctx.agent_loader.dump(
        ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w")
    )


def is_item_present_unified(ctx: Context, item_type: str, item_public_id: PublicId):
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
    is_in_vendor = is_item_present(ctx, item_type, item_public_id, is_vendor=True)
    if item_public_id.author != ctx.agent_config.author:
        return is_in_vendor
    return is_in_vendor or is_item_present(
        ctx, item_type, item_public_id, is_vendor=False
    )


def is_item_present(
    ctx: Context,
    item_type: str,
    item_public_id: PublicId,
    is_vendor: bool = True,
    with_version: bool = False,
) -> bool:
    """
    Check if item is already present in AEA.

    Optionally, consider the check also with the version.

    :param ctx: context object.
    :param item_type: type of an item.
    :param item_public_id: PublicId of an item.
    :param is_vendor: flag for vendorized path (True by default).
    :param with_version: if true, consider also the package version.

    :return: boolean is item present.
    """
    item_path = Path(
        get_package_path(ctx, item_type, item_public_id, is_vendor=is_vendor)
    )
    registered_item_public_id = get_item_public_id_by_author_name(
        ctx.agent_config, item_type, item_public_id.author, item_public_id.name
    )
    is_item_registered_no_version = registered_item_public_id is not None
    does_path_exist = Path(item_path).exists()
    if item_public_id.package_version.is_latest or not with_version:
        return is_item_registered_no_version and does_path_exist

    # the following makes sense because public id is not latest
    component_id = ComponentId(ComponentType(item_type), item_public_id)
    component_is_registered = component_id in ctx.agent_config.package_dependencies
    return component_is_registered and does_path_exist


def get_item_id_present(
    ctx: Context, item_type: str, item_public_id: PublicId
) -> PublicId:
    """
    Get the item present in AEA.

    :param ctx: context object.
    :param item_type: type of an item.
    :param item_public_id: PublicId of an item.

    :return: boolean is item present.
    :raises: AEAEnforceError
    """
    registered_item_public_id = get_item_public_id_by_author_name(
        ctx.agent_config, item_type, item_public_id.author, item_public_id.name
    )
    if registered_item_public_id is None:
        raise AEAEnforceError("Cannot find item.")  # pragma: nocover
    return registered_item_public_id


def get_item_public_id_by_author_name(
    agent_config: AgentConfig, item_type: str, author: str, name: str
) -> Optional[PublicId]:
    """
    Get component public_id by author and namme.

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
    """
    if item_public_id.package_version.is_latest:
        return any(item_public_id.same_prefix(other) for other in DISTRIBUTED_PACKAGES)
    return item_public_id in DISTRIBUTED_PACKAGES


def _override_ledger_configurations(agent_config: AgentConfig) -> None:
    """Override LedgerApis configurations with agent override configurations."""
    ledger_component_id = ComponentId(
        ComponentType.CONNECTION, PublicId.from_str(LEDGER_CONNECTION)
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

    :retun: token balance.
    """
    try:
        if type_ not in DEFAULT_LEDGER_CONFIGS:  # pragma: no cover
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


def get_wallet_from_context(ctx: Context) -> Wallet:
    """
    Get wallet from current click Context.

    :param ctx: click context

    :return: wallet
    """
    verify_or_create_private_keys_ctx(ctx=ctx)
    wallet = get_wallet_from_agent_config(ctx.agent_config)
    return wallet


def get_wallet_from_agent_config(agent_config: AgentConfig) -> Wallet:
    """Get wallet from agent_cofig provided."""
    private_key_paths: Dict[str, Optional[str]] = {
        config_pair[0]: config_pair[1]
        for config_pair in agent_config.private_key_paths.read_all()
    }
    wallet = Wallet(private_key_paths)
    return wallet


def update_item_public_id_in_init(
    item_type: str, package_path: Path, item_id: PublicId
) -> None:
    """
    Update item config and item config file.

    :param item_type: type of item.
    :param package_path: path to a package folder.
    :param item_id: public_id

    :return: None
    """
    if item_type != SKILL:
        return
    init_filepath = os.path.join(package_path, "__init__.py")
    with open(init_filepath, "r") as f:
        file_content = f.readlines()
    with open(init_filepath, "w") as f:
        for line in file_content:
            if PACKAGE_PUBLIC_ID_VAR_NAME in line:
                f.write(
                    f'{PACKAGE_PUBLIC_ID_VAR_NAME} = PublicId.from_str("{str(item_id)}")'
                )
            else:
                f.write(line)


def update_references(ctx: Context, replacements: Dict[ComponentId, ComponentId]):
    """
    Update references across an AEA project.

    Caveat: the update is done in a sequential manner. There is no check
    of multiple updates, due to the occurrence of transitive relations.
    E.g. replacements as {c1: c2, c2: c3} might lead to c1 replaced with c3
      instead of c2.

    :param ctx: the context.
    :param replacements: mapping from old component ids to new component ids.
    :return: None.
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

    :return: None
    """
    vendor_path_str = get_package_path(ctx, item_type, public_id, is_vendor=True)
    local_path = get_package_path(ctx, item_type, public_id, is_vendor=False)
    vendor_path = Path(vendor_path_str)
    if not os.path.exists(vendor_path.parent):
        os.makedirs(vendor_path.parent)
    create_symlink(vendor_path, Path(local_path), Path(ctx.cwd))


def create_symlink_packages_to_vendor(ctx: Context) -> None:
    """
    Creates a symlink from a local packages to the vendor folder.

    :param ctx: click context

    :return: None
    """
    if not os.path.exists(PACKAGES):
        create_symlink(Path(PACKAGES), Path(VENDOR), Path(ctx.cwd))


def replace_all_import_statements(
    aea_project_path: Path,
    item_type: ComponentType,
    old_public_id: PublicId,
    new_public_id: PublicId,
):
    """
    Replace all import statements in Python modules of all the non-vendor packages.

    The function looks for two patterns:
    - from packages.<author>.<item_type_plural>.<name>
    - import packages.<author>.<item_type_plural>.<name>

    :param aea_project_path: path to the AEA project.
    :param item_type: the item type.
    :param old_public_id: the old public id.
    :param new_public_id: the new public id.
    :return: None
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
    :return: None
    """
    aea_project_path = Path(ctx.cwd)
    for package_path in get_non_vendor_package_path(aea_project_path):
        item_type = package_path.parent.name[:-1]
        config = load_item_config(item_type, package_path)
        fingerprint_item(ctx, item_type, config.public_id)
