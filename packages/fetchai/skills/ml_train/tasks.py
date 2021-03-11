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
<<<<<<< HEAD

from typing import Any, List, Optional, Tuple
=======
from typing import Any, Tuple
>>>>>>> a19ac2041d38baee10bc84083828f89879de1025

import numpy as np

from aea.skills.tasks import Task


class MLTrainTask(Task):
    """ML train task."""

    def __init__(
        self,
        train_data: Tuple[np.ndarray, np.ndarray],
        epochs_per_batch: int = 10,
        weights: Optional[List[np.ndarray]] = None,
    ):
        """Initialize the task."""
        super().__init__()

        self.train_x, self.train_y = train_data
        self.epochs_per_batch = epochs_per_batch
        self.weights = weights

    def setup(self) -> None:
        """Set up the task."""
        self.logger.info("ML Train task: setup method called.")

    def make_model(self) -> Any:
        """Make model."""
        import tensorflow as tf  # pylint: disable=import-outside-toplevel

        model = tf.keras.Sequential(
            [
                tf.keras.layers.Flatten(input_shape=(28, 28)),
                tf.keras.layers.Dense(128, activation="relu"),
                tf.keras.layers.Dense(10, activation="softmax"),
            ]
        )
        model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )

        if self.weights is not None:
            model.set_weights(self.weights)

        return model

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the task."""
<<<<<<< HEAD
        self.logger.info(f"Start training with {self.train_x.shape[0]} rows")

        model = self.make_model()

        model.fit(self.train_x, self.train_y, epochs=self.epochs_per_batch)
        new_weights = model.get_weights()

        loss, acc = model.evaluate(self.train_x, self.train_y, verbose=2)
        self.logger.info("Loss: {}, Acc: {}".format(loss, acc))

        return new_weights
=======
        self.logger.info("Start training with {} rows".format(self.train_x.shape[0]))
        model = self._make_model()
        model.fit(self.train_x, self.train_y, epochs=self.epochs_per_batch)
        loss, acc = model.evaluate(self.train_x, self.train_y, verbose=2)
        self.logger.info("Loss: {}, Acc: {}".format(loss, acc))
        return loss, acc
>>>>>>> a19ac2041d38baee10bc84083828f89879de1025

    def teardown(self) -> None:
        """Teardown the task."""
        self.logger.info("ML Train task: teardown method called.")
