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
from multiprocessing.context import Process
from pathlib import Path
from typing import List

import click

from aea.cli.common import AgentDirectory, logger
from aea.cli.run import run


def _run_agent(click_context, agent_directory: str):
    os.chdir(agent_directory)
    click_context.invoke(run)


@click.command()
@click.argument("agents", nargs=-1, type=AgentDirectory())
@click.pass_context
def launch(click_context, agents: List[str]):
    """Launch many agents."""
    agents_directories = list(map(Path, list(OrderedDict.fromkeys(agents))))
    agent_processes = [
        Process(target=_run_agent, args=(click_context, agent_directory))
        for agent_directory in agents_directories
    ]

    failed = 0
    try:
        for agent_directory, agent_process in zip(agents_directories, agent_processes):
            agent_process.start()
            logger.info("Agent {} started...".format(agent_directory.name))
        for agent_process in agent_processes:
            agent_process.join()
            failed |= (
                agent_process.exitcode if agent_process.exitcode is not None else 1
            )
    except KeyboardInterrupt:
        # at this point, the keyboard interrupt has been propagated
        # to all the child process, hence we just need to 'join' the processes.
        for agent_directory, agent_process in zip(agents_directories, agent_processes):
            logger.info(
                "Waiting for agent {} to shut down...".format(agent_directory.name)
            )
            agent_process.join(5.0)
            if agent_process.is_alive():
                logger.info("Killing agent {}...".format(agent_directory.name))
                agent_process.kill()
                failed = 1
            else:
                logger.info(
                    "Agent {} terminated with exit code {}".format(
                        agent_directory.name, agent_process.exitcode
                    )
                )
                failed |= (
                    agent_process.exitcode if agent_process.exitcode is not None else 1
                )
    except Exception as e:
        logger.exception(e)
        sys.exit(1)

    sys.exit(1) if failed else sys.exit(0)
