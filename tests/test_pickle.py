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
"""This module contains the basic tests for the skill tasks pickling to pass task to the worker processes."""
import logging
import pickle  # nosec
from multiprocessing.pool import Pool
from unittest.mock import Mock

from packages.fetchai.skills.ml_data_provider.strategy import Strategy
from packages.fetchai.skills.ml_train.tasks import MLTrainTask


class TestMlTrainTaskPickle:
    """Test skill task pickling."""

    def setup(self):
        """Setup the test class."""
        context = Mock()
        x = Strategy(name="name", skill_context=Mock()).sample_data(10)
        context.logger = logging.getLogger("some logger")
        self.task = MLTrainTask(context, x)

    def test_skill_pickle_locally(self):
        """Test pickle and unpickle task locally."""
        data = pickle.dumps(self.task)
        task2: MLTrainTask = pickle.loads(data)  # nosec
        assert self.task.train_x.tolist() == task2.train_x.tolist()
        assert self.task.train_y.tolist() == task2.train_y.tolist()

    def test_skill_pickle_crossprocess(self):
        """Test task execute passed to worker process."""
        pool = Pool()
        pool.apply(self.task)
