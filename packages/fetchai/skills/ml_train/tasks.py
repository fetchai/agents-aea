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

from typing import Tuple

import numpy as np
from tensorflow import keras

from aea.skills.base import SkillContext
from aea.skills.tasks import Task


class MLTrainTask(Task):
    """ML train task."""

    def __init__(
        self,
        skill_context: SkillContext,
        train_data: Tuple[np.ndarray, np.ndarray],
        model: keras.Model,
        epochs_per_batch: int = 10,
        batch_size: int = 32,
    ):
        """Initialize the task."""
        super().__init__(logger=skill_context.logger)
        self.train_x, self.train_y = train_data

        self.model = model
        self.epochs_per_batch = epochs_per_batch
        self.batch_size = batch_size

    def setup(self) -> None:
        """Set up the task."""
        self.logger.info("ML Train task: setup method called.")

    def execute(self, *args, **kwargs) -> keras.Model:
        """Execute the task."""
        self.logger.info("Start training with {} rows".format(self.train_x.shape[0]))
        self.model.fit(self.train_x, self.train_y, epochs=self.epochs_per_batch)
        loss, acc = self.model.evaluate(self.train_x, self.train_y, verbose=2)
        self.logger.info("Loss: {}, Acc: {}".format(loss, acc))
        return self.model

    def teardown(self) -> None:
        """Teardown the task."""
        self.logger.info("ML Train task: teardown method called.")
