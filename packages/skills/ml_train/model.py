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
import json
import threading
from pathlib import Path

from tensorflow import keras

from aea.skills.base import SharedClass

DEFAULT_MODEL_CONFIG_PATH = str(Path("..", "..", "model.config").resolve())


class Model(SharedClass):
    """This class defines a machine learning model."""

    def __init__(self, **kwargs):
        """Initialize the machine learning model."""
        self._model_config_path = kwargs.pop("model_config_path", DEFAULT_MODEL_CONFIG_PATH)
        super().__init__(**kwargs)

        self._model = keras.Model.from_config(json.load(open(self._model_config_path)))
        self._lock = threading.Lock()
