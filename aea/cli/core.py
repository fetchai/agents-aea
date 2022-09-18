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
"""Core definitions for the AEA command-line tool."""
from typing import Optional

import click
from pkg_resources import iter_entry_points

import aea
from aea.cli.add import add
from aea.cli.add_key import add_key
from aea.cli.build import build
from aea.cli.check_packages import check_packages
from aea.cli.config import config
from aea.cli.create import create
from aea.cli.delete import delete
from aea.cli.eject import eject
from aea.cli.fetch import fetch
from aea.cli.fingerprint import fingerprint
from aea.cli.freeze import freeze
from aea.cli.generate import generate
from aea.cli.generate_all_protocols import generate_all_protocols
from aea.cli.generate_key import generate_key
from aea.cli.generate_wealth import generate_wealth
from aea.cli.get_address import get_address
from aea.cli.get_multiaddress import get_multiaddress
from aea.cli.get_public_key import get_public_key
from aea.cli.get_wealth import get_wealth
from aea.cli.init import init
from aea.cli.install import install
from aea.cli.ipfs_hash import hash_group
from aea.cli.issue_certificates import issue_certificates
from aea.cli.launch import launch
from aea.cli.list import list_command as _list
from aea.cli.local_registry_sync import local_registry_sync
from aea.cli.login import login
from aea.cli.logout import logout
from aea.cli.packages import package_manager
from aea.cli.plugin import with_plugins
from aea.cli.publish import publish
from aea.cli.push import push
from aea.cli.push_all import push_all
from aea.cli.register import register
from aea.cli.remove import remove
from aea.cli.remove_key import remove_key
from aea.cli.reset_password import reset_password
from aea.cli.run import run
from aea.cli.scaffold import scaffold
from aea.cli.search import search
from aea.cli.test import test
from aea.cli.transfer import transfer
from aea.cli.upgrade import upgrade
from aea.cli.utils.click_utils import registry_path_option
from aea.cli.utils.config import get_registry_path_from_cli_config
from aea.cli.utils.context import Context
from aea.cli.utils.loggers import logger, simple_verbosity_option
from aea.helpers.win32 import enable_ctrl_c_support


@with_plugins(iter_entry_points("aea.cli"))
@click.group(name="aea")  # type: ignore
@click.version_option(aea.__version__, prog_name="aea")
@simple_verbosity_option(logger, default="INFO")
@click.option(
    "-s",
    "--skip-consistency-check",
    "skip_consistency_check",
    is_flag=True,
    required=False,
    default=False,
    help="Skip consistency checks of agent during command execution.",
)
@registry_path_option
@click.pass_context
def cli(
    click_context: click.Context,
    skip_consistency_check: bool,
    registry_path: Optional[str],
) -> None:
    """Command-line tool for setting up an Autonomous Economic Agent (AEA)."""
    verbosity_option = click_context.meta.pop("verbosity")
    if not registry_path:
        registry_path = get_registry_path_from_cli_config()
    click_context.obj = Context(
        cwd=".", verbosity=verbosity_option, registry_path=registry_path
    )
    click_context.obj.set_config("skip_consistency_check", skip_consistency_check)

    # enables CTRL+C support on windows!
    enable_ctrl_c_support()


cli.add_command(_list)
cli.add_command(add_key)
cli.add_command(add)
cli.add_command(build)
cli.add_command(create)
cli.add_command(config)
cli.add_command(delete)
cli.add_command(eject)
cli.add_command(fetch)
cli.add_command(fingerprint)
cli.add_command(freeze)
cli.add_command(generate_key)
cli.add_command(generate_wealth)
cli.add_command(generate)
cli.add_command(get_address)
cli.add_command(get_public_key)
cli.add_command(get_multiaddress)
cli.add_command(get_wealth)
cli.add_command(init)
cli.add_command(install)
cli.add_command(issue_certificates)
cli.add_command(launch)
cli.add_command(login)
cli.add_command(logout)
cli.add_command(publish)
cli.add_command(push)
cli.add_command(register)
cli.add_command(remove)
cli.add_command(remove_key)
cli.add_command(reset_password)
cli.add_command(run)
cli.add_command(scaffold)
cli.add_command(search)
cli.add_command(local_registry_sync)
cli.add_command(test)
cli.add_command(transfer)
cli.add_command(upgrade)
cli.add_command(hash_group)
cli.add_command(generate_all_protocols)
cli.add_command(check_packages)
cli.add_command(push_all)
cli.add_command(package_manager)
