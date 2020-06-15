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
import os
import sys
from collections import OrderedDict
from pathlib import Path
from typing import List

import click

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.cli.run import run
from aea.cli.utils.click_utils import AgentDirectory
from aea.cli.utils.loggers import logger
from aea.helpers.base import cd
from aea.helpers.multiple_executor import ExecutorExceptionPolicies
from aea.launcher import AEALauncher
from aea.runner import AEARunner


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
    if multithreaded:
        failed = _launch_threads(click_context, agents_directories)
    else:
        failed = _launch_subprocesses(click_context, agents_directories)
    logger.debug(f"Exit cli. code: {failed}")
    sys.exit(failed)


def _run_agent(click_context, agent_directory: str):
    os.chdir(agent_directory)
    click_context.invoke(run)


def _launch_subprocesses(click_context: click.Context, agents: List[Path]) -> int:
    """
    Launch many agents using subprocesses.

    :param agents: the click context.
    :param agents: list of paths to agent projects.
    :return: execution status
    """
    launcher = AEALauncher(
        agents, mode="multiprocess", fail_policy=ExecutorExceptionPolicies.log_only
    )

    try:
        launcher.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected.")
    finally:
        launcher.stop()

    for agent in launcher.failed:
        logger.info(f"Agent {agent} terminated with exit code 1")

    for agent in launcher.not_failed:
        logger.info(f"Agent {agent} terminated with exit code 0")

    return launcher.num_failed


def _launch_threads(click_context: click.Context, agents: List[Path]) -> int:
    """
    Launch many agents, multithreaded.

    :param agents: the click context.
    :param agents: list of paths to agent projects.
    :return: exit status
    """
    aeas = []  # type: List[AEA]
    for agent_directory in agents:
        with cd(agent_directory):
            aeas.append(AEABuilder.from_aea_project(".").build())

    runner = AEARunner(
        agents=aeas, mode="threaded", fail_policy=ExecutorExceptionPolicies.log_only
    )
    try:
        runner.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected.")
    finally:
        runner.stop()
    return runner.num_failed
