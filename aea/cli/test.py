# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Implementation of the 'aea test' command."""
import sys
from pathlib import Path
from typing import Sequence, cast

import click
import pytest

from aea.cli.utils.click_utils import (
    PublicIdParameter,
    determine_package_type_for_directory,
)
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, pass_ctx, pytest_args
from aea.cli.utils.package_utils import get_package_path
from aea.configurations.constants import CONNECTION, CONTRACT, PROTOCOL, SKILL
from aea.configurations.data_types import PublicId
from aea.exceptions import enforce
from aea.helpers.base import cd


@click.group(invoke_without_command=True)
@click.pass_context
@check_aea_project
@pytest_args
def test(click_context: click.Context, args: Sequence[str]) -> None:
    """Run tests of an AEA project."""
    click.echo("Executing tests of the AEA project...")
    ctx = cast(Context, click_context.obj)
    if click_context.invoked_subcommand is None:
        test_package_by_path(Path(ctx.cwd), args)


@test.command()
@click.argument("connection_public_id", type=PublicIdParameter(), required=True)
@pytest_args
@pass_ctx
def connection(
    ctx: Context, connection_public_id: PublicId, args: Sequence[str]
) -> None:
    """Executes a test suite of a connection package dependency."""
    test_item(ctx, CONNECTION, connection_public_id, args)


@test.command()
@click.argument("contract_public_id", type=PublicIdParameter(), required=True)
@pytest_args
@pass_ctx
def contract(ctx: Context, contract_public_id: PublicId, args: Sequence[str]) -> None:
    """Executes a test suite of a contract package dependency."""
    test_item(ctx, CONTRACT, contract_public_id, args)


@test.command()
@click.argument("protocol_public_id", type=PublicIdParameter(), required=True)
@pytest_args
@pass_ctx
def protocol(ctx: Context, protocol_public_id: PublicId, args: Sequence[str]) -> None:
    """Executes a test suite of a protocol package dependency."""
    test_item(ctx, PROTOCOL, protocol_public_id, args)


@test.command()
@click.argument("skill_public_id", type=PublicIdParameter(), required=True)
@pytest_args
@pass_ctx
def skill(ctx: Context, skill_public_id: PublicId, args: Sequence[str]) -> None:
    """Executes a test suite of a skill package dependency."""
    test_item(ctx, SKILL, skill_public_id, args)


@test.command()
@click.argument(
    "path", type=click.Path(exists=True, file_okay=False, dir_okay=True), required=True
)
@pytest_args
@pass_ctx
def by_path(
    ctx: Context,
    path: str,
    args: Sequence[str],
) -> None:
    """Executes a test suite of a package specified by a path."""
    click.echo(f"Executing tests of package at {path}'...")
    full_path = Path(ctx.cwd) / Path(path)
    test_package_by_path(full_path, args)


def test_item(
    ctx: Context,
    item_type: str,
    item_public_id: PublicId,
    pytest_arguments: Sequence[str],
) -> None:
    """
    Run tests of a package dependency.

    :param ctx: the context.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :param pytest_arguments: arguments to forward to Pytest
    """
    click.echo(
        "Executing tests of component of type {}, {}' ...".format(
            item_type, item_public_id
        )
    )
    package_dirpath = Path(
        get_package_path(ctx.cwd, item_type, item_public_id, is_vendor=False)
    )
    if not package_dirpath.exists():
        # check if it is a vendor package
        package_dirpath = Path(
            get_package_path(ctx.cwd, item_type, item_public_id, is_vendor=True)
        )
        enforce(
            package_dirpath.exists(),
            exception_text=f"package {item_public_id} of type {item_type} not found",
            exception_class=click.ClickException,
        )
    test_package_by_path(package_dirpath, pytest_arguments)


def test_package_by_path(package_dir: Path, pytest_arguments: Sequence[str]) -> None:
    """
    Fingerprint package placed in package_dir.

    :param package_dir: directory of the package
    :param pytest_arguments: arguments to forward to Pytest
    """
    # check the path points to a valid AEA package
    determine_package_type_for_directory(package_dir)
    with cd(package_dir):
        exit_code = pytest.main(list(pytest_arguments))
        sys.exit(exit_code)
