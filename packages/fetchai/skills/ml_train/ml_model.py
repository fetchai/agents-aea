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

import tensorflow as tf

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
        model = self._make_model()
        self._set_weights(model.get_weights())
        while True:
            data = self.data_queue.get()
            if data is None:
                break

            X, y, kwargs = data
            model.fit(X, y, **kwargs)
            loss, acc = model.evaluate(X, y, verbose=2)
            self.context.logger.info("Loss: {}, Acc: {}".format(loss, acc))
            self._set_weights(model.get_weights())

    @staticmethod
    def _make_model() -> Any:
        """Make the model."""
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

    def _get_weights(self) -> Any:
        """Get the weights, thread-safe."""
        with self._lock:
            return self._weights

    def _set_weights(self, weights: Any) -> None:
        """Set the weights, thread-safe."""
        with self._lock:
            self._weights = weights

    def predict(self, *args: Any, **kwargs: Any) -> None:
        """Predict."""
        with self._lock:
            model = self._make_model()
            weights = self._get_weights()
            model.set_weights(weights)
            return model.predict(*args, **kwargs)

    def evaluate(self, *args: Any, **kwargs: Any) -> None:
        """Predict."""
        with self._lock:
            model = self._make_model()
            weights = self._get_weights()
            model.set_weights(weights)
            return model.evaluate(*args, **kwargs)

    def save(self) -> None:
        """Save the model weights."""
        raise NotImplementedError

    def update(self, X: Any, y: Any, epochs: int) -> None:
        """Update the ML model."""
        self.data_queue.put((X, y, dict(epochs=epochs)))

    def teardown(self) -> None:
        """
        Teardown the model.

        :return: None
        """
