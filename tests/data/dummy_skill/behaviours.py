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

"""This module contains the behaviours for the 'dummy' skill."""

from aea.skills.base import Behaviour


class DummyBehaviour(Behaviour):
    """Dummy behaviour."""

    def __init__(self, **kwargs):
        """Initialize the echo behaviour."""
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.nb_act_called = 0
        self.nb_teardown_called = 0

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def act(self) -> None:
        """Act according to the behaviour."""
        self.nb_act_called += 1

    def teardown(self) -> None:
        """Teardown the behaviour."""
        self.nb_teardown_called += 1
