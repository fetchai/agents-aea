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
"""Methods for CLI publish functionality."""

import os
import tarfile
from typing import Dict

import click

from aea.cli.common import Context, _load_yaml, logger, try_to_load_agent_config
from aea.cli.registry.utils import (
    check_is_author_logged_in,
    clean_tarfiles,
    request_api,
)
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE


def _compress(output_filename: str, *filepaths):
    """Compare the output file."""
    with tarfile.open(output_filename, "w:gz") as f:
        for filepath in filepaths:
            f.add(filepath, arcname=os.path.basename(filepath))


def _load_agent_config(agent_config_path: str) -> Dict:
    if not os.path.exists(agent_config_path):
        raise click.ClickException(
            "Agent config not found. Make sure you run push command "
            "from a correct folder."
        )
    return _load_yaml(agent_config_path)


@clean_tarfiles
def publish_agent(ctx: Context):
    """Publish an agent."""
    try_to_load_agent_config(ctx)
    ctx.agent_config.author
    agent_config_path = os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE)
    agent_config = _load_agent_config(agent_config_path)
    check_is_author_logged_in(agent_config["author"])

    name = agent_config["agent_name"]
    output_tar = os.path.join(ctx.cwd, "{}.tar.gz".format(name))
    _compress(output_tar, agent_config_path)

    data = {
        "name": name,
        "description": agent_config["description"],
        "version": agent_config["version"],
    }
    for key in ("connections", "protocols", "skills"):
        data[key] = agent_config[key]

    path = "/agents/create"
    logger.debug("Publishing agent {} to Registry ...".format(name))
    resp = request_api("POST", path, data=data, is_auth=True, filepath=output_tar)
    click.echo(
        "Successfully published agent {} to the Registry. Public ID: {}".format(
            name, resp["public_id"]
        )
    )
