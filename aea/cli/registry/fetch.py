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
from shutil import rmtree

import click

from aea.cli.add import _add_item
from aea.cli.common import Context, try_to_load_agent_config
from aea.cli.registry.utils import download_file, extract, request_api
from aea.configurations.base import PublicId


def fetch_agent(ctx: Context, public_id: PublicId, click_context) -> None:
    """
    Fetch Agent from Registry.

    :param public_id: str public ID of desirable Agent.

    :return: None
    """
    author, name, version = public_id.author, public_id.name, public_id.version
    api_path = "/agents/{}/{}/{}".format(author, name, version)
    resp = request_api("GET", api_path)
    file_url = resp["file"]

    filepath = download_file(file_url, ctx.cwd)
    extract(filepath, ctx.cwd)

    target_folder = os.path.join(ctx.cwd, name)
    ctx.cwd = target_folder
    try_to_load_agent_config(ctx)

    click.echo("Fetching dependencies...")
    for item_type in ("connection", "contract", "skill", "protocol"):
        item_type_plural = item_type + "s"

        # initialize fetched agent with empty folders for custom packages
        custom_items_folder = os.path.join(ctx.cwd, item_type_plural)
        os.makedirs(custom_items_folder)

        config = getattr(ctx.agent_config, item_type_plural)
        for item_public_id in config:
            try:
                _add_item(click_context, item_type, item_public_id)
            except Exception as e:
                rmtree(target_folder)
                raise click.ClickException(
                    'Unable to fetch dependency for agent "{}", aborting. {}'.format(
                        name, e
                    )
                )
    click.echo("Dependencies successfully fetched.")
    click.echo("Agent {} successfully fetched to {}.".format(name, target_folder))
