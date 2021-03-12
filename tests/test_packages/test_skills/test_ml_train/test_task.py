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
"""This module contains the tests of the task class of the ml_train skill."""

import sys
from pathlib import Path
from typing import Tuple
from unittest.mock import patch

import numpy as np
import pytest

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.ml_train.tasks import MLTrainTask

from tests.conftest import ROOT_DIR


@pytest.mark.skipif(
    sys.version_info >= (3, 9),
    reason="These tests use tensorflow which, at the time of writing, does not yet support python version 3.9.",
)
class TestTask(BaseSkillTestCase):
    """Test Task of ml_train."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_train")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.batch_size = 32
        cls.train_data = cls.produce_data(cls.batch_size)
        cls.epochs_per_batch = 10
        cls.weights = None

        cls.task = MLTrainTask(
            train_data=cls.train_data,
            epochs_per_batch=cls.epochs_per_batch,
            weights=cls.weights,
        )
        cls.logger = cls.task.logger

    @staticmethod
    def produce_data(batch_size) -> Tuple:
        """Prodice the data."""
        import tensorflow as tf  # pylint: disable=import-outside-toplevel

        ((train_x, train_y), _) = tf.keras.datasets.fashion_mnist.load_data()

        idx = np.arange(train_x.shape[0])
        mask = np.zeros_like(idx, dtype=bool)

        selected = np.random.choice(idx, batch_size, replace=False)
        mask[selected] = True

        x_sample = train_x[mask]
        y_sample = train_y[mask]
        return x_sample, y_sample

    def test_setup(self):
        """Test the setup method of the MLTrainTask class."""
        # operation
        with patch.object(self.logger, "info") as mock_logger:
            self.task.setup()

        # after
        mock_logger.assert_any_call("ML Train task: setup method called.")

    def test_make_model_i(self):
        """Test the make_model method of the MLTrainTask class where weights is None."""
        # setup
        import tensorflow as tf  # pylint: disable=import-outside-toplevel

        # operation
        with patch("tensorflow.keras.Sequential.set_weights") as mock_set_weights:
            model = self.task.make_model()

        # after
        assert isinstance(model, tf.keras.Sequential)
        mock_set_weights.assert_not_called()

    def test_make_model_ii(self):
        """Test the make_model method of the MLTrainTask class where weights is NOT None."""
        # setup
        import tensorflow as tf  # pylint: disable=import-outside-toplevel

        # before
        self.task.weights = []

        # operation
        with patch("tensorflow.keras.Sequential.set_weights") as mock_set_weights:
            model = self.task.make_model()

        # after
        assert isinstance(model, tf.keras.Sequential)
        mock_set_weights.assert_any_call(self.task.weights)

    def test_execute(self):
        """Test the execute method of the MLTrainTask class."""
        # before
        mocked_new_weights = ["new_weights"]
        mocked_loss = "0.1"
        mocked_acc = "0.8"

        # operation
        with patch.object(self.logger, "info") as mock_logger:
            with patch("tensorflow.keras.Sequential.fit") as mock_fit:
                with patch(
                    "tensorflow.keras.Sequential.get_weights",
                    return_value=mocked_new_weights,
                ) as mock_get_weights:
                    with patch(
                        "tensorflow.keras.Sequential.evaluate",
                        return_value=(mocked_loss, mocked_acc),
                    ) as mock_evaluate:
                        actual_new_weights = self.task.execute()

        # after
        mock_fit.assert_called_with(
            self.task.train_x, self.task.train_y, epochs=self.task.epochs_per_batch
        )
        mock_get_weights.assert_called_once()
        mock_evaluate.assert_called_with(
            self.task.train_x, self.task.train_y, verbose=2
        )

        mock_logger.assert_any_call(
            f"Start training with {self.task.train_x.shape[0]} rows"
        )
        mock_logger.assert_any_call(f"Loss: {mocked_loss}, Acc: {mocked_acc}")

        assert actual_new_weights == mocked_new_weights

    def test_teardown(self):
        """Test the teardown method of the MLTrainTask class."""
        # operation
        with patch.object(self.logger, "info") as mock_logger:
            self.task.teardown()

        # after
        mock_logger.assert_any_call("ML Train task: teardown method called.")
