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

"""Implementation of the 'aea install' subcommand."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast, Optional

import click
from click import pass_context
from jsonschema import ValidationError

from aea import AEA_DIR
from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, DEFAULT_CONNECTION_CONFIG_FILE, DEFAULT_SKILL_CONFIG_FILE, DEFAULT_PROTOCOL_CONFIG_FILE


@click.command()
@click.option('-r', '--requirement', type=str, required=False, default=None,
              help="Install from the given requirements file.")
@pass_ctx
def install(ctx: Context, requirement: Optional[str]):
    """Get the dependencies."""
    _try_to_load_agent_config(ctx)

    if requirement:
        logger.debug("Installing the dependencies in '{}'...".format(requirement))
        dependencies = list(map(lambda x: x.strip(), open(requirement).readlines()))
    else:
        logger.debug("Installing all the dependencies...")
        dependencies = ctx.get_dependencies()

    for d in dependencies:
        logger.debug("Installing {}...".format(d))
        try:
            subp = subprocess.Popen([sys.executable, "-m", "pip", "install", d])
            subp.wait(30.0)
        except Exception:
            logger.error("An error occurred while installing {}. Stopping...".format(d))
            exit(-1)
