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
"""Implementation of the 'aea launch' subcommand."""
import sys
from collections import OrderedDict
from pathlib import Path
from typing import List, cast

import click

from aea.cli.utils.click_utils import AgentDirectory
from aea.cli.utils.context import Context
from aea.cli.utils.loggers import logger
from aea.helpers.multiple_executor import ExecutorExceptionPolicies
from aea.launcher import AEALauncher


@click.command()
@click.argument("agents", nargs=-1, type=AgentDirectory())
@click.option("--multithreaded", is_flag=True)
@click.pass_context
def launch(click_context, agents: List[str], multithreaded: bool):
    """Launch many agents at the same time."""
    _launch_agents(click_context, agents, multithreaded)


def _launch_agents(
    click_context: click.core.Context, agents: List[str], multithreaded: bool
) -> None:
    """
    Run multiple agents.

    :param click_context: click context object.
    :param agents: agents names.
    :param multithreaded: bool flag to run as multithreads.

    :return: None.
    """
    agents_directories = list(map(Path, list(OrderedDict.fromkeys(agents))))
    mode = "threaded" if multithreaded else "multiprocess"
    ctx = cast(Context, click_context.obj)

    launcher = AEALauncher(
        agent_dirs=agents_directories,
        mode=mode,
        fail_policy=ExecutorExceptionPolicies.log_only,
        log_level=ctx.verbosity,
    )

    try:
        """
        run in threaded mode and wait for thread finished cause issue with python 3.6/3.7 on windows
        probably keyboard interrupt exception gets lost in executor pool or in asyncio module
        """
        launcher.start(threaded=True)
        launcher.join_thread()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected.")
    finally:
        launcher.stop()

    for agent in launcher.failed:
        logger.info(f"Agent {agent} terminated with exit code 1")

    for agent in launcher.not_failed:
        logger.info(f"Agent {agent} terminated with exit code 0")

    logger.debug(f"Exit cli. code: {launcher.num_failed}")
    sys.exit(1 if launcher.num_failed > 0 else 0)
