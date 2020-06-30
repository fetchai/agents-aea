#!/usr/bin/env python3
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


"""Core definitions for the AEA command-line tool."""

import click

import aea
from aea.cli.add import add
from aea.cli.add_key import add_key
from aea.cli.config import config
from aea.cli.create import create
from aea.cli.delete import delete
from aea.cli.eject import eject
from aea.cli.fetch import fetch
from aea.cli.fingerprint import fingerprint
from aea.cli.freeze import freeze
from aea.cli.generate import generate
from aea.cli.generate_key import generate_key
from aea.cli.generate_wealth import generate_wealth
from aea.cli.get_address import get_address
from aea.cli.get_wealth import get_wealth
from aea.cli.init import init
from aea.cli.install import install
from aea.cli.interact import interact
from aea.cli.launch import launch
from aea.cli.list import list_command as _list
from aea.cli.login import login
from aea.cli.logout import logout
from aea.cli.publish import publish
from aea.cli.push import push
from aea.cli.register import register
from aea.cli.remove import remove
from aea.cli.run import run
from aea.cli.scaffold import scaffold
from aea.cli.search import search
from aea.cli.utils.config import get_or_create_cli_config
from aea.cli.utils.constants import AUTHOR_KEY
from aea.cli.utils.context import Context
from aea.cli.utils.loggers import logger, simple_verbosity_option
from aea.helpers.win32 import enable_ctrl_c_support


@click.group(name="aea")
@click.version_option(aea.__version__, prog_name="aea")
@simple_verbosity_option(logger, default="INFO")
@click.option(
    "--skip-consistency-check",
    "skip_consistency_check",
    is_flag=True,
    required=False,
    default=False,
    help="Skip consistency check.",
)
@click.pass_context
def cli(click_context, skip_consistency_check: bool) -> None:
    """Command-line tool for setting up an Autonomous Economic Agent."""
    verbosity_option = click_context.meta.pop("verbosity")
    click_context.obj = Context(cwd=".", verbosity=verbosity_option)
    click_context.obj.set_config("skip_consistency_check", skip_consistency_check)

    # enables CTRL+C support on windows!
    enable_ctrl_c_support()


@cli.command()
@click.option("-p", "--port", default=8080)
@click.option("--local", is_flag=True, help="For using local folder.")
@click.pass_context
def gui(click_context, port, local):  # pragma: no cover
    """Run the CLI GUI."""
    _init_gui()
    import aea.cli_gui  # pylint: disable=import-outside-toplevel,redefined-outer-name

    click.echo("Running the GUI.....(press Ctrl+C to exit)")
    aea.cli_gui.run(port)


def _init_gui() -> None:
    """
    Initialize GUI before start.

    :return: None
    :raisees: ClickException if author is not set up.
    """
    config = get_or_create_cli_config()
    author = config.get(AUTHOR_KEY, None)
    if author is None:
        raise click.ClickException(
            "Author is not set up. Please run 'aea init' and then restart."
        )


cli.add_command(_list)
cli.add_command(add_key)
cli.add_command(add)
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
cli.add_command(get_wealth)
cli.add_command(init)
cli.add_command(install)
cli.add_command(interact)
cli.add_command(launch)
cli.add_command(login)
cli.add_command(logout)
cli.add_command(publish)
cli.add_command(push)
cli.add_command(register)
cli.add_command(remove)
cli.add_command(run)
cli.add_command(scaffold)
cli.add_command(search)
