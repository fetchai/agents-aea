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

"""This module contains the tasks for the 'echo' skill."""

import logging
import time

from aea.skills.tasks import Task

logger = logging.getLogger("aea.echo_skill")


class EchoTask(Task):
    """Echo task."""

    def __init__(self, **kwargs):
        """Initialize the task."""
        super().__init__(**kwargs)
        logger.info("EchoTask.__init__: arguments: {}".format(kwargs))

    def setup(self) -> None:
        """Set up the task."""
        logger.info("Echo Task: setup method called.")

    def execute(self, *args, **kwargs) -> None:
        """Execute the task."""
        logger.info("Echo Task: execute method called.")
        time.sleep(1.0)

    def teardown(self) -> None:
        """Teardown the task."""
        logger.info("Echo Task: teardown method called.")
