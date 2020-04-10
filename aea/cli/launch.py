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
import subprocess  # nosec
import sys
from collections import OrderedDict
from pathlib import Path
from subprocess import Popen  # nosec
from threading import Thread
from typing import List, cast

import click

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.cli.common import AgentDirectory, Context, logger
from aea.cli.run import run


def _run_agent(click_context, agent_directory: str):
    os.chdir(agent_directory)
    click_context.invoke(run)


def _launch_subprocesses(click_context: click.Context, agents: List[Path]):
    """
    Launch many agents using subprocesses.

    :param agents: the click context.
    :param agents: list of paths to agent projects.
    :return: None
    """
    ctx = cast(Context, click_context.obj)
    processes = []
    failed = 0
    for agent_directory in agents:
        process = Popen(  # nosec
            [sys.executable, "-m", "aea.cli", "-v", ctx.verbosity, "run"],
            cwd=str(agent_directory),
        )
        logger.info("Agent {} started...".format(agent_directory.name))
        processes.append(process)

    try:
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected.")
    finally:
        for agent_directory, process in zip(agents, processes):
            result = process.poll()
            if result is None:
                try:
                    process.wait()
                except (subprocess.TimeoutExpired, KeyboardInterrupt):
                    logger.info("Force shutdown {}...".format(agent_directory.name))
                    process.kill()

            logger.info(
                "Agent {} terminated with exit code {}".format(
                    agent_directory.name, process.returncode
                )
            )
            failed |= process.returncode if process.returncode is not None else -1

    sys.exit(failed)


def _launch_threads(click_context: click.Context, agents: List[Path]):
    """
    Launch many agents, multithreaded.

    :param agents: the click context.
    :param agents: list of paths to agent projects.
    :return: None
    """
    aeas = []  # type: List[AEA]
    for agent_directory in agents:
        aeas.append(AEABuilder.from_aea_project(agent_directory).build())

    threads = [Thread(target=agent.start) for agent in aeas]
    for t in threads:
        t.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected.")
    finally:
        for idx, agent in enumerate(aeas):
            if not agent.liveness.is_stopped:
                agent.stop()
                threads[idx].join()
            logger.info("Agent {} has been stopped.".format(agent.name))


@click.command()
@click.argument("agents", nargs=-1, type=AgentDirectory())
@click.option("--multithreaded", is_flag=True)
@click.pass_context
def launch(click_context, agents: List[str], multithreaded: bool):
    """Launch many agents at the same time."""
    agents_directories = list(map(Path, list(OrderedDict.fromkeys(agents))))
    if not multithreaded:
        _launch_subprocesses(click_context, agents_directories)
    else:
        _launch_threads(click_context, agents_directories)
