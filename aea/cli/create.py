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

"""Implementation of the 'aea create' subcommand."""
import os
import shutil
import sys
from pathlib import Path
from typing import cast

import click

from jsonschema import ValidationError

import aea
from aea.cli.add import _add_item
from aea.cli.common import (
    AUTHOR,
    Context,
    DEFAULT_CONNECTION,
    DEFAULT_LEDGER,
    DEFAULT_LICENSE,
    DEFAULT_REGISTRY_PATH,
    DEFAULT_SKILL,
    DEFAULT_VERSION,
    _get_or_create_cli_config,
    logger,
)
from aea.cli.init import init
from aea.configurations.base import AgentConfig, DEFAULT_AEA_CONFIG_FILE


def _check_is_parent_folders_are_aea_projects_recursively() -> None:
    """Look for 'aea-config.yaml' in parent folders recursively up to the user home directory.

    :return: None
    :raise ValueError: if a parent folder has a file named 'aea-config.yaml'.
    """
    current = Path(".").resolve()
    root = Path("/")
    home = current.home()
    while current not in (home, root):
        files = set(map(lambda x: x.name, current.iterdir()))
        if DEFAULT_AEA_CONFIG_FILE in files:
            raise Exception(
                "Folder {} has file named {}".format(current, DEFAULT_AEA_CONFIG_FILE)
            )
        current = current.parent.resolve()


def _setup_package_folder(path: Path):
    """Set a package folder up."""
    path.mkdir(exist_ok=False)
    init_module = path / "__init__.py"
    logger.debug("Creating {}".format(init_module))
    Path(init_module).touch(exist_ok=False)


@click.command()
@click.argument("agent_name", type=str, required=True)
@click.option(
    "--author",
    type=str,
    required=False,
    help="Add the author to run `init` before `create` execution.",
)
@click.option("--local", is_flag=True, help="For creating from local data.")
@click.pass_context
def create(click_context, agent_name, author, local):
    """Create an agent."""
    try:
        _check_is_parent_folders_are_aea_projects_recursively()
    except Exception:
        logger.error(
            "The current folder is already an AEA project. Please move to the parent folder."
        )
        sys.exit(1)

    if author is not None:
        if local:
            click_context.invoke(init, author=author)
        else:
            raise click.ClickException(
                "Author is not set up. Please use 'aea init' to initialize."
            )

    config = _get_or_create_cli_config()
    set_author = config.get(AUTHOR, None)
    if set_author is None:
        click.echo(
            "The AEA configurations are not initialized. Uses `aea init` before continuing or provide optional argument `--author`."
        )
        sys.exit(1)

    ctx = cast(Context, click_context.obj)
    path = Path(agent_name)

    click.echo("Initializing AEA project '{}'".format(agent_name))
    click.echo("Creating project directory './{}'".format(agent_name))

    # create the agent's directory
    try:
        path.mkdir(exist_ok=False)

        # set up packages directories.
        _setup_package_folder(Path(agent_name, "protocols"))
        _setup_package_folder(Path(agent_name, "connections"))
        _setup_package_folder(Path(agent_name, "skills"))

        # set up a vendor directory
        Path(agent_name, "vendor").mkdir(exist_ok=False)
        Path(agent_name, "vendor", "__init__.py").touch(exist_ok=False)

        # create a config file inside it
        click.echo("Creating config file {}".format(DEFAULT_AEA_CONFIG_FILE))
        config_file = open(os.path.join(agent_name, DEFAULT_AEA_CONFIG_FILE), "w")
        agent_config = AgentConfig(
            agent_name=agent_name,
            aea_version=aea.__version__,
            author=set_author,
            version=DEFAULT_VERSION,
            license=DEFAULT_LICENSE,
            registry_path=os.path.join("..", DEFAULT_REGISTRY_PATH),
            description="",
        )
        agent_config.default_connection = DEFAULT_CONNECTION
        agent_config.default_ledger = DEFAULT_LEDGER
        ctx.agent_loader.dump(agent_config, config_file)

        # next commands must be done from the agent's directory -> overwrite ctx.cwd
        ctx.agent_config = agent_config
        ctx.cwd = agent_config.agent_name

        click.echo("Adding default packages ...")
        if local:
            ctx.set_config("is_local", True)
        _add_item(click_context, "connection", DEFAULT_CONNECTION)
        _add_item(click_context, "skill", DEFAULT_SKILL)

    except OSError:
        logger.error("Directory already exist. Aborting...")
        sys.exit(1)
    except ValidationError as e:
        logger.error(str(e))
        shutil.rmtree(agent_name, ignore_errors=True)
        sys.exit(1)
    except Exception as e:
        logger.exception(e)
        shutil.rmtree(agent_name, ignore_errors=True)
        sys.exit(1)
