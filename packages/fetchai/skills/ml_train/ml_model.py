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

"""This module contains the strategy class."""
import threading
from pathlib import Path
from queue import Queue
from typing import Any

from aea.skills.base import Model


DEFAULT_MODEL_CONFIG_PATH = str(Path("..", "..", "model.config").resolve())


class MLModel(Model):
    """This class defines a machine learning model."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the machine learning model."""
        self._model_config_path = kwargs.pop(
            "model_config_path", DEFAULT_MODEL_CONFIG_PATH
        )
        super().__init__(**kwargs)

        # this at the moment does not work - need to compile the model according to the network configuration
        #      A better alternative is to save/load in HDF5 format, but that might require some system level dependencies
        #      https://keras.io/getting-started/faq/#how-can-i-install-hdf5-or-h5py-to-save-my-models-in-keras
        # self._model = keras.Model.from_config(json.load(open(self._model_config_path))) # noqa: E800
        self._lock = threading.RLock()
        self._weights = None

        self.data_queue: Queue = Queue()

    def setup(self) -> None:
        """
        Setup the model.

        :return: None
        """

    def training_loop(self) -> None:
        """
        Start the training loop.

        :return: None
        """
        model = self.make_model()
        self.set_weights(model.get_weights())
        while True:
            data = self.data_queue.get()
            if data is None:
                break

            X, y, kwargs = data
            model.fit(X, y, **kwargs)
            loss, acc = model.evaluate(X, y, verbose=2)
            self.context.logger.info("Loss: {}, Acc: {}".format(loss, acc))
            self.set_weights(model.get_weights())

    @staticmethod
    def _make_raw_model() -> Any:
        """Make a raw model."""
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
        return model

    def _reconstruct_model_with_weights(self, weights) -> Any:
        """Reconstruct the model with input weights."""
        model = MLModel._make_raw_model()
        model.set_weights(weights)
        self.set_weights(weights)
        return model

    def make_model(self, weights) -> Any:
        if weights is None:
            model = self._make_raw_model()
        else:
            model = self._reconstruct_model_with_weights(weights)

        return model

    def get_weights(self) -> Any:
        """Get the weights, thread-safe."""
        with self._lock:
            return self._weights

    def set_weights(self, weights: Any) -> None:
        """Set the weights, thread-safe."""
        with self._lock:
            self._weights = weights

    def evaluate(self, *args: Any, **kwargs: Any) -> None:
        """Predict."""
        with self._lock:
            model = self.make_model()
            weights = self.get_weights()
            model.set_weights(weights)
            return model.evaluate(*args, **kwargs)

    def teardown(self) -> None:
        """
        Teardown the model.

        :return: None
        """
