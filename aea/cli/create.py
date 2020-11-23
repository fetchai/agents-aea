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
from pathlib import Path
from typing import Optional, cast

import click

import aea
from aea.cli.add import add_item
from aea.cli.init import do_init
from aea.cli.utils.config import get_or_create_cli_config
from aea.cli.utils.constants import AUTHOR_KEY
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import clean_after
from aea.cli.utils.loggers import logger
from aea.configurations.base import AgentConfig, PublicId
from aea.configurations.constants import (
    CONNECTION,
    CONNECTIONS,
    CONTRACTS,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION,
    DEFAULT_LEDGER,
    DEFAULT_LICENSE,
    DEFAULT_PROTOCOL,
    DEFAULT_REGISTRY_PATH,
    DEFAULT_SKILL,
    DEFAULT_VERSION,
    PROTOCOL,
    PROTOCOLS,
    SIGNING_PROTOCOL,
    SKILL,
    SKILLS,
    STATE_UPDATE_PROTOCOL,
    VENDOR,
)


@click.command()
@click.argument("agent_name", type=str, required=True)
@click.option(
    "--author",
    type=str,
    required=False,
    help="Add the author to run `init` before `create` execution.",
)
@click.option("--local", is_flag=True, help="For using local folder.")
@click.option("--empty", is_flag=True, help="Not adding default dependencies.")
@click.pass_context
def create(
    click_context: click.core.Context,
    agent_name: str,
    author: str,
    local: bool,
    empty: bool,
):
    """Create a new agent."""
    ctx = cast(Context, click_context.obj)
    create_aea(ctx, agent_name, local, author=author, empty=empty)


@clean_after
def create_aea(
    ctx: Context,
    agent_name: str,
    local: bool,
    author: Optional[str] = None,
    empty: bool = False,
) -> None:
    """
    Create AEA project.

    :param ctx: Context object.
    :param local: boolean flag for local folder usage.
    :param agent_name: agent name.
    :param author: optional author name (valid with local=True only).
    :param empty: optional boolean flag for skip adding default dependencies.

    :return: None
    :raises: ClickException if an error occured.
    """
    try:
        _check_is_parent_folders_are_aea_projects_recursively()
    except Exception:
        raise click.ClickException(
            "The current folder is already an AEA project. Please move to the parent folder."
        )

    if author is not None:
        if local:
            do_init(author, False, False, False)  # pragma: nocover
        else:
            raise click.ClickException(
                "Author is not set up. Please use 'aea init' to initialize."
            )

    config = get_or_create_cli_config()
    set_author = config.get(AUTHOR_KEY, None)
    if set_author is None:
        raise click.ClickException(
            "The AEA configurations are not initialized. Uses `aea init` before continuing or provide optional argument `--author`."
        )

    if Path(agent_name).exists():
        raise click.ClickException("Directory already exist. Aborting...")

    click.echo("Initializing AEA project '{}'".format(agent_name))
    click.echo("Creating project directory './{}'".format(agent_name))
    path = Path(agent_name)
    ctx.clean_paths.append(str(path))

    # we have already checked that the directory does not exist.
    path.mkdir(exist_ok=False)

    try:
        # set up packages directories.
        _setup_package_folder(Path(agent_name, PROTOCOLS))
        _setup_package_folder(Path(agent_name, CONTRACTS))
        _setup_package_folder(Path(agent_name, CONNECTIONS))
        _setup_package_folder(Path(agent_name, SKILLS))

        # set up a vendor directory
        Path(agent_name, VENDOR).mkdir(exist_ok=False)
        Path(agent_name, VENDOR, "__init__.py").touch(exist_ok=False)

        # create a config file inside it
        click.echo("Creating config file {}".format(DEFAULT_AEA_CONFIG_FILE))
        agent_config = _crete_agent_config(ctx, agent_name, set_author)

        # next commands must be done from the agent's directory -> overwrite ctx.cwd
        ctx.agent_config = agent_config
        ctx.cwd = agent_config.agent_name

        if not empty:
            click.echo("Adding default packages ...")
            if local:
                ctx.set_config("is_local", True)
            add_item(ctx, PROTOCOL, PublicId.from_str(DEFAULT_PROTOCOL))
            add_item(ctx, PROTOCOL, PublicId.from_str(SIGNING_PROTOCOL))
            add_item(ctx, PROTOCOL, PublicId.from_str(STATE_UPDATE_PROTOCOL))
            add_item(ctx, CONNECTION, PublicId.from_str(DEFAULT_CONNECTION))
            add_item(ctx, SKILL, PublicId.from_str(DEFAULT_SKILL))

    except Exception as e:
        raise click.ClickException(str(e))


def _crete_agent_config(ctx: Context, agent_name: str, set_author: str) -> AgentConfig:
    """
    Create agent config.

    :param ctx: context object.
    :param agent_name: agent name.
    :param set_author: author name to set.

    :return: AgentConfig object.
    """
    agent_config = AgentConfig(
        agent_name=agent_name,
        aea_version=aea.__version__,
        author=set_author,
        version=DEFAULT_VERSION,
        license_=DEFAULT_LICENSE,
        registry_path=os.path.join("..", DEFAULT_REGISTRY_PATH),
        description="",
        default_ledger=DEFAULT_LEDGER,
        default_connection=str(PublicId.from_str(DEFAULT_CONNECTION).to_any()),
    )

    with open(os.path.join(agent_name, DEFAULT_AEA_CONFIG_FILE), "w") as config_file:
        ctx.agent_loader.dump(agent_config, config_file)

    return agent_config


def _check_is_parent_folders_are_aea_projects_recursively() -> None:
    """Look for 'aea-config.yaml' in parent folders recursively up to the user home directory.

    :return: None
    :raise ValueError: if a parent folder has a file named 'aea-config.yaml'.
    """
    current = Path(".").resolve()
    root = Path("/").resolve()
    home = current.home()
    while current not in (home, root):
        files = set(map(lambda x: x.name, current.iterdir()))
        if DEFAULT_AEA_CONFIG_FILE in files:
            raise ValueError(
                "Folder {} has file named {}".format(current, DEFAULT_AEA_CONFIG_FILE)
            )
        current = current.parent.resolve()


def _setup_package_folder(path: Path):
    """Set a package folder up."""
    path.mkdir(exist_ok=False)
    init_module = path / "__init__.py"
    logger.debug("Creating {}".format(init_module))
    Path(init_module).touch(exist_ok=False)
