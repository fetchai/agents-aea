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
"""This module contains the tests of the handler classes of the ml_train skill."""
from typing import Tuple

import numpy as np


def produce_data(batch_size) -> Tuple:
    """Produce the data."""
    from tensorflow import keras  # pylint: disable=import-outside-toplevel

    ((train_x, train_y), _) = keras.datasets.fashion_mnist.load_data()

    idx = np.arange(train_x.shape[0])
    mask = np.zeros_like(idx, dtype=bool)

    selected = np.random.choice(idx, batch_size, replace=False)
    mask[selected] = True

    x_sample = train_x[mask]
    y_sample = train_y[mask]
    return x_sample, y_sample
