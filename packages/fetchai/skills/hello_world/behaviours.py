# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2022 Fetch.AI Limited
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

"""This module contains the behaviour of the 'Hello World!' skill."""

from typing import Any

from aea.skills.behaviours import OneShotBehaviour


DEFAULT_MESSAGE = "Hello World!"


class HelloWorld(OneShotBehaviour):
    """This skill prints 'Hello World!' on the screen."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialise the behaviour."""

        self.message = kwargs.pop("message", DEFAULT_MESSAGE)  # type: str
        super().__init__(**kwargs)

    def setup(self) -> None:
        """The setup."""

    def act(self) -> None:
        """The act."""
        self.context.logger.info(self.message)

    def teardown(self) -> None:
        """The teardown."""
