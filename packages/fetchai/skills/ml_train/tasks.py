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

from typing import Any, Optional, Tuple, cast

import numpy as np

from aea.skills.base import SkillContext
from aea.skills.tasks import Task

from packages.fetchai.skills.ml_train.ml_model import MLModel


class MLTrainTask(Task):
    """ML train task."""

    def __init__(
        self,
        skill_context: SkillContext,
        train_data: Tuple[np.ndarray, np.ndarray],
        epochs_per_batch: int = 10,
        weights: Optional[int] = None,
    ):
        """Initialize the task."""
        super().__init__(logger=skill_context.logger)

        self.train_x, self.train_y = train_data
        self.weights = weights
        self.epochs_per_batch = epochs_per_batch

        self.ml_model = cast(MLModel, skill_context.ml_model)

    def setup(self) -> None:
        """Set up the task."""
        self.logger.info("ML Train task: setup method called.")

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the task."""
        self.logger.info("Start training with {} rows".format(self.train_x.shape[0]))

        model = self.ml_model.make_model(self.weights)

        model.fit(self.train_x, self.train_y, epochs=self.epochs_per_batch)
        new_weights = model.get_weights()

        loss, acc = model.evaluate(self.train_x, self.train_y, verbose=2)
        self.logger.info("Loss: {}, Acc: {}".format(loss, acc))

        return new_weights

    def teardown(self) -> None:
        """Teardown the task."""
        self.logger.info("ML Train task: teardown method called.")
