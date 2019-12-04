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

"""This module contains the tasks for the 'ml_train' skill."""
import logging
import sys
from typing import TYPE_CHECKING, Tuple

import numpy as np
from tensorflow import keras
from aea.skills.base import Task

if TYPE_CHECKING or "pytest" in sys.modules:
    pass
else:
    pass

logger = logging.getLogger("aea.gym_skill")


class MLTrainTask(Task):
    """ML train task."""

    def __init__(self, train_data: Tuple[np.ndarray, np.ndarray], *args, **kwargs):
        """Initialize the task."""
        super().__init__(*args, **kwargs)
        self.train_x, self.train_y = train_data

        self.model = self.context.model.tf_model  # type: keras.Model
        self.epochs_per_batch = kwargs.pop("epochs_per_batch", 10)
        # TODO not sure it's relevant - MLTrainTask already trains over a single batch.
        self.batch_size = kwargs.pop("batch_size", 32)

    def setup(self) -> None:
        """Set up the task."""
        logger.info("ML Train task: setup method called.")

    def execute(self, *args, **kwargs) -> None:
        """Execute the task."""
        logger.info("Start training with {} rows".format(self.train_x.shape[0]))
        self.model.fit(self.train_x, self.train_y, epochs=self.epochs_per_batch)
        loss, acc = self.model.evaluate(self.train_x, self.train_y, verbose=2)
        logger.info("Loss: {}, Acc: {}".format(loss, acc))
        self.completed = True

    def teardown(self) -> None:
        """Teardown the task."""
        logger.info("ML Train task: teardown method called.")
