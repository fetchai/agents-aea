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

import logging

from aea.skills.base import Task

logger = logging.getLogger("aea.my_search_skill")


class MySearchTask(Task):
    """This class scaffolds a task."""

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        logger.info("[{}]: setting up MySearchTask".format(self.context.agent_name))

    def execute(self) -> None:
        """
        Implement the task execution.

        :param envelope: the envelope
        :return: None
        """
        my_search_behaviour = self.context.behaviours[0]
        my_search_handler = self.context.handlers[0]
        logger.info("[{}]: number of search requests sent={} vs. number of search responses received={}".format(
            self.context.agent_name,
            my_search_behaviour.sent_search_count,
            my_search_handler.received_search_count)
        )

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        logger.info("[{}]: tearing down MySearchTask".format(self.context.agent_name))