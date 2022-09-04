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
"""Implementation of the 'aea sync-local-registry' subcommand."""
import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator, Tuple, Union, cast

import click

from aea.cli.registry.add import fetch_package
from aea.cli.registry.utils import get_package_meta
from aea.cli.utils.click_utils import determine_package_type_for_directory
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import pass_ctx
from aea.cli.utils.loggers import logger
from aea.configurations.data_types import PackageId, PackageType, PublicId
from aea.configurations.loader import load_package_configuration


PACKAGES_DIRS = [i.to_plural() for i in PackageType]


@click.command()
@pass_ctx
def local_registry_sync(ctx: Context) -> None:
    """Upgrade the local package registry."""
    skip_consistency_check = ctx.config["skip_consistency_check"]
    do_local_registry_update(ctx.cwd, skip_consistency_check)


def do_local_registry_update(
    base_dir: Union[str, Path], skip_consistency_check: bool = True
) -> None:
    """
    Perform local registry update.

    :param base_dir: root directory of the local registry.
    :param skip_consistency_check: whether or not to skip consistency checks.
    """
    for package_id, package_dir in enlist_packages(base_dir, skip_consistency_check):
        current_public_id = package_id.public_id
        latest_public_id = get_package_latest_public_id(package_id)
        if not (  # pylint: disable=superfluous-parens
            current_public_id < latest_public_id
        ):
            click.echo(f"{package_id} is the latest version.")
            continue
        click.echo(f"Updating {current_public_id} to {latest_public_id}.")
        replace_package(str(package_id.package_type), latest_public_id, package_dir)


def replace_package(
    package_type: str, public_id: PublicId, package_dir: Union[Path, str]
) -> None:
    """
    Download, extract and replace exists package.

    :param package_type: str.
    :param public_id: package public id to download
    :param: package_dir: target package dir
    """
    with TemporaryDirectory() as tmp_dir:
        new_package_dir = os.path.join(tmp_dir, public_id.name)
        os.mkdir(new_package_dir)
        fetch_package(
            package_type, public_id=public_id, cwd=tmp_dir, dest=new_package_dir
        )
        shutil.rmtree(package_dir)
        shutil.move(new_package_dir, package_dir)


def get_package_latest_public_id(package_id: PackageId) -> PublicId:
    """
    Get package latest package id from the remote repo.

    :param package_id: id of the package to check

    :return: package id of the latest package in remote repo
    """
    package_meta = get_package_meta(
        str(package_id.package_type), package_id.public_id.to_latest()
    )
    return PublicId.from_str(cast(str, package_meta["public_id"]))


def enlist_packages(
    base_dir: Union[Path, str], skip_consistency_check: bool = True
) -> Generator[Tuple[PackageId, Union[Path, str]], None, None]:
    """
    Generate list of the packages in local repo directory.

    :param base_dir: path or str of the local repo.
    :param skip_consistency_check: whether or not to skip consistency checks.

    :yield: a Tuple of package_id and package directory.
    """
    for author in os.listdir(base_dir):
        author_dir = os.path.join(base_dir, author)
        if not os.path.isdir(author_dir):
            continue  # pragma: nocover
        for package_type_plural in os.listdir(author_dir):
            if package_type_plural not in PACKAGES_DIRS:
                continue  # pragma: nocover
            package_type_dir = os.path.join(author_dir, package_type_plural)
            if not os.path.isdir(package_type_dir):
                continue  # pragma: nocover
            for package_name in os.listdir(package_type_dir):
                package_dir = os.path.join(package_type_dir, package_name)
                if not os.path.isdir(package_dir):
                    continue  # pragma: nocover
                try:
                    package_type = determine_package_type_for_directory(
                        Path(package_dir)
                    )
                    if package_type.to_plural() != package_type_plural:
                        # incorrect package placing
                        continue  # pragma: nocover
                    config = load_package_configuration(
                        package_type,
                        Path(package_dir),
                        skip_consistency_check=skip_consistency_check,
                    )
                    yield (config.package_id, package_dir)
                except ValueError as e:  # pragma: nocover
                    logger.error(  # pragma: nocover
                        f"Error with package_dir={package_dir}: {e}"
                    )
