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
"""Methods for CLI push functionality."""

import os
import shutil
import tarfile
from typing import List, Tuple, cast

import click

from aea.cli.registry.utils import (
    check_is_author_logged_in,
    clean_tarfiles,
    list_missing_packages,
    request_api,
)
from aea.cli.utils.context import Context
from aea.cli.utils.generic import is_readme_present, load_yaml
from aea.cli.utils.loggers import logger
from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.configurations.constants import (
    CONNECTIONS,
    CONTRACTS,
    DEFAULT_README_FILE,
    ITEM_TYPE_PLURAL_TO_TYPE,
    PROTOCOLS,
    SKILLS,
)


def _remove_pycache(source_dir: str) -> None:
    pycache_path = os.path.join(source_dir, "__pycache__")
    if os.path.exists(pycache_path):
        shutil.rmtree(pycache_path)


def _compress_dir(output_filename: str, source_dir: str) -> None:
    _remove_pycache(source_dir)
    with tarfile.open(output_filename, "w:gz") as f:
        f.add(source_dir, arcname=os.path.basename(source_dir))


def load_component_public_id(source_path: str, item_type: str) -> PublicId:
    """Get component version from source path."""
    config = load_yaml(os.path.join(source_path, item_type + ".yaml"))
    item_author = config.get("author", "")
    item_name = config.get("name", "")
    item_version = config.get("version", "")
    return PublicId(item_author, item_name, item_version)


def check_package_public_id(
    source_path: str, item_type: str, item_id: PublicId
) -> PublicId:
    """
    Check component version is corresponds to specified version.

    :param source_path: the source path
    :param item_type: str type of item (connection/protocol/skill).
    :param item_id: item public id.
    :return: actual package public id
    """
    # we load only based on item_name, hence also check item_version and item_author match.

    actual_item_id = load_component_public_id(source_path, item_type)
    if not actual_item_id.same_prefix(item_id) or (
        not item_id.package_version.is_latest
        and item_id.version != actual_item_id.version
    ):
        raise click.ClickException(
            "Version, name or author does not match. Expected '{}', found '{}'".format(
                item_id,
                actual_item_id.author
                + "/"
                + actual_item_id.name
                + ":"
                + actual_item_id.version,
            )
        )
    return actual_item_id


@clean_tarfiles
def push_item(ctx: Context, item_type: str, item_id: PublicId) -> None:
    """
    Push item to the Registry.

    :param ctx: click context
    :param item_type: str type of item (connection/protocol/skill).
    :param item_id: item public id.
    """
    item_type_plural = item_type + "s"

    items_folder = os.path.join(ctx.cwd, item_type_plural)
    item_path = os.path.join(items_folder, item_id.name)

    if not os.path.exists(item_path):
        raise click.ClickException(
            '{} "{}" not found  in {}. Make sure you run push command '
            "from a correct folder.".format(
                item_type.title(), item_id.name, items_folder
            )
        )

    check_package_public_id(item_path, item_type, item_id)

    item_config_filepath = os.path.join(item_path, "{}.yaml".format(item_type))
    logger.debug("Reading {} {} config ...".format(item_id.name, item_type))
    item_config = load_yaml(item_config_filepath)
    check_is_author_logged_in(item_config["author"])

    logger.debug(
        "Searching for {} {} in {} ...".format(item_id.name, item_type, items_folder)
    )

    output_filename = "{}.tar.gz".format(item_id.name)
    logger.debug(
        "Compressing {} {} to {} ...".format(item_id.name, item_type, output_filename)
    )
    _compress_dir(output_filename, item_path)
    output_filepath = os.path.join(ctx.cwd, output_filename)

    data = {
        "name": item_id.name,
        "description": item_config["description"],
        "version": item_config["version"],
    }

    # dependencies
    dependencies: List[Tuple[str, PublicId]] = []
    for key in [CONNECTIONS, CONTRACTS, PROTOCOLS, SKILLS]:
        deps_list = item_config.get(key, [])
        if deps_list:
            data.update({key: deps_list})
        for dep in deps_list:
            dependencies.append((ITEM_TYPE_PLURAL_TO_TYPE[key], PublicId.from_str(dep)))

    missing_dependencies = list_missing_packages(dependencies)

    if missing_dependencies:
        for package_type, package_id in missing_dependencies:
            click.echo(f"Error: Cannot find {package_type} {package_id} in registry!")
        raise click.ClickException("Found missing dependencies! Push canceled!")
    try:
        files = {"file": open(output_filepath, "rb")}
        readme_path = os.path.join(item_path, DEFAULT_README_FILE)
        if is_readme_present(readme_path):
            files["readme"] = open(readme_path, "rb")

        path = "/{}/create".format(item_type_plural)
        logger.debug("Pushing {} {} to Registry ...".format(item_id.name, item_type))
        resp = cast(
            JSONLike, request_api("POST", path, data=data, is_auth=True, files=files)
        )
        click.echo(
            "Successfully pushed {} {} to the Registry. Public ID: {}".format(
                item_type, item_id.name, resp["public_id"]
            )
        )
    finally:
        for fd in files.values():
            fd.close()
