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

import click

from aea.cli.common import Context, logger, try_to_load_agent_config
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


@clean_tarfiles
def publish_agent(ctx: Context):
    """Publish an agent."""
    try_to_load_agent_config(ctx)
    check_is_author_logged_in(ctx.agent_config.author)

    name = ctx.agent_config.agent_name
    agent_config_path = os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE)
    output_tar = os.path.join(ctx.cwd, "{}.tar.gz".format(name))
    _compress(output_tar, agent_config_path)

    data = {
        "name": name,
        "description": ctx.agent_config.description,
        "version": ctx.agent_config.version,
        "connections": ctx.agent_config.connections,
        "protocols": ctx.agent_config.protocols,
        "skills": ctx.agent_config.skills,
    }

    path = "/agents/create"
    logger.debug("Publishing agent {} to Registry ...".format(name))
    resp = request_api("POST", path, data=data, is_auth=True, filepath=output_tar)
    click.echo(
        "Successfully published agent {} to the Registry. Public ID: {}".format(
            name, resp["public_id"]
        )
    )
