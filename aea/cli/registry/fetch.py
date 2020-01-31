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

from aea.cli.common import Context
from aea.cli.registry.utils import download_file, extract, fetch_package, request_api
from aea.configurations.base import PublicId


def fetch_agent(ctx: Context, public_id: PublicId) -> None:
    """
    Fetch Agent from Registry.

    :param public_id: str public ID of desirable Agent.

    :return: None
    """
    author, name, version = public_id.author, public_id.name, public_id.version
    api_path = "/agents/{}/{}/{}".format(author, name, version)
    resp = request_api("GET", api_path)
    file_url = resp["file"]

    target_folder = os.path.join(ctx.cwd, name)
    os.makedirs(target_folder, exist_ok=True)

    click.echo("Fetching dependencies...")
    for item_type in ("connection", "skill", "protocol"):
        item_type_plural = item_type + "s"
        for item_public_id in resp[item_type_plural]:
            item_public_id = PublicId.from_str(item_public_id)
            try:
                fetch_package(item_type, item_public_id, target_folder)
            except Exception as e:
                rmtree(target_folder)
                raise click.ClickException(
                    'Unable to fetch dependency for agent "{}", aborting. {}'.format(
                        name, e
                    )
                )
    click.echo("Dependencies successfully fetched.")

    filepath = download_file(file_url, ctx.cwd)
    extract(filepath, target_folder)
    click.echo("Agent {} successfully fetched to {}.".format(name, target_folder))
