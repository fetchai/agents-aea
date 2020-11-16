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

"""Implementation of the 'aea scaffold' subcommand."""

import os
import re
import shutil
from pathlib import Path
from typing import cast

import click
from jsonschema import ValidationError

from aea import AEA_DIR
from aea.cli.fingerprint import fingerprint_item
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after, pass_ctx
from aea.cli.utils.loggers import logger
from aea.cli.utils.package_utils import (
    create_symlink_packages_to_vendor,
    create_symlink_vendor_to_local,
    validate_package_name,
)
from aea.configurations.base import PublicId
from aea.configurations.constants import (  # noqa: F401  # pylint: disable=unused-import
    CONNECTION,
    CONTRACT,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_CONTRACT_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
    DEFAULT_VERSION,
    PROTOCOL,
    SCAFFOLD_PUBLIC_ID,
    SKILL,
)


@click.group()
@click.option(
    "--with-symlinks",
    is_flag=True,
    help="Add symlinks from vendor to non-vendor and packages to vendor folders.",
)
@click.pass_context
@check_aea_project
def scaffold(
    click_context: click.core.Context, with_symlinks: bool
):  # pylint: disable=unused-argument
    """Scaffold a resource for the agent."""
    ctx = cast(Context, click_context.obj)
    ctx.set_config("with_symlinks", with_symlinks)


@scaffold.command()
@click.argument("connection_name", type=str, required=True)
@pass_ctx
def connection(ctx: Context, connection_name: str) -> None:
    """Add a connection scaffolding to the configuration file and agent."""
    scaffold_item(ctx, CONNECTION, connection_name)


@scaffold.command()
@click.argument("contract_name", type=str, required=True)
@pass_ctx
def contract(ctx: Context, contract_name: str) -> None:
    """Add a contract scaffolding to the configuration file and agent."""
    scaffold_item(ctx, CONTRACT, contract_name)


@scaffold.command()
@click.argument("protocol_name", type=str, required=True)
@pass_ctx
def protocol(ctx: Context, protocol_name: str):
    """Add a protocol scaffolding to the configuration file and agent."""
    scaffold_item(ctx, PROTOCOL, protocol_name)


@scaffold.command()
@click.argument("skill_name", type=str, required=True)
@pass_ctx
def skill(ctx: Context, skill_name: str):
    """Add a skill scaffolding to the configuration file and agent."""
    scaffold_item(ctx, SKILL, skill_name)


@scaffold.command()
@pass_ctx
def decision_maker_handler(ctx: Context):
    """Add a decision maker scaffolding to the configuration file and agent."""
    _scaffold_dm_handler(ctx)


@clean_after
def scaffold_item(ctx: Context, item_type: str, item_name: str) -> None:
    """
    Add an item scaffolding to the configuration file and agent.

    :param ctx: Context object.
    :param item_type: type of item.
    :param item_name: item name.

    :return: None
    :raises ClickException: if some error occures.
    """
    validate_package_name(item_name)
    author_name = ctx.agent_config.author
    loader = getattr(ctx, f"{item_type}_loader")
    default_config_filename = globals()[f"DEFAULT_{item_type.upper()}_CONFIG_FILE"]

    item_type_plural = item_type + "s"
    existing_ids = getattr(ctx.agent_config, f"{item_type}s")
    existing_ids_only_author_and_name = map(lambda x: (x.author, x.name), existing_ids)
    # check if we already have an item with the same public id
    if (author_name, item_name) in existing_ids_only_author_and_name:
        raise click.ClickException(
            f"A {item_type} with name '{item_name}' already exists. Aborting..."
        )

    agent_name = ctx.agent_config.agent_name
    click.echo(
        f"Adding {item_type} scaffold '{item_name}' to the agent '{agent_name}'..."
    )

    # create the item folder
    Path(item_type_plural).mkdir(exist_ok=True)
    dest = os.path.join(item_type_plural, item_name)
    if os.path.exists(dest):
        raise click.ClickException(
            f"A {item_type} with this name already exists. Please choose a different name and try again."
        )

    ctx.clean_paths.append(str(dest))
    try:
        # copy the item package into the agent project.
        src = Path(os.path.join(AEA_DIR, item_type_plural, "scaffold"))
        logger.debug(f"Copying {item_type} modules. src={src} dst={dest}")
        shutil.copytree(src, dest)

        # add the item to the configurations.
        logger.debug(f"Registering the {item_type} into {DEFAULT_AEA_CONFIG_FILE}")
        new_public_id = PublicId(author_name, item_name, DEFAULT_VERSION)
        existing_ids.add(new_public_id)
        with open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w") as fp:
            ctx.agent_loader.dump(ctx.agent_config, fp)

        # ensure the name in the yaml and the name of the folder are the same
        config_filepath = Path(
            ctx.cwd, item_type_plural, item_name, default_config_filename
        )
        with config_filepath.open() as fp:
            config = loader.load(fp)
        config.name = item_name
        config.author = author_name
        with config_filepath.open("w") as fp:
            loader.dump(config, fp)

        # update 'PUBLIC_ID' variable with the right public id
        init_module = Path(dest, "__init__.py")
        init_module.write_text(
            re.sub(SCAFFOLD_PUBLIC_ID, str(new_public_id), init_module.read_text())
        )

        # fingerprint item.
        fingerprint_item(ctx, item_type, new_public_id)

        if ctx.config.get("with_symlinks", False):
            click.echo(
                "Adding symlinks from vendor to non-vendor and packages to vendor folders."
            )
            create_symlink_vendor_to_local(ctx, item_type, new_public_id)
            create_symlink_packages_to_vendor(ctx)

    except ValidationError:
        raise click.ClickException(
            f"Error when validating the {item_type} configuration file."
        )
    except Exception as e:
        raise click.ClickException(str(e))


def _scaffold_dm_handler(ctx: Context):
    """Add a scaffolded decision maker handler to the project and configuration."""
    existing_dm_handler = ctx.agent_config.decision_maker_handler

    # check if we already have a decision maker in the project
    if existing_dm_handler != {}:
        raise click.ClickException(
            "A decision maker handler specification already exists. Aborting..."
        )

    dest = Path("decision_maker.py")
    agent_name = ctx.agent_config.agent_name
    click.echo("Adding decision maker scaffold to the agent '{}'...".format(agent_name))

    # create the file name
    dotted_path = ".decision_maker::DecisionMakerHandler"
    try:
        # copy the item package into the agent project.
        src = Path(os.path.join(AEA_DIR, "decision_maker", "scaffold.py"))
        logger.debug("Copying decision maker. src={} dst={}".format(src, dest))
        shutil.copyfile(src, dest)

        # add the item to the configurations.
        logger.debug(
            "Registering the decision_maker into {}".format(DEFAULT_AEA_CONFIG_FILE)
        )
        ctx.agent_config.decision_maker_handler = {
            "dotted_path": str(dotted_path),
            "file_path": str(os.path.join(".", dest)),
        }
        ctx.agent_loader.dump(
            ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w")
        )

    except Exception as e:
        os.remove(dest)
        raise click.ClickException(str(e))
