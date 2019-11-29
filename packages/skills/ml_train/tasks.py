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

"""This module contains the tasks for the 'ml_train_predict' skill."""
import logging
import sys
from typing import TYPE_CHECKING

from aea.skills.base import Task

if TYPE_CHECKING or "pytest" in sys.modules:
    pass
else:
    pass

logger = logging.getLogger("aea.gym_skill")


class MLTrainTask(Task):
    """ML train task."""

    def __init__(self, *args, **kwargs):
        """Initialize the task."""
        logger.info("MLTrainTask.__init__: arguments: {}".format(kwargs))
        super().__init__(*args, **kwargs)

    def setup(self) -> None:
        """Set up the task."""
        logger.info("ML Train task: setup method called.")

    def execute(self, *args, **kwargs) -> None:
        """Execute the task."""

    def teardown(self) -> None:
        """Teardown the task."""
        logger.info("Gym Task: teardown method called.")