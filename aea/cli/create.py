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
from click import pass_context
from jsonschema import ValidationError

import aea
from aea.cli.add import connection, skill
from aea.cli.common import Context, logger, DEFAULT_REGISTRY_PATH, DEFAULT_CONNECTION, DEFAULT_SKILL, DEFAULT_LEDGER, DEFAULT_VERSION
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, AgentConfig


def _check_is_parent_folders_are_aea_projects_recursively() -> None:
    """Look for 'aea-config.yaml' in parent folders recursively up to the user home directory.

    :return: None
    :raise ValueError: if a parent folder has a file named 'aea-config.yaml'.
    """
    current = Path(".").resolve()
    root = Path("/")
    home = current.home()
    while current != home and current != root:
        files = set(map(lambda x: x.name, current.iterdir()))
        if DEFAULT_AEA_CONFIG_FILE in files:
            raise Exception("Folder {} has file named {}".format(current, DEFAULT_AEA_CONFIG_FILE))
        current = current.parent.resolve()
    return


def _setup_package_folder(ctx, item_type_plural):
    """Set a package folder up."""
    Path(ctx.cwd, item_type_plural).mkdir()
    connections_init_module = os.path.join(ctx.cwd, item_type_plural, "__init__.py")
    logger.debug("Creating {}".format(connections_init_module))
    Path(connections_init_module).touch(exist_ok=True)


@click.command()
@click.argument('agent_name', type=str, required=True)
@pass_context
def create(click_context, agent_name):
    """Create an agent."""
    try:
        _check_is_parent_folders_are_aea_projects_recursively()
    except Exception:
        logger.error("The current folder is already an AEA project. Please move to the parent folder.")
        sys.exit(1)

    ctx = cast(Context, click_context.obj)
    path = Path(agent_name)

    logger.info("Initializing AEA project '{}'".format(agent_name))
    logger.info("Creating project directory '/{}'".format(agent_name))

    # create the agent's directory
    try:
        path.mkdir(exist_ok=False)

        # create a config file inside it
        logger.info("Creating config file {}".format(DEFAULT_AEA_CONFIG_FILE))
        config_file = open(os.path.join(agent_name, DEFAULT_AEA_CONFIG_FILE), "w")
        agent_config = AgentConfig(agent_name=agent_name, aea_version=aea.__version__,
                                   author="", version=DEFAULT_VERSION, license="", fingerprint="",
                                   registry_path=os.path.join("..", DEFAULT_REGISTRY_PATH), description="")
        agent_config.default_connection = DEFAULT_CONNECTION
        agent_config.default_ledger = DEFAULT_LEDGER
        ctx.agent_loader.dump(agent_config, config_file)

        # next commands must be done from the agent's directory -> overwrite ctx.cwd
        ctx.agent_config = agent_config
        ctx.cwd = agent_config.agent_name

        _setup_package_folder(ctx, "protocols")
        _setup_package_folder(ctx, "connections")
        _setup_package_folder(ctx, "skills")

        logger.info("Adding default packages ...")
        click_context.invoke(connection, connection_public_id=DEFAULT_CONNECTION)

        click_context.invoke(skill, skill_public_id=DEFAULT_SKILL)

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
