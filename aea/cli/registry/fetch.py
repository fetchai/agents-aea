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
"""Methods for CLI fetch functionality."""
import os
import shutil
from typing import Optional

import click

from aea.cli.add import add_item
from aea.cli.registry.utils import download_file, extract, request_api
from aea.cli.utils.config import try_to_load_agent_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import clean_after
from aea.configurations.base import PublicId
from aea.configurations.constants import (
    CONNECTION,
    CONTRACT,
    DEFAULT_AEA_CONFIG_FILE,
    PROTOCOL,
    SKILL,
)


@clean_after
def fetch_agent(
    ctx: Context,
    public_id: PublicId,
    alias: Optional[str] = None,
    target_dir: Optional[str] = None,
) -> None:
    """
    Fetch Agent from Registry.

    :param ctx: Context
    :param public_id: str public ID of desirable agent.
    :param alias: an optional alias.
    :param target_dir: the target directory to which the agent is fetched.
    :return: None
    """
    author, name, version = public_id.author, public_id.name, public_id.version
    api_path = f"/agents/{author}/{name}/{version}"
    resp = request_api("GET", api_path)
    file_url = resp["file"]

    filepath = download_file(file_url, ctx.cwd)

    folder_name = target_dir or (name if alias is None else alias)
    aea_folder = os.path.join(ctx.cwd, folder_name)
    ctx.clean_paths.append(aea_folder)

    extract(filepath, ctx.cwd)

    if alias or target_dir:
        shutil.move(
            os.path.join(ctx.cwd, name), aea_folder,
        )

    ctx.cwd = aea_folder
    try_to_load_agent_config(ctx)

    if alias is not None:
        ctx.agent_config.agent_name = alias
        ctx.agent_loader.dump(
            ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w")
        )

    click.echo("Fetching dependencies...")
    for item_type in (CONNECTION, CONTRACT, SKILL, PROTOCOL):
        item_type_plural = item_type + "s"

        # initialize fetched agent with empty folders for custom packages
        custom_items_folder = os.path.join(ctx.cwd, item_type_plural)
        os.makedirs(custom_items_folder)

        config = getattr(ctx.agent_config, item_type_plural)
        for item_public_id in config:
            try:
                add_item(ctx, item_type, item_public_id)
            except Exception as e:
                raise click.ClickException(
                    f'Unable to fetch dependency for agent "{name}", aborting. {e}'
                )
    click.echo("Dependencies successfully fetched.")
    click.echo(f"Agent {name} successfully fetched to {aea_folder}.")
