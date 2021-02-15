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
import shutil
import tarfile
import tempfile
from typing import cast

import click

from aea.cli.registry.utils import (
    check_is_author_logged_in,
    clean_tarfiles,
    request_api,
)
from aea.cli.utils.config import try_to_load_agent_config
from aea.cli.utils.context import Context
from aea.cli.utils.generic import is_readme_present
from aea.cli.utils.loggers import logger
from aea.common import JSONLike
from aea.configurations.constants import (
    CONNECTIONS,
    CONTRACTS,
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_README_FILE,
    PROTOCOLS,
    SKILLS,
)


def _compress(output_filename: str, *filepaths: str) -> None:
    """Compare the output file."""
    with tarfile.open(output_filename, "w:gz") as f:
        for filepath in filepaths:
            f.add(filepath, arcname=os.path.basename(filepath))


@clean_tarfiles
def publish_agent(ctx: Context) -> None:
    """Publish an agent."""
    try_to_load_agent_config(ctx)
    check_is_author_logged_in(ctx.agent_config.author)

    name = ctx.agent_config.agent_name
    config_file_source_path = os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE)
    readme_source_path = os.path.join(ctx.cwd, DEFAULT_README_FILE)
    output_tar = os.path.join(ctx.cwd, "{}.tar.gz".format(name))

    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = os.path.join(temp_dir, name)
        os.makedirs(package_dir)
        config_file_target_path = os.path.join(package_dir, DEFAULT_AEA_CONFIG_FILE)
        shutil.copy(config_file_source_path, config_file_target_path)
        if is_readme_present(readme_source_path):
            readme_file_target_path = os.path.join(package_dir, DEFAULT_README_FILE)
            shutil.copy(readme_source_path, readme_file_target_path)

        _compress(output_tar, package_dir)

    data = {
        "name": name,
        "description": ctx.agent_config.description,
        "version": ctx.agent_config.version,
        CONNECTIONS: ctx.agent_config.connections,
        CONTRACTS: ctx.agent_config.contracts,
        PROTOCOLS: ctx.agent_config.protocols,
        SKILLS: ctx.agent_config.skills,
    }

    files = {}
    try:
        files["file"] = open(output_tar, "rb")
        if is_readme_present(readme_source_path):
            files["readme"] = open(readme_source_path, "rb")
        path = "/agents/create"
        logger.debug("Publishing agent {} to Registry ...".format(name))
        resp = cast(
            JSONLike, request_api("POST", path, data=data, is_auth=True, files=files)
        )
    finally:
        for fd in files.values():
            fd.close()
    click.echo(
        "Successfully published agent {} to the Registry. Public ID: {}".format(
            name, resp["public_id"]
        )
    )
